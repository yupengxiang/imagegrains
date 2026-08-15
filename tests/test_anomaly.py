import numpy as np
import pandas as pd

from aggregate_screening import anomaly as an


def _df_with(d_sieve, solidity=None):
    n = len(d_sieve)
    df = pd.DataFrame(
        {
            "b_mm": d_sieve,
            "area_px": np.full(n, 1000.0),
            "solidity": solidity if solidity is not None else np.full(n, 0.95),
        }
    )
    return df


def test_size_anomaly_mask():
    over, under = an.size_anomaly_mask(np.array([3.0, 10.0, 60.0]))
    assert list(over) == [False, False, True]
    assert list(under) == [True, False, False]


def test_classify_oversized_and_undersized():
    df = _df_with(np.array([3.0, 10.0, 60.0]))
    out = an.classify_anomalies(df, df["b_mm"].to_numpy())
    assert list(out["anomaly_class"]) == ["undersized", "normal", "oversized"]


def test_suspect_mud_rule():
    # 45mm 且凸度很低 -> 疑似泥团（开启兜底规则时）
    df = _df_with(np.array([45.0]), solidity=np.array([0.7]))
    out = an.classify_anomalies(df, df["b_mm"].to_numpy())
    assert out["anomaly_class"][0] == "suspect_mud"


def test_suspect_mud_disabled_when_solidity_high():
    df = _df_with(np.array([45.0]), solidity=np.array([0.95]))
    out = an.classify_anomalies(df, df["b_mm"].to_numpy())
    assert out["anomaly_class"][0] == "normal"


def test_anomaly_summary():
    df = _df_with(np.array([3.0, 10.0, 60.0]))
    out = an.classify_anomalies(df, df["b_mm"].to_numpy())
    summ = an.anomaly_summary(out)
    assert summ["oversized"]["count"] == 1
    assert summ["undersized"]["count"] == 1
    assert summ["normal"]["count"] == 1
