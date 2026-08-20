"""异常检测：大块异物、过小噪声、疑似泥团。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ._columns import AREA_CONVEX_PX, AREA_PX

# 正常骨料区间与异物阈值（mm）
NORMAL_MIN: float = 5.0
NORMAL_MAX: float = 40.0
FOREIGN_MIN: float = 50.0  # >50 视为大块异物
MUD_BAND: tuple[float, float] = (40.0, 50.0)

# 兼容旧常量名
SIZE_LOWER_MM = NORMAL_MIN
SIZE_UPPER_MM = NORMAL_MAX
OVERSIZE_MM = FOREIGN_MIN

LABELS: dict[str, str] = {
    "normal": "正常骨料",
    "oversized": "大块异物(>50mm)",
    "undersized": "过小噪声(<5mm)",
    "suspect_mud": "疑似泥团/非骨料",
}


def size_anomaly_mask(
    d_sieve_mm, upper: float = FOREIGN_MIN, lower: float = NORMAL_MIN
) -> tuple[np.ndarray, np.ndarray]:
    """按筛分等效粒径返回 (oversized_mask, undersized_mask)。"""
    d = np.asarray(d_sieve_mm, dtype=float)
    return d > upper, d < lower


def _get_solidity(df: pd.DataFrame) -> np.ndarray | None:
    if "solidity" in df.columns:
        return df["solidity"].to_numpy(dtype=float)
    if "convexity" in df.columns:
        return df["convexity"].to_numpy(dtype=float)
    if AREA_PX in df.columns and AREA_CONVEX_PX in df.columns:
        a = df[AREA_PX].to_numpy(dtype=float)
        ac = df[AREA_CONVEX_PX].to_numpy(dtype=float)
        return np.minimum(a, ac) / np.maximum(ac, 1e-12)
    return None


_UNSET = object()


def classify_anomalies(
    df: pd.DataFrame,
    d_sieve_mm,
    thresholds: dict | None = None,
    *,
    mud_solidity: float | None | object = _UNSET,
    mud_band: tuple[float, float] | None | object = _UNSET,
) -> pd.DataFrame:
    """给 DataFrame 加 ``anomaly_class / anomaly_label`` 列。

    判定顺序：oversized > suspect_mud > undersized > normal。
    ``mud_solidity=None`` 时关闭泥团兜底规则（避免误报）。
    """
    # 兼容旧 thresholds 字典
    if thresholds is not None:
        if mud_solidity is _UNSET:
            mud_solidity = thresholds.get("mud_solidity", 0.85)
        if mud_band is _UNSET:
            lo = thresholds.get("mud_size_lo", MUD_BAND[0])
            hi = thresholds.get("mud_size_hi", MUD_BAND[1])
            mud_band = (float(lo), float(hi))
    if mud_band is _UNSET:
        mud_band = MUD_BAND
    if mud_solidity is _UNSET:
        mud_solidity = 0.85

    d = np.asarray(d_sieve_mm, dtype=float)
    if len(d) != len(df):
        raise ValueError(f"d_sieve 长度 {len(d)} 与 DataFrame 行数 {len(df)} 不一致")

    over, under = size_anomaly_mask(d, upper=FOREIGN_MIN, lower=NORMAL_MIN)

    keys = np.full(len(df), "normal", dtype=object)
    keys[over] = "oversized"
    keys[under] = "undersized"

    if mud_solidity is not None:
        sol = _get_solidity(df)
        if sol is not None:
            mud = (d > mud_band[0]) & (d <= mud_band[1]) & (sol < mud_solidity)
            # mud 与 over 不重叠（over 是 >50，mud 是 ≤50），无需 ~over
            keys[mud] = "suspect_mud"

    out = df.copy()
    out["anomaly_class"] = keys
    out["anomaly_label"] = [LABELS[k] for k in keys]
    return out


def anomaly_summary(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """各异常类别的颗粒数与占比，需先 ``classify_anomalies``。"""
    if "anomaly_class" not in df.columns:
        raise ValueError("请先调用 classify_anomalies 添加 anomaly_class 列")
    counts = df["anomaly_class"].value_counts()
    total = len(df)
    return {
        key: {"count": int(counts.get(key, 0)), "fraction": 100.0 * int(counts.get(key, 0)) / total if total else 0.0}
        for key in LABELS
    }
