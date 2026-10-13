"""Deploy ATFAEvidenceAnchor to PureChain PoA² and run an on-chain functional check.

    python scripts/purechain_deploy.py --admin 0x6aDb63B9dBaa1e6df2bA2D16bA6273aE916D429A

- Creates the ATFA engine key in .env (ATFA_PRIVATE_KEY) if absent. The key is never printed;
  .env is git-ignored. PureChain is zero-fee, so the account needs no balance.
- The admin wallet governs the authoriser list; the engine key is the initial authoriser.
- Writes deployments/purechain.json (address, ABI, deployment receipt data).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from atfa.ledger import (PURECHAIN_CHAIN_ID, PURECHAIN_RPC, EvidenceRecord, PureChainAdapter,  # noqa: E402
                         purechain_connect)

SOLC_VERSION = "0.8.24"


def ensure_key(env_path: Path):
    from eth_account import Account
    text = env_path.read_text() if env_path.exists() else ""
    if "ATFA_PRIVATE_KEY=" in text:
        return False
    acct = Account.create()
    with open(env_path, "a", encoding="utf-8") as f:
        f.write(f"ATFA_PRIVATE_KEY={acct.key.hex()}\n")
    return True


def compile_contract(path: Path):
    import solcx
    if SOLC_VERSION not in [str(v) for v in solcx.get_installed_solc_versions()]:
        solcx.install_solc(SOLC_VERSION)
    out = solcx.compile_source(path.read_text(encoding="utf-8"), output_values=["abi", "bin"],
                               optimize=True, optimize_runs=200, solc_version=SOLC_VERSION)
    (_, data), = [(k, v) for k, v in out.items() if k.endswith(":ATFAEvidenceAnchor")]
    return data["abi"], data["bin"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--admin", required=True)
    ap.add_argument("--rpc", default=PURECHAIN_RPC)
    ap.add_argument("--out", default="deployments/purechain.json")
    args = ap.parse_args()

    created = ensure_key(ROOT / ".env")
    w3, acct = purechain_connect(args.rpc, str(ROOT / ".env"))
    assert w3.eth.chain_id == PURECHAIN_CHAIN_ID, w3.eth.chain_id
    print(f"engine account {acct.address} ({'new key created in .env' if created else 'existing key'})")

    import truststore
    truststore.inject_into_ssl()
    abi, bytecode = compile_contract(ROOT / "contracts" / "ATFAEvidenceAnchor.sol")
    from web3 import Web3
    admin = Web3.to_checksum_address(args.admin)
    factory = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = factory.constructor(admin).build_transaction({
        "from": acct.address, "nonce": w3.eth.get_transaction_count(acct.address, "pending"),
        "gas": 3_000_000, "gasPrice": 0, "chainId": PURECHAIN_CHAIN_ID})
    t0 = time.perf_counter()
    txh = w3.eth.send_raw_transaction(acct.sign_transaction(tx).raw_transaction)
    rec = w3.eth.wait_for_transaction_receipt(txh, timeout=180)
    lat = (time.perf_counter() - t0) * 1000
    assert rec["status"] == 1, "deployment reverted"
    dep = dict(network="PureChain PoA²", rpc=args.rpc, chain_id=PURECHAIN_CHAIN_ID,
               address=rec["contractAddress"], admin=admin, engine=acct.address,
               tx_hash=rec["transactionHash"].to_0x_hex(), block=rec["blockNumber"], gas_used=rec["gasUsed"],
               deploy_latency_ms=round(lat, 1), solc=SOLC_VERSION,
               deployed_at=datetime.now(timezone.utc).isoformat(), abi=abi)
    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dep, indent=2))
    print(f"deployed at {dep['address']} block {dep['block']} gas {dep['gas_used']} ({lat:.0f} ms)")

    # ---- functional check on-chain
    ad = PureChainAdapter(args.rpc, str(out), str(ROOT / ".env"))
    rec_ok = EvidenceRecord("EQ-0001", 600, 1600, "ab" * 32, 760.0, 0.93, 0.02, 0.0, 0.09, "approve", "atfa-v1")
    rec_hold = EvidenceRecord("EQ-0002", 600, 1600, "cd" * 32, 1900.0, 0.55, 0.71, 0.4, 0.88, "hold", "atfa-v1")
    rcs = ad.submit([rec_ok, rec_hold])
    deadline = time.time() + 120
    while ad.pending and time.time() < deadline:
        ad.poll()
        time.sleep(0.2)
    tampered = EvidenceRecord(**{**rec_ok.__dict__, "claimed_amount": 9999.0})
    checks = {
        "both anchored (status 1)": all(r.status == 1 for r in rcs),
        "approve record verifies": ad.verify(rec_ok),
        "approve record settleable": ad.is_settleable(rec_ok),
        "held record NOT settleable": not ad.is_settleable(rec_hold),
        "tampered record NOT settleable": not ad.is_settleable(tampered),
    }
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    dep["functional_check"] = checks
    out.write_text(json.dumps(dep, indent=2))


if __name__ == "__main__":
    main()
