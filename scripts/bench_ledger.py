"""Ledger benchmark: confirmation latency, batching, sustained throughput, settlement-check cost.

    python scripts/bench_ledger.py --adapter purechain --out results/purechain
    python scripts/bench_ledger.py --adapter inmemory  --out results/inmemory_check   # harness check only

Experiments (purechain):
  E1 sequential   N single-record anchors, each awaited -> confirmation latency distribution
  E2 batching     anchorBatch with k records/tx (k in --batch-sizes) -> latency and gas per record
  E3 load         open-loop offered loads (tx/s): pre-signed txs, parallel senders, block watcher
                  (E3b: the same with k records per transaction)
  E4 check        isSettleable() call latency (the pre-settlement verification read)
  E5 multi-acct   E3 on a benchmark instance with 1 vs N authoriser accounts (per-sender limits)
PoA² seals blocks on demand: a transaction is final when included, so finality = inclusion.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from atfa.ledger import EvidenceRecord, InMemoryLedger, PureChainAdapter  # noqa: E402

RUN_ID = f"{int(time.time())}"


def make_record(i: int, rng) -> EvidenceRecord:
    return EvidenceRecord(device_id=f"EQ-{i % 100:04d}", day=i // 100, seq=1000 + i,
                          report_hash=f"{RUN_ID}-{i}-{rng.integers(1 << 62):016x}",
                          claimed_amount=float(rng.uniform(100, 2000)), trust=0.9, anomaly=0.02,
                          exposure=0.0, risk=0.12, decision=["approve", "hold", "reject"][i % 3],
                          policy_version="atfa-v1")


def pct(a, q):
    a = np.asarray(a, float)
    return float(np.percentile(a, q)) if a.size else np.nan


def wait_all(ad, rcs, timeout=180):
    end = time.time() + timeout
    while ad.pending and time.time() < end:
        ad.poll()
        time.sleep(0.02)
    return rcs


def e1_sequential(ad, n, rng):
    lat, gas, size = [], [], []
    for i in range(n):
        rcs = wait_all(ad, ad.submit([make_record(i, rng)]))
        r = rcs[0]
        if r.status == 1:
            lat.append((r.included_at - r.submitted_at) * 1000)
            gas.append(r.gas_used)
            size.append(r.raw_size)
    return dict(experiment="E1 sequential", records_per_tx=1, n_tx=n, ok=len(lat),
                latency_ms_p50=pct(lat, 50), latency_ms_p95=pct(lat, 95), latency_ms_mean=float(np.mean(lat)),
                gas_per_record=float(np.mean(gas)), tx_bytes=float(np.mean(size))), lat


def e2_batch(ad_factory, sizes, reps, rng):
    rows = []
    for k in sizes:
        ad = ad_factory(k)
        lat, gas = [], []
        for rep in range(reps):
            recs = [make_record(10_000 * k + rep * k + j, rng) for j in range(k)]
            rcs = wait_all(ad, ad.submit(recs))
            if all(r.status == 1 for r in rcs):
                lat.append((rcs[0].included_at - rcs[0].submitted_at) * 1000)
                gas.append(rcs[0].gas_used)
        rows.append(dict(experiment="E2 batching", records_per_tx=k, n_tx=reps, ok=len(lat),
                         latency_ms_p50=pct(lat, 50), latency_ms_p95=pct(lat, 95),
                         gas_per_record=float(np.mean(gas)) if gas else np.nan,
                         records_per_s_sequential=k / (np.mean(lat) / 1000) if lat else np.nan))
    return rows


def e3_load(ad, rates, duration, rng, batch=1):
    rows = []
    base = 1_000_000
    for rate in rates:
        stop = threading.Event()
        lock = threading.Lock()

        def poller():
            while not stop.is_set() or ad.pending:
                with lock:
                    ad.poll()
                time.sleep(0.05)

        th = threading.Thread(target=poller, daemon=True)
        th.start()
        receipts, errors, i = [], 0, 0
        t0 = time.time()
        while time.time() - t0 < duration:
            tick = time.time()
            try:
                with lock:
                    receipts += ad.submit([make_record(base + i + j, rng) for j in range(batch)])
            except Exception:
                errors += 1
            i += batch
            time.sleep(max(0.0, batch / rate - (time.time() - tick)))
        send_span = time.time() - t0
        end = time.time() + 120
        while ad.pending and time.time() < end:
            time.sleep(0.1)
        stop.set()
        th.join(timeout=5)
        base += 100_000
        done = [r for r in receipts if r.included_at and r.status == 1]
        lat = [(r.included_at - r.submitted_at) * 1000 for r in done]
        span = (max(r.included_at for r in done) - min(r.submitted_at for r in receipts)) if done else np.nan
        rows.append(dict(experiment="E3 load", records_per_tx=batch, offered_tps=rate,
                         achieved_send_tps=len(receipts) / send_span, n_tx=len(receipts), ok=len(done),
                         failed_or_timeout=len(receipts) - len(done), send_errors=errors,
                         throughput_tps=len(done) / span if done else np.nan,
                         latency_ms_p50=pct(lat, 50), latency_ms_p95=pct(lat, 95), latency_ms_p99=pct(lat, 99)))
        print(rows[-1], flush=True)
    return rows


def e3_load_presigned(deployment, rates, duration, rng, batch=1, senders=8, label="E3 load", accounts=None,
                      observe_timeout=120):
    """Open-loop load: transactions are pre-signed (sequential nonces), sent by `senders` threads,
    each with its own HTTP connection, paced to the offered rate. A separate watcher reads every new
    block once and timestamps the inclusion of our transactions. This measures the chain, not the
    client; the achieved send rate is reported so any client-side shortfall is visible."""
    import queue
    from atfa.ledger import DECISION_CODE, _b32, purechain_connect
    dep = json.loads(Path(deployment).read_text())
    rows = []
    base = 5_000_000 + 1_000_000 * batch
    for rate in rates:
        w3, acct = purechain_connect(dep["rpc"])
        accts = accounts or [acct]   # transactions are spread round-robin over sender accounts
        c = w3.eth.contract(address=dep["address"], abi=dep["abi"])
        nonces = [w3.eth.get_transaction_count(a.address, "pending") for a in accts]
        n = int(rate * duration)
        raws = []
        for i in range(n):
            recs = [make_record(base + i * batch + j, rng) for j in range(batch)]
            if batch == 1:
                r = recs[0]
                fn = c.functions.anchor(bytes.fromhex(r.digest()), _b32(r.device_id), int(r.day),
                                        DECISION_CODE[r.decision])
                gas = 200_000
            else:
                fn = c.functions.anchorBatch([bytes.fromhex(r.digest()) for r in recs],
                                             [DECISION_CODE[r.decision] for r in recs])
                gas = 100_000 + 30_000 * batch
            a = accts[i % len(accts)]
            tx = fn.build_transaction({"from": a.address, "nonce": nonces[i % len(accts)] + i // len(accts),
                                       "gas": gas, "gasPrice": 0,
                                       "chainId": dep["chain_id"]})
            raws.append(a.sign_transaction(tx).raw_transaction)
        base += n * batch + 10_000
        sent_at, errors, lock = {}, [], threading.Lock()
        q = queue.Queue()
        t_start = time.time() + 0.5
        for i in range(n):
            q.put((t_start + i / rate, i))

        def sender():
            ws, _ = purechain_connect(dep["rpc"])
            while True:
                try:
                    due, i = q.get_nowait()
                except queue.Empty:
                    return
                time.sleep(max(0.0, due - time.time()))
                t = time.time()
                try:
                    h = ws.eth.send_raw_transaction(raws[i]).to_0x_hex()
                    with lock:
                        sent_at[h] = t
                except Exception as e:
                    with lock:
                        errors.append(str(e)[:100])

        included, blocks = {}, []
        stop = threading.Event()

        def watcher():
            ww, _ = purechain_connect(dep["rpc"])
            last = ww.eth.block_number
            while not stop.is_set():
                try:
                    head = ww.eth.block_number
                    while last < head:
                        # the RPC may report a head before the block is fetchable; retry next tick
                        blk = ww.eth.get_block(last + 1)
                        now = time.time()
                        hs = [h.to_0x_hex() for h in blk["transactions"]]
                        blocks.append((last + 1, now, len(hs), blk["gasUsed"]))
                        for h in hs:
                            included.setdefault(h, now)
                        last += 1
                except Exception:
                    pass
                time.sleep(0.05)

        wt = threading.Thread(target=watcher, daemon=True)
        wt.start()
        ths = [threading.Thread(target=sender, daemon=True) for _ in range(senders)]
        for th in ths:
            th.start()
        for th in ths:
            th.join()
        send_span = (max(sent_at.values()) - min(sent_at.values())) if len(sent_at) > 1 else np.nan
        end = time.time() + observe_timeout
        while time.time() < end and any(h not in included for h in sent_at):
            time.sleep(0.2)
        stop.set()
        wt.join(timeout=5)
        # direct receipt check for anything the block watcher did not see (late inclusion vs lost)
        missing = [h for h in sent_at if h not in included]
        late_found = 0
        if missing:
            wr, _ = purechain_connect(dep["rpc"])
            for h in missing:
                try:
                    if wr.eth.get_transaction_receipt(h)["status"] == 1:
                        late_found += 1
                except Exception:
                    pass
        ok = [h for h in sent_at if h in included]
        lat = [(included[h] - sent_at[h]) * 1000 for h in ok]
        first = min(sent_at.values()) if sent_at else np.nan
        last_inc = max(included[h] for h in ok) if ok else np.nan
        span = last_inc - first if ok else np.nan
        ours = [b for b in blocks if b[2] > 0]
        rows.append(dict(
            experiment=label, records_per_tx=batch, offered_tps=rate, senders=senders, accounts=len(accts), n_tx=n,
            # ok = included (seen by the block watcher, with latency) + included per direct receipt check
            sent=len(sent_at), ok=len(ok) + late_found, failed_or_timeout=len(sent_at) - len(ok) - late_found,
            send_errors=len(errors),
            achieved_send_tps=len(sent_at) / send_span if send_span else np.nan,
            throughput_tps=len(ok) / span if ok else np.nan,
            throughput_records_per_s=batch * len(ok) / span if ok else np.nan,
            latency_ms_p50=pct(lat, 50), latency_ms_p95=pct(lat, 95), latency_ms_p99=pct(lat, 99),
            blocks_used=len(ours), mean_tx_per_block=float(np.mean([b[2] for b in ours])) if ours else np.nan,
            not_seen_in_window=len(missing), found_by_receipt_check=late_found,
            observe_timeout_s=observe_timeout,
            first_error=errors[0] if errors else ""))
        print(rows[-1], flush=True)
    return rows


def e4_check(ad, n, rng):
    rec = make_record(0, rng)
    lat = []
    for _ in range(n):
        t = time.perf_counter()
        ad.is_settleable(rec)
        lat.append((time.perf_counter() - t) * 1000)
    return dict(experiment="E4 settlement check (eth_call)", n_tx=n, latency_ms_p50=pct(lat, 50),
                latency_ms_p95=pct(lat, 95))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", choices=["inmemory", "purechain"], default="purechain")
    ap.add_argument("--deployment", default="deployments/purechain.json")
    ap.add_argument("--seq", type=int, default=100)
    ap.add_argument("--batch-sizes", default="1,10,50,100")
    ap.add_argument("--batch-reps", type=int, default=10)
    ap.add_argument("--rates", default="5,10,20,50")
    ap.add_argument("--duration", type=float, default=20)
    ap.add_argument("--checks", type=int, default=100)
    ap.add_argument("--senders", type=int, default=8)
    ap.add_argument("--load-batch", type=int, default=100)
    ap.add_argument("--load-batch-rates", default="1,2,5")
    ap.add_argument("--only", default="", help="comma list of E1,E2,E3,E4,E5 (default: E1-E4)")
    ap.add_argument("--bench-deployment", default="deployments/purechain_bench.json")
    ap.add_argument("--multi-rates", default="20,50,100")
    ap.add_argument("--observe-timeout", type=float, default=120)
    ap.add_argument("--out", default="results/purechain")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    rates = [float(r) for r in args.rates.split(",")]

    if args.adapter == "inmemory":
        rows = e3_load(InMemoryLedger(block_time=1.0, confirmations=1), rates, args.duration, rng)
        pd.DataFrame(rows).to_csv(out / "ledger_bench.csv", index=False)
        return

    factory = lambda k=1: PureChainAdapter(deployment=args.deployment, batch_size=k)
    ad = factory()
    head0 = ad.w3.eth.block_number
    rows = []
    only = set(args.only.split(",")) if args.only else {"E1", "E2", "E3", "E4"}
    if "E1" in only:
        r1, lat1 = e1_sequential(ad, args.seq, rng)
        rows.append(r1)
        print(r1, flush=True)
        pd.DataFrame({"latency_ms": lat1}).to_csv(out / "e1_latencies.csv", index=False)
    if "E2" in only:
        for r in e2_batch(factory, [int(k) for k in args.batch_sizes.split(",")], args.batch_reps, rng):
            rows.append(r)
            print(r, flush=True)
    if "E3" in only:
        rows += e3_load_presigned(args.deployment, rates, args.duration, rng, senders=args.senders)
        if args.load_batch > 1:
            rows += e3_load_presigned(args.deployment, [float(r) for r in args.load_batch_rates.split(",")],
                                      args.duration, rng, batch=args.load_batch, senders=args.senders,
                                      label=f"E3b batched load (k={args.load_batch})")
    if "E5" in only:
        import os
        from dotenv import load_dotenv
        from eth_account import Account
        load_dotenv(".env")
        bdep = json.loads(Path(args.bench_deployment).read_text())
        keys = [os.environ["ATFA_PRIVATE_KEY"]] + [os.environ[f"ATFA_BENCH_KEY_{i}"]
                                                   for i in range(1, len(bdep["authorisers"]))]
        accts = [Account.from_key(k) for k in keys]
        mrates = [float(r) for r in args.multi_rates.split(",")]
        for k in sorted({1, len(accts)}):
            rows += e3_load_presigned(args.bench_deployment, mrates, args.duration, rng, senders=args.senders,
                                      label=f"E5 multi-account ({k} sender{'s' if k > 1 else ''})", accounts=accts[:k],
                                      observe_timeout=args.observe_timeout)
    if "E4" in only:
        rows.append(e4_check(ad, args.checks, rng))
        print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    tag = "" if only == {"E1", "E2", "E3", "E4"} else "_" + "_".join(sorted(only))
    df.to_csv(out / f"ledger_bench{tag}.csv", index=False)
    meta = dict(rpc=ad.w3.provider.endpoint_uri, chain_id=ad.w3.eth.chain_id,
                contract=json.loads(Path(args.deployment).read_text())["address"],
                blocks=[head0, ad.w3.eth.block_number], run_id=RUN_ID,
                client=ad.w3.client_version, finished=time.strftime("%Y-%m-%d %H:%M:%S"))
    (out / f"ledger_bench{tag}_meta.json").write_text(json.dumps(meta, indent=2))
    print(df.round(2).to_string())


if __name__ == "__main__":
    main()
