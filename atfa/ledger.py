"""Ledger layer: anchoring authorisation decisions and their evidence before settlement.

ATFA records, for each settled or held claim, a compact evidence record (hash of the device
report, T, s, F, R, decision, thresholds version). Only Approve decisions are released for
settlement; Hold/Reject are anchored for auditability.

`PureChainAdapter` anchors digests in contracts/ATFAEvidenceAnchor.sol on PureChain PoA²
(deployed with scripts/purechain_deploy.py). `InMemoryLedger` is a hash-chained reference used
for functional tests; its timings are NOT blockchain measurements. Paper figures come from
scripts/bench_ledger.py --adapter purechain.
"""
from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path

PURECHAIN_RPC = "https://purechainnode.com"
PURECHAIN_CHAIN_ID = 900_520_900_520
DECISION_CODE = {"approve": 0, "hold": 1, "reject": 2}


@dataclass
class EvidenceRecord:
    device_id: str
    day: int
    seq: int
    report_hash: str          # sha256 of the canonical device message
    claimed_amount: float
    trust: float
    anomaly: float
    exposure: float
    risk: float
    decision: str             # approve | hold | reject
    policy_version: str

    def digest(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()


@dataclass
class Receipt:
    tx_id: str
    submitted_at: float
    included_at: float | None = None
    finalized_at: float | None = None
    block: int | None = None
    tx_hash: str | None = None
    raw_size: int | None = None
    gas_used: float | None = None   # per record (batch gas divided by batch size)
    status: int | None = None


def report_hash(message: dict) -> str:
    return hashlib.sha256(json.dumps(message, sort_keys=True, default=str).encode()).hexdigest()


class LedgerAdapter(ABC):
    @abstractmethod
    def submit(self, records: list[EvidenceRecord]) -> list[Receipt]:
        """Submit evidence records; return one receipt per record (submission time set)."""

    @abstractmethod
    def poll(self, receipts: list[Receipt]) -> list[Receipt]:
        """Update inclusion / finality times of receipts."""

    def verify(self, record: EvidenceRecord, receipt: Receipt) -> bool:
        """Check that the anchored digest matches the record (pre-settlement evidence check)."""
        raise NotImplementedError


@dataclass
class _Block:
    height: int
    prev: str
    txs: list[str] = field(default_factory=list)
    sealed_at: float = 0.0

    def hash(self) -> str:
        return hashlib.sha256((self.prev + "".join(self.txs) + str(self.height)).encode()).hexdigest()


class InMemoryLedger(LedgerAdapter):
    """Hash-chained blocks sealed every `block_time` seconds; finality after `confirmations` blocks."""

    def __init__(self, block_time: float = 0.0, confirmations: int = 1, max_block_txs: int = 10_000):
        self.block_time, self.conf, self.max_txs = block_time, confirmations, max_block_txs
        self.chain = [_Block(0, "0" * 64, sealed_at=time.time())]
        self.pending: list[str] = []
        self.index: dict[str, tuple[int, str]] = {}
        self._last_seal = time.time()

    def _new_block(self, sealed_at):
        b = _Block(len(self.chain), self.chain[-1].hash(), self.pending[: self.max_txs], sealed_at)
        self.pending = self.pending[self.max_txs:]
        for tx in b.txs:
            self.index[tx] = (b.height, tx)
        self.chain.append(b)

    def _seal(self, force=False):
        if self.block_time == 0:              # instant sealing (functional tests)
            while self.pending:
                self._new_block(time.time())
            return
        now = time.time()                     # PoA-style: a block every block_time, empty or not
        while now - self._last_seal >= self.block_time:
            self._last_seal += self.block_time
            self._new_block(self._last_seal)

    def submit(self, records):
        now = time.time()
        out = []
        for r in records:
            d = r.digest()
            self.pending.append(d)
            out.append(Receipt(tx_id=d, submitted_at=now))
        self._seal(force=self.block_time == 0)
        return out

    def poll(self, receipts):
        self._seal()
        head = len(self.chain) - 1
        for rc in receipts:
            if rc.tx_id in self.index:
                h, _ = self.index[rc.tx_id]
                rc.block = h
                rc.included_at = rc.included_at or self.chain[h].sealed_at
                if head - h + 1 >= self.conf and rc.finalized_at is None:
                    rc.finalized_at = self.chain[min(head, h + self.conf - 1)].sealed_at
        return receipts

    def verify(self, record, receipt):
        return receipt.tx_id == record.digest() and receipt.tx_id in self.index

    def chain_valid(self) -> bool:
        return all(self.chain[i].prev == self.chain[i - 1].hash() for i in range(1, len(self.chain)))


class PureChainAdapter(LedgerAdapter):
    """Anchors evidence digests in the ATFAEvidenceAnchor contract on PureChain PoA².

    Conventions (validated on this network): gasPrice = 0 (zero-fee chain) with an explicit gas
    limit, locally tracked nonces, chainId 900520900520. PoA² seals blocks on demand, so a
    transaction is final once it is included in an authority-sealed block (finalized_at =
    included_at); inclusion is observed by polling receipts, so `poll` should be called often.
    """

    GAS_SINGLE = 200_000
    GAS_PER_BATCH_ITEM = 30_000

    def __init__(self, endpoint: str = PURECHAIN_RPC, deployment: str = "deployments/purechain.json",
                 env_path: str = ".env", batch_size: int = 1, timeout: int = 60):
        w3, acct = purechain_connect(endpoint, env_path, timeout)
        dep = json.loads(Path(deployment).read_text())
        self.w3, self.acct, self.batch = w3, acct, max(1, batch_size)
        self.contract = w3.eth.contract(address=dep["address"], abi=dep["abi"])
        self.chain_id = int(dep["chain_id"])
        self.nonce = w3.eth.get_transaction_count(acct.address, "pending")
        self.pending: dict[str, list[Receipt]] = {}

    def _send(self, fn, gas):
        tx = fn.build_transaction({"from": self.acct.address, "nonce": self.nonce, "gas": gas,
                                   "gasPrice": 0, "chainId": self.chain_id})
        raw = self.acct.sign_transaction(tx).raw_transaction
        self.nonce += 1
        return self.w3.eth.send_raw_transaction(raw).to_0x_hex(), len(raw)

    def submit(self, records):
        out = []
        for i in range(0, len(records), self.batch):
            chunk = records[i:i + self.batch]
            now = time.time()
            if len(chunk) == 1:
                r = chunk[0]
                fn = self.contract.functions.anchor(bytes.fromhex(r.digest()), _b32(r.device_id), int(r.day),
                                                   DECISION_CODE[r.decision])
                txh, size = self._send(fn, self.GAS_SINGLE)
            else:
                fn = self.contract.functions.anchorBatch([bytes.fromhex(r.digest()) for r in chunk],
                                                        [DECISION_CODE[r.decision] for r in chunk])
                txh, size = self._send(fn, 100_000 + self.GAS_PER_BATCH_ITEM * len(chunk))
            rcs = [Receipt(tx_id=r.digest(), submitted_at=now, tx_hash=txh, raw_size=size) for r in chunk]
            self.pending[txh] = rcs
            out += rcs
        return out

    def poll(self, receipts=None):
        from web3.exceptions import TransactionNotFound
        for txh in list(self.pending):
            try:
                rec = self.w3.eth.get_transaction_receipt(txh)
            except TransactionNotFound:
                continue
            now = time.time()
            for rc in self.pending.pop(txh):
                rc.included_at = rc.finalized_at = now
                rc.block, rc.gas_used, rc.status = rec["blockNumber"], rec["gasUsed"] / max(1, self.batch), rec["status"]
        return receipts

    def verify(self, record, receipt=None):
        anchored_at, decision = self.contract.functions.anchors(bytes.fromhex(record.digest())).call()
        return anchored_at != 0 and decision == DECISION_CODE[record.decision]

    def is_settleable(self, record) -> bool:
        return self.contract.functions.isSettleable(bytes.fromhex(record.digest())).call()


# ---------------------------------------------------------------- PureChain helpers
def _b32(text: str) -> bytes:
    return hashlib.sha256(text.encode()).digest()


def purechain_connect(endpoint: str = PURECHAIN_RPC, env_path: str = ".env", timeout: int = 60):
    """Web3 connection (OS trust store, as required on this host) and the ATFA engine account."""
    import os

    import truststore
    from dotenv import load_dotenv
    from eth_account import Account
    from web3 import Web3

    from web3.middleware import ExtraDataToPOAMiddleware

    truststore.inject_into_ssl()
    w3 = Web3(Web3.HTTPProvider(endpoint, request_kwargs={"timeout": timeout}))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)   # PoA headers carry 97-byte extraData
    load_dotenv(env_path)
    key = os.environ.get("ATFA_PRIVATE_KEY", "").strip()
    acct = Account.from_key(key) if key else None
    return w3, acct
