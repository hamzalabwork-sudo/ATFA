"""One experimental world: generate -> features -> detectors -> calibration -> financial systems."""
from __future__ import annotations

import copy
import time

import numpy as np

from .authorisation import SimData, SystemSpec, calibrate, simulate, theta_grid
from .detectors import REGISTRY, FitContext, HybridStacker, Platt, Split, timed_score
from .features import build_features, expected_usage, hard_violations, observable_view, to_tensor
from .generator import ATTACK_FAMILIES, KNOWLEDGE_LEVELS, generate_world
from .metrics import best_f1_threshold, detection_metrics, episode_latency, trust_metrics
from .windows import WindowStore, index_grid


def build_systems(cfg) -> list[SystemSpec]:
    """Baselines, the ATFA design (configs: atfa_design), comparisons and ablations.

    Every ATFA variant is the ATFA design with exactly one change.
    """
    p = cfg["detectors"]["primary"]
    d = dict(cfg.get("atfa_design", {}))
    base = dict(detector=p, risk=d.get("risk", "noisy_or"), use_F=d.get("use_F", True),
                audit=d.get("audit", False), exposure=d.get("exposure", "baseline"))

    def atfa(name, group, **change):
        return SystemSpec(name, group=group, **{**base, **change})

    S = [
        SystemSpec("B0 approve all (smart contract only)", kind="approve_all", group="baseline"),
        SystemSpec("B1 hard rules only", kind="hard_only", group="baseline"),
        SystemSpec("B2 fixed amount threshold", kind="amount", group="baseline"),
        SystemSpec("B3 detector only", detector=p, trust="none", risk="detector", use_F=False, gate=False,
                   group="baseline"),
        SystemSpec("B4 trust only", detector=p, trust="atfa", risk="trust", use_F=False, group="baseline"),
        SystemSpec("Oracle", kind="oracle", group="baseline"),
        atfa("ATFA", "atfa"),
        atfa("ATFA (provisional thresholds)", "atfa", thresholds="provisional"),
    ]
    for t in ("none", "static", "ewma", "beta"):
        S.append(atfa(f"ATFA trust={t}", "trust", trust=t))
    for det in cfg["detectors"]["enabled"]:
        if det != p:
            S.append(atfa(f"ATFA detector={det}", "detector", detector=det))
    S += [
        atfa("ATFA -detector (s=0)", "ablation", detector=None),
        atfa("ATFA -exposure-weighted trust", "ablation", trust_opts={"exposure": False}),
        atfa("ATFA -verification feedback", "ablation", trust_opts={"feedback": False}),
        atfa("ATFA -asymmetric evidence", "ablation", trust_opts={"asymmetric": False}),
        atfa("ATFA -low-trust gate", "ablation", gate=False),
        atfa("ATFA -hard rules", "ablation", hard=False, trust_opts={"hard": False}),
        atfa("ATFA weighted-sum risk", "ablation", risk="weighted", use_F=True),
        atfa("ATFA +exposure term F (noisy-OR)", "ablation", risk="noisy_or", use_F=True),
        atfa("ATFA expected-loss risk (lambda=0.7)", "ablation", risk="expected_loss", use_F=True),
        atfa("ATFA +random audits", "ablation", audit=True),
        atfa("ATFA v1 authorisation (noisy-OR+F, rolling exposure)", "ablation", risk="noisy_or", use_F=True,
             exposure="rolling"),
    ]
    return S


def world_config(cfg, scen, level):
    from .config import deep_merge
    g = deep_merge(cfg["generator"], scen.get("generator_overrides", {}))   # robustness scenarios
    g["compromise_fraction"] = level
    if scen.get("holdout_family") or scen.get("alpha_multiplier") is not None:
        g["attacks"]["shift"] = dict(start_day=cfg["splits"]["val_end"],
                                     holdout_family=scen.get("holdout_family"),
                                     alpha_multiplier=scen.get("alpha_multiplier"))
    return g


def run_world(cfg: dict, scen_name: str, scen: dict, level: float, seed: int, log=print) -> dict:
    t_start = time.time()
    g = world_config(cfg, scen, level)
    sp, W = cfg["splits"], cfg["windows"]["length"]
    A, D = g["n_assets"], g["n_days"]
    te, vs, ve = sp["train_end"], sp["val_split"], sp["val_end"]
    key = dict(scenario=scen_name, level=level, seed=seed)

    records, assets = generate_world(g, seed)
    records = records.sort_values(["asset_id", "day"]).reset_index(drop=True)
    obs = observable_view(records)
    X = to_tensor(build_features(obs, assets, g["commissioning_days"]), A, D)
    baseline_grid = expected_usage(obs, g["commissioning_days"]).baseline.to_numpy().reshape(A, D)
    hard = hard_violations(obs, g["contract"]).to_numpy().reshape(A, D)
    grid = lambda c: records[c].to_numpy().reshape(A, D)
    y, fraud, fam = grid("anomaly_label"), grid("fraud_label"), grid("attack_family")
    know, benign = grid("knowledge"), grid("benign_event")

    if scen.get("split") == "asset":
        perm = np.random.default_rng(seed + 7).permutation(A)
        n_test = int(round(sp["asset_holdout_fraction"] * A))
        test_assets, train_assets = np.sort(perm[:n_test]), np.sort(perm[n_test:])
    else:
        train_assets = test_assets = np.arange(A)

    mask = np.zeros((A, D), bool)
    mask[np.ix_(train_assets, np.arange(te))] = True
    store = WindowStore.fit(X, W, mask)

    def split(assets_, lo, hi, labels=True):
        a, t = index_grid(assets_, lo, hi)
        return Split(a, t, y[a, t] if labels else None)

    tr, vc, vp = split(train_assets, 0, te), split(train_assets, te, vs), split(train_assets, vs, ve)
    tst = split(test_assets, ve, D)
    normal = split(train_assets, 10, g["commissioning_days"], labels=False)
    ctx = FitContext(store, tr, vc, normal, cfg["detectors"], seed)

    # ---- detectors: raw scores on all assets for days [te, D)
    a_all, t_all = index_grid(np.arange(A), te, D)
    Dr = D - te
    raw, prob, det_rows, timing = {}, {}, [], {}
    enabled = cfg["detectors"]["enabled"]
    for name in [n for n in enabled if n not in ("hybrid", "tcn_xgb")]:
        t0 = time.time()
        det = REGISTRY[name]().fit(ctx)
        fit_s = time.time() - t0
        r, ms = timed_score(det, store, a_all, t_all)
        raw[name] = r.reshape(A, Dr)
        timing[name] = dict(fit_s=fit_s, infer_ms_per_window=ms, n_params=det.n_params(),
                            transform=det.transform)
        log(f"  [{scen_name} L={level} s={seed}] {name}: fit {fit_s:.1f}s")
    for name in raw:
        cal = Platt(timing[name]["transform"]).fit(raw[name][vc.a, vc.t - te], vc.y)
        prob[name] = cal(raw[name].ravel()).reshape(A, Dr)
    if "tcn_xgb" in enabled:
        # ensemble of the generalising TCN and the strong in-distribution XGBoost (stacked on val_calib)
        ens = HybridStacker(kinds=("logit", "logit")).fit(raw["tcn"][vc.a, vc.t - te],
                                                          raw["xgboost"][vc.a, vc.t - te], vc.y)
        prob["tcn_xgb"] = ens(raw["tcn"].ravel(), raw["xgboost"].ravel()).reshape(A, Dr)
        timing["tcn_xgb"] = dict(fit_s=timing["tcn"]["fit_s"] + timing["xgboost"]["fit_s"],
                                 infer_ms_per_window=timing["tcn"]["infer_ms_per_window"]
                                 + timing["xgboost"]["infer_ms_per_window"],
                                 n_params=timing["tcn"]["n_params"])
    if "hybrid" in enabled:
        hs = HybridStacker().fit(raw["tcn"][vc.a, vc.t - te], raw["lstm_ae"][vc.a, vc.t - te], vc.y)
        prob["hybrid"] = hs(raw["tcn"].ravel(), raw["lstm_ae"].ravel()).reshape(A, Dr)
        timing["hybrid"] = dict(fit_s=timing["tcn"]["fit_s"] + timing["lstm_ae"]["fit_s"],
                                infer_ms_per_window=timing["tcn"]["infer_ms_per_window"]
                                + timing["lstm_ae"]["infer_ms_per_window"],
                                n_params=timing["tcn"]["n_params"] + timing["lstm_ae"]["n_params"])

    # ---- detection metrics on the test split
    yt = y[tst.a, tst.t]
    ta_grid = test_assets
    for name, p in prob.items():
        thr = best_f1_threshold(vp.y, p[vp.a, vp.t - te])
        pt = p[tst.a, tst.t - te]
        row = dict(key, detector=name, **detection_metrics(yt, pt, thr),
                   **{k: v for k, v in timing[name].items() if k != "transform"})
        ft, kt, bt = fam[tst.a, tst.t], know[tst.a, tst.t], benign[tst.a, tst.t]
        for f in ATTACK_FAMILIES:
            m = ft == f
            row[f"recall[{f}]"] = float((pt[m] >= thr).mean()) if m.any() else np.nan
        for k in KNOWLEDGE_LEVELS:
            m = (kt == k) & (yt == 1)
            row[f"recall[{k}]"] = float((pt[m] >= thr).mean()) if m.any() else np.nan
        for b in ("delay", "dropout", "stuck_sensor", "overtime", "maintenance", "none"):
            m = (bt == b) & (yt == 0)
            row[f"fpr[{b}]"] = float((pt[m] >= thr).mean()) if m.any() else np.nan
        pg = p[ta_grid, ve - te:] >= thr
        row["episode_detect_rate"], row["episode_median_latency_days"], row["n_episodes"] = \
            episode_latency(y[ta_grid, ve:].astype(bool), pg)
        det_rows.append(row)

    # ---- financial systems
    def simdata(assets_, lo, hi):
        sl = (np.asarray(assets_)[:, None], np.arange(lo, hi)[None, :])
        rate = assets.rate.to_numpy()[assets_]
        return SimData(
            hours=grid("reported_hours")[sl], claimed=grid("claimed_amount")[sl], rate=rate,
            nominal=assets.nominal_hours.to_numpy()[assets_], peer_med=peer_med[sl], hard=hard[sl],
            scores={k: v[np.asarray(assets_)[:, None], np.arange(lo - te, hi - te)[None, :]]
                    for k, v in prob.items()},
            ref_hours=grid("reference_hours")[sl], overclaim=grid("overclaim_amount")[sl],
            fraud=fraud[sl], compromised=assets.compromised.to_numpy()[assets_],
            family=fam[sl], baseline=baseline_grid[sl],
        )

    hrs = records.reported_hours.where(records.reported_hours > 0)
    peer_med = (hrs.groupby([records.site, records.day]).transform("median").fillna(0.0)
                .to_numpy().reshape(A, D))
    val = simdata(train_assets, te, ve)
    test = simdata(test_assets, te, D)
    cache = cfg["experiment"].get("cache_dir")
    if cache:   # development only: cache simulation inputs to iterate on authorisation quickly
        import pickle
        from pathlib import Path as _P
        _P(cache).mkdir(parents=True, exist_ok=True)
        with open(_P(cache) / f"{scen_name}__L{level:.2f}__s{seed}.pkl", "wb") as fh:
            pickle.dump(dict(val=val, test=test, v_from=vs - te, t_from=ve - te, key=key), fh)
    v_from, t_from = vs - te, ve - te
    fin_rows, trust_rows, sens_rows = [], [], []
    tl = cfg["trust"]["low"]
    for spec in build_systems(cfg):
        if spec.detector is not None and spec.detector not in prob:
            continue
        theta, cap, feasible = calibrate(spec, val, cfg, v_from, seed=seed)
        m = simulate(spec, test, cfg, theta, cap, seed=seed + 1, eval_from=t_from,
                     trace=spec.kind == "risk")
        tr_ = m.pop("_trace", None)
        fin_rows.append(dict(key, system=spec.name, group=spec.group, theta_approve=theta[0],
                             theta_reject=theta[1], amount_cap=cap, calib_feasible=feasible, **m))
        if tr_ is not None:
            T = tr_["T"][:, t_from:]
            claim = test.hours[:, t_from:] > 0
            trust_rows.append(dict(key, system=spec.name, group=spec.group,
                                   **trust_metrics(T, test.fraud[:, t_from:].astype(bool), claim,
                                                   test.compromised.astype(bool), tl)))
        if spec.name == "ATFA" and seed in cfg["experiment"].get("sensitivity_seeds", []):
            for th in theta_grid(cfg, spec):
                mm = simulate(spec, test, cfg, th, seed=seed + 1, eval_from=t_from)
                sens_rows.append(dict(key, theta_approve=th[0], theta_reject=th[1],
                                      selected=th == tuple(theta),
                                      **{k: v for k, v in mm.items() if not k.startswith("fvs_pct[")}))

    claims = records.reported_hours > 0
    world = dict(key, n_records=len(records), n_claims=int(claims.sum()),
                 anomaly_rate=float(records.anomaly_label.mean()),
                 fraud_claim_rate=float(records.fraud_label[claims].mean()),
                 fraud_value=float(records.overclaim_amount.sum()),
                 claimed_value=float(records.claimed_amount.sum()),
                 hard_violation_rate=float(hard.mean()),
                 n_compromised=int(assets.compromised.sum()), runtime_s=time.time() - t_start)
    log(f"  [{scen_name} L={level} s={seed}] done in {world['runtime_s']:.0f}s")
    return dict(detection=det_rows, financial=fin_rows, trust=trust_rows, sensitivity=sens_rows,
                world=[world])
