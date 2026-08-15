"""形貌分类（规则法）。

比赛要求"针片状、圆形、棱角状"为可选加分项。单张俯视 RGB 图像无法获得真实
颗粒厚度，因此这里识别的是**投影形貌**类别，不声称严格的三维针/片状判定。

规则基于 ImageGrains 已输出的几何量：

- 长宽比 AR = b/a（越接近 1 越等轴）
- 圆度 circularity = 4*pi*A/P^2（越接近 1 越圆）
- 凸度 solidity = A / A_convex（越接近 1 轮廓越凸，棱角颗粒较低）

默认阈值来自通用颗粒形态学经验值，需用自采骨料数据重新标定
（见 docs/ai/PLAN.md）。
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# 形貌类别（中英文对照，用于报告输出）
SHAPE_LABELS = {
    "needle_flaky": "针片状候选",
    "round": "圆形",
    "angular": "棱角状",
    "regular": "普通",
}

# 默认规则阈值：needle_flaky / round / angular / regular
DEFAULT_THRESHOLDS = {
    "ar_needle": 0.5,      # AR < 0.5 -> 针片状候选
    "circ_round": 0.85,    # circularity > 0.85
    "sol_round": 0.95,     # solidity > 0.95
    "ar_round": 0.8,       # AR > 0.8（圆形需接近等轴）
    "circ_angular": 0.6,   # circularity < 0.6 -> 棱角状
    "sol_angular": 0.9,    # solidity < 0.9 -> 棱角状
}

B_AXIS_COL = "ell: b-axis (mm)"
A_AXIS_COL = "ell: a-axis (mm)"
AREA_COL = "area"
AREA_CONVEX_COL = "area_convex"
PERIMETER_COL = "perimeter_crofton"


def aspect_ratio(b_mm, a_mm):
    """长宽比 AR = b/a，范围 (0, 1]。"""
    b = np.asarray(b_mm, dtype=float)
    a = np.asarray(a_mm, dtype=float)
    return np.minimum(b, a) / np.maximum(a, 1e-12)


def circularity(area_px, perimeter_px):
    """圆度 4*pi*A/P^2，范围 (0, 1]。"""
    a = np.asarray(area_px, dtype=float)
    p = np.asarray(perimeter_px, dtype=float)
    return 4.0 * np.pi * a / np.maximum(p**2, 1e-12)


def solidity(area_px, area_convex_px):
    """凸度 A/A_convex，范围 (0, 1]。"""
    a = np.asarray(area_px, dtype=float)
    ac = np.asarray(area_convex_px, dtype=float)
    return np.minimum(a, ac) / np.maximum(ac, 1e-12)


def classify_shape(b_mm, a_mm, area_px, area_convex_px, perimeter_px, thresholds=None):
    """逐颗粒形貌分类。

    参数
    ----
    各几何量可以是标量或数组；同时提供时返回逐颗粒类别数组。

    返回
    ----
    ndarray[str]：类别键（SHAPE_LABELS 的键）
    """
    t = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        t.update(thresholds)
    ar = aspect_ratio(b_mm, a_mm)
    circ = circularity(area_px, perimeter_px)
    sol = solidity(area_px, area_convex_px)

    ar = np.asarray(ar)
    circ = np.asarray(circ)
    sol = np.asarray(sol)
    out = np.full(np.broadcast(ar, circ, sol).shape, "regular", dtype=object)
    out[ar < t["ar_needle"]] = "needle_flaky"
    mask_round = (circ > t["circ_round"]) & (sol > t["sol_round"]) & (ar > t["ar_round"])
    out[mask_round] = "round"
    mask_angular = (circ < t["circ_angular"]) | (sol < t["sol_angular"])
    mask_angular &= ~(ar < t["ar_needle"])
    out[mask_angular] = "angular"
    if np.ndim(ar) == 0:
        return out[()]
    return out


def classify_dataset(df, thresholds=None):
    """给 grains DataFrame 加 shape_class / shape_label 列并返回副本。"""
    out = df.copy()
    keys = classify_shape(
        out[B_AXIS_COL].to_numpy(dtype=float),
        out[A_AXIS_COL].to_numpy(dtype=float),
        out[AREA_COL].to_numpy(dtype=float),
        out[AREA_CONVEX_COL].to_numpy(dtype=float),
        out[PERIMETER_COL].to_numpy(dtype=float),
        thresholds=thresholds,
    )
    out["shape_class"] = keys
    out["shape_label"] = [SHAPE_LABELS[k] for k in keys]
    return out


def shape_summary(df):
    """各形貌类别的颗粒数与占比（%）。"""
    if "shape_class" not in df.columns:
        df = classify_dataset(df)
    counts = df["shape_class"].value_counts()
    total = len(df)
    out = {}
    for key in SHAPE_LABELS:
        n = int(counts.get(key, 0))
        out[key] = {"count": n, "fraction": 100.0 * n / total if total else 0.0}
    return out
