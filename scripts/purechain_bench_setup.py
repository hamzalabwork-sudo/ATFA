"""Benchmark-only contract instance with several authoriser accounts (multi-sender scaling test).

    python scripts/purechain_bench_setup.py --accounts 4

The production deployment (deployments/purechain.json) is governed by the admin wallet, so extra
authorisers cannot be added from here. This deploys a separate ATFAEvidenceAnchor instance whose
admin is the ATFA engine key, creates extra benchmark keys in .env (ATFA_BENCH_KEY_i; never printed)
and authorises them. Writes deployments/purechain_bench.json.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from atfa.ledger import PURECHAIN_CHAIN_ID, PURECHAIN_RPC, purechain_connect  # noqa: E402
from purechain_deploy import compile_contract  # noqa: E402


def bench_keys(n: int):
    from dotenv import load_dotenv
    from eth_account import Account
    env = ROOT / ".env"
    load_dotenv(env)
    accts = []
    for i in range(1, n):
        k = os.environ.get(f"ATFA_BENCH_KEY_{i}")
        if not k:
            a = Account.create()
            with open(env, "a", encoding="utf-8") as f:
                f.write(f"ATFA_BENCH_KEY_{i}={a.key.hex()}\n")
            os.environ[f"ATFA_BENCH_KEY_{i}"] = a.key.hex()
            k = a.key.hex()
        accts.append(Account.from_key(k))
    return accts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--accounts", type=int, default=4)
    ap.add_argument("--out", default="deployments/purechain_bench.json")
    args = ap.parse_args()
    w3, engine = purechain_connect(PURECHAIN_RPC, str(ROOT / ".env"))
    extra = bench_keys(args.accounts)
    abi, bytecode = compile_contract(ROOT / "contracts" / "ATFAEvidenceAnchor.sol")

    def send(fn, gas):
        tx = fn.build_transaction({"from": engine.address, "gas": gas, "gasPrice": 0, "chainId": PURECHAIN_CHAIN_ID,
                                   "nonce": w3.eth.get_transaction_count(engine.address, "pending")})
        rec = w3.eth.wait_for_transaction_receipt(
            w3.eth.send_raw_transaction(engine.sign_transaction(tx).raw_transaction), timeout=180)
        assert rec["status"] == 1
        return rec

    rec = send(w3.eth.contract(abi=abi, bytecode=bytecode).constructor(engine.address), 3_000_000)
    c = w3.eth.contract(address=rec["contractAddress"], abi=abi)
    for a in extra:
        send(c.functions.setAuthoriser(a.address, True), 100_000)
    assert all(c.functions.authorisers(a.address).call() for a in [engine] + extra)
    dep = dict(network="PureChain PoA² (benchmark instance)", rpc=PURECHAIN_RPC, chain_id=PURECHAIN_CHAIN_ID,
               address=rec["contractAddress"], admin=engine.address,
               authorisers=[engine.address] + [a.address for a in extra],
               block=rec["blockNumber"], created=time.strftime("%Y-%m-%d %H:%M:%S"), abi=abi)
    (ROOT / args.out).write_text(json.dumps(dep, indent=2))
    print(f"benchmark instance {dep['address']} with {len(dep['authorisers'])} authorisers")


if __name__ == "__main__":
    main()
