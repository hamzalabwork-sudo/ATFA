"""Loader tests on small fixtures in the published TON_IoT / Edge-IIoTset formats."""
import numpy as np
import pandas as pd

from atfa.public import EDGE_LEAKY, load_edge_iiot, load_ton_iot_file


def test_ton_iot_fridge_format(tmp_path):
    p = tmp_path / "Train_Test_IoT_Fridge.csv"
    p.write_text(
        "date,time,fridge_temperature,temp_condition,label,type\n"
        "25-Apr-19, 19:42:23,9.0, high ,1,ddos\n"
        "25-Apr-19, 19:40:23,13.1, low ,0,normal\n"
        "26-Apr-19, 01:02:03,8.5, high ,0,normal\n"
    )
    X, y, typ, feats = load_ton_iot_file(p)
    assert feats == ["fridge_temperature", "temp_condition"]          # no date/time/label/type
    np.testing.assert_allclose(X[:, 0], [13.1, 9.0, 8.5])             # sorted by timestamp
    np.testing.assert_allclose(X[:, 1], [0, 1, 1])
    assert list(y) == [0, 1, 0] and list(typ) == ["normal", "ddos", "normal"]


def test_edge_iiot_drops_leaky_fields_and_duplicates(tmp_path):
    cols = {c: ["x", "x", "y"] for c in EDGE_LEAKY[:4]}
    df = pd.DataFrame({**cols, "tcp.len": [1, 1, 5], "mqtt.protoname": ["MQTT", "MQTT", "0"],
                       "Attack_label": [0, 0, 1], "Attack_type": ["Normal", "Normal", "DDoS_UDP"]})
    p = tmp_path / "edge.csv"
    df.to_csv(p, index=False)
    X, yb, yt, feats, n_dup = load_edge_iiot(p)
    assert not set(feats) & set(EDGE_LEAKY)
    assert n_dup == 1 and len(yb) == 2 and set(feats) == {"tcp.len", "mqtt.protoname"}


def test_blocked_split_disjoint_embargoed_and_stratified():
    from atfa.public import blocked_split
    n = 24 * 3600 // 10                                   # one day, one reading every 10 s
    ts = np.datetime64("2019-04-01T00:00:00") + np.arange(n) * np.timedelta64(10, "s")
    y = np.zeros(n, int)
    y[int(0.75 * n):] = 1                                 # attacks only at the end (as in TON_IoT)
    W = 40
    parts = blocked_split(ts, y, W, block_minutes=60, seed=0)
    allidx = np.concatenate(parts)
    assert len(allidx) == len(np.unique(allidx))          # disjoint
    block = ((ts - ts[0]) / np.timedelta64(1, "m") // 60).astype(int)
    first = np.searchsorted(block, block, side="left")
    assert ((allidx - first[allidx]) >= W).all()          # embargo respected
    assert y[parts[0]].sum() > 0 and y[parts[3]].sum() > 0  # train and test both see attacks
