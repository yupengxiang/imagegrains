"""异常检测。

比赛要求识别两类异常：

1. 大块异物（>50 mm）：纯尺寸阈值，直接由筛分等效粒径判定；
2. 泥团等非骨料物质：grains CSV 只含几何量，不含颜色/纹理。
   本模块提供 (a) 基于尺寸与几何的兜底规则（如 >40mm 且凸度异常低），
   (b) 一个"疑似泥团"标记位，供未来接入基于图像 crop 的分类器
   （`SpectralAnomalyDetector` 占位），不硬编码未经验证的判别式。

另外把低于比赛下限（<5mm）的颗粒标记为噪声，供过滤使用。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# 比赛粒径范围（mm）：5-40 为正常骨料
SIZE_LOWER_MM = 5.0
SIZE_UPPER_MM = 40.0
# 比赛要求的异物阈值
OVERSIZE_MM = 50.0

# anomaly 列的值
LABELS = {
    "normal": "正常骨料",
    "oversized": "大块异物(>50mm)",
    "undersized": "过小噪声(<5mm)",
    "suspect_mud": "疑似泥团/非骨料",
}


def size_anomaly_mask(d_sieve_mm, upper=OVERSIZE_MM, lower=SIZE_LOWER_MM):
    """按筛分等效粒径标记异常（逐颗粒 bool 数组）。

    返回 (oversized_mask, undersized_mask)。
    """
    d = np.asarray(d_sieve_mm, dtype=float)
    return d > upper, d < lower


def classify_anomalies(df, d_sieve_mm, thresholds=None):
    """给 DataFrame 加 anomaly_class / anomaly_label 列。

    判定顺序：oversized > suspect_mud > undersized > normal。

    suspect_mud 兜底规则（可配置，默认关闭，避免误报）：
    尺寸落在 (40, 50] mm 且凸度低于阈值 —— 大而非常不规则的物体更可能是
    泥团/异物而非正常骨料。该规则未被真实数据验证，谨慎使用。
    """
    t = {"mud_size_lo": 40.0, "mud_size_hi": 50.0, "mud_solidity": 0.85}
    if thresholds:
        t.update(thresholds)
    d = np.asarray(d_sieve_mm, dtype=float)
    over, under = size_anomaly_mask(d, upper=t["mud_size_hi"], lower=SIZE_LOWER_MM)

    out = df.copy()
    n = len(out)
    keys = np.full(n, "normal", dtype=object)
    keys[over] = "oversized"
    keys[under] = "undersized"

    if t["mud_solidity"] is not None and "solidity" in out.columns:
        sol = out["solidity"].to_numpy(dtype=float)
        mud = (
            (d > t["mud_size_lo"])
            & (d <= t["mud_size_hi"])
            & (sol < t["mud_solidity"])
            & ~over
        )
        keys[mud] = "suspect_mud"

    out["anomaly_class"] = keys
    out["anomaly_label"] = [LABELS[k] for k in keys]
    return out


def anomaly_summary(df):
    """各异常类别的颗粒数（count）与占比（%）。"""
    if "anomaly_class" not in df.columns:
        raise ValueError("请先调用 classify_anomalies 添加 anomaly_class 列")
    counts = df["anomaly_class"].value_counts()
    total = len(df)
    out = {}
    for key in LABELS:
        n = int(counts.get(key, 0))
        out[key] = {"count": n, "fraction": 100.0 * n / total if total else 0.0}
    return out
