"""Public benchmark loaders and detection protocol.

TON_IoT (UNSW) IoT telemetry - primary public *temporal* benchmark.
    Expected files (Train_Test_IoT_dataset folder), e.g. Train_Test_IoT_Fridge.csv with columns
    date, time, <sensor columns>, label, type. Each file is one device stream. Rows are ordered
    by timestamp, windowed causally and split chronologically 60/20/20 (train / val / test; val is
    halved into val_calib and val_policy exactly as for ATFA-AssetFinance).
    Note: the Train_Test files are sub-sampled, so consecutive rows are not equally spaced, and
    attacks are concentrated in particular time periods; per-split class counts are reported.
    `type` (attack name) and timestamps are never used as features.

Edge-IIoTset (Ferrag et al., 2022) - optional network-level intrusion benchmark, non-temporal.
    DNN-EdgeIIoT-dataset.csv. Rows are packets/flows, not per-device sequences, so only the
    window-free models (XGBoost, Isolation Forest) are evaluated. Identifier and payload fields
    that leak the label are dropped, and exact duplicates are removed *before* splitting.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

BOOL_MAP = {"true": 1, "false": 0, "on": 1, "off": 0, "open": 1, "closed": 0, "high": 1, "low": 0,
            "yes": 1, "no": 0, "1": 1, "0": 0}
TON_NON_FEATURES = {"date", "time", "ts", "timestamp", "label", "type"}

EDGE_LEAKY = [
    "frame.time", "ip.src_host", "ip.dst_host", "arp.src.proto_ipv4", "arp.dst.proto_ipv4",
    "http.file_data", "http.request.full_uri", "icmp.transmit_timestamp", "http.request.uri.query",
    "tcp.options", "tcp.payload", "tcp.srcport", "tcp.dstport", "udp.port", "mqtt.msg",
]


def _encode(col: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(col):
        return col.astype(float)
    s = col.astype(str).str.strip().str.lower()
    num = pd.to_numeric(s, errors="coerce")
    if num.notna().mean() > 0.95:
        return num.astype(float)
    if set(s.dropna().unique()) <= set(BOOL_MAP):
        return s.map(BOOL_MAP).astype(float)
    return s.astype("category").cat.codes.astype(float)


def load_ton_iot_file(path: str | Path, return_ts: bool = False):
    """Returns (X [N, F] time-ordered, y [N], attack_type [N], feature names[, timestamps])."""
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    df.columns = [c.lstrip("﻿") for c in df.columns]
    lower = {c.lower(): c for c in df.columns}
    ts = None
    if "date" in lower and "time" in lower:
        ts = pd.to_datetime(df[lower["date"]].astype(str).str.strip() + " "
                            + df[lower["time"]].astype(str).str.strip(),
                            format="mixed", dayfirst=True, errors="coerce")
        order = np.argsort(ts.fillna(pd.Timestamp.max).to_numpy(), kind="stable")
        df = df.iloc[order].reset_index(drop=True)
        ts = ts.iloc[order].reset_index(drop=True)
    feats = [c for c in df.columns if c.lower() not in TON_NON_FEATURES]
    X = pd.DataFrame({c: _encode(df[c]) for c in feats}).ffill().fillna(0.0).to_numpy(np.float32)
    y = pd.to_numeric(df[lower["label"]], errors="coerce").fillna(0).astype(int).to_numpy()
    typ = df[lower["type"]].astype(str).str.strip().to_numpy() if "type" in lower else np.array(["?"] * len(df))
    if return_ts:
        return X, y, typ, feats, (ts.to_numpy() if ts is not None else None)
    return X, y, typ, feats


def blocked_split(ts, y, W, block_minutes=60, fracs=(0.6, 0.1, 0.1, 0.2), seed=0):
    """Blocked time-series split. Contiguous blocks of `block_minutes` are assigned whole to
    train / val_calib / val_policy / test; blocks containing attacks and attack-free blocks are
    assigned separately so each split gets its share of both. The first W rows of every block are
    embargoed (dropped from all splits), so no window spans two splits. Returns 4 index arrays."""
    t = (ts - ts[0]) / np.timedelta64(1, "m")
    block = np.floor(t / block_minutes).astype(np.int64)
    ub, inv = np.unique(block, return_inverse=True)
    has_attack = np.bincount(inv, weights=y, minlength=len(ub)) > 0
    rng = np.random.default_rng(seed)
    assign = np.empty(len(ub), int)
    cuts = np.cumsum(fracs)[:-1]
    for grp in (np.flatnonzero(has_attack), np.flatnonzero(~has_attack)):
        perm = rng.permutation(grp)
        edges = np.round(cuts * len(perm)).astype(int)
        for k, part in enumerate(np.split(perm, edges)):
            assign[part] = k
    pos_in_block = np.arange(len(block)) - np.searchsorted(block, block, side="left")
    keep = pos_in_block >= W
    split_of_row = assign[inv]
    return [np.flatnonzero(keep & (split_of_row == k)) for k in range(4)]


def load_edge_iiot(path: str | Path, target: str = "Attack_label"):
    df = pd.read_csv(path, low_memory=False)
    df = df.drop(columns=[c for c in EDGE_LEAKY if c in df.columns])
    n0 = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    y_bin = df["Attack_label"].astype(int).to_numpy()
    y_type = df["Attack_type"].astype(str).to_numpy()
    X = df.drop(columns=["Attack_label", "Attack_type"])
    X = pd.DataFrame({c: _encode(X[c]) for c in X.columns}).fillna(0.0)
    return X.to_numpy(np.float32), y_bin, y_type, list(X.columns), n0 - len(df)
