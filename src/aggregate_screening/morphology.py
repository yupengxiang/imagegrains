"""形貌分类（规则法，投影形貌）。

单张俯视 RGB 无法得厚度，这里只做**投影形貌**判定：
针片状候选 / 圆形 / 棱角状 / 普通，基于长宽比、圆度、凸度。

默认阈值来自通用经验，需用自采骨料重标定。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ._columns import AREA_CONVEX_PX, AREA_PX, B_AXIS_MM, A_AXIS_MM, PERIMETER_PX

SHAPE_LABELS: dict[str, str] = {
    "needle_flaky": "针片状候选",
    "round": "圆形",
    "angular": "棱角状",
    "regular": "普通",
}


@dataclass(frozen=True)
class MorphThresholds:
    ar_needle: float = 0.5
    circ_round: float = 0.85
    sol_round: float = 0.95
    ar_round: float = 0.8
    circ_angular: float = 0.6
    sol_angular: float = 0.9


DEFAULT_THRESHOLDS = MorphThresholds()
_EPS = 1e-12


def _aspect_ratio(b_mm: np.ndarray, a_mm: np.ndarray) -> np.ndarray:
    return np.minimum(b_mm, a_mm) / np.maximum(a_mm, _EPS)


def _circularity(area_px: np.ndarray, perimeter_px: np.ndarray) -> np.ndarray:
    return 4.0 * np.pi * area_px / np.maximum(perimeter_px**2, _EPS)


def _solidity(area_px: np.ndarray, area_convex_px: np.ndarray) -> np.ndarray:
    return np.minimum(area_px, area_convex_px) / np.maximum(area_convex_px, _EPS)


def _resolve_thresholds(overrides: dict | MorphThresholds | None) -> MorphThresholds:
    if overrides is None:
        return DEFAULT_THRESHOLDS
    if isinstance(overrides, MorphThresholds):
        return overrides
    # dict 覆盖
    base = DEFAULT_THRESHOLDS.__dict__.copy()
    base.update(overrides)
    return MorphThresholds(**base)


def aspect_ratio(b_mm, a_mm) -> np.ndarray:
    """长宽比 AR = b/a ∈ (0,1]。兼容旧名，内部转调 ``_aspect_ratio``。"""
    return _aspect_ratio(np.asarray(b_mm, dtype=float), np.asarray(a_mm, dtype=float))


def circularity(area_px, perimeter_px) -> np.ndarray:
    """圆度 4πA/P²。兼容旧名。"""
    return _circularity(np.asarray(area_px, dtype=float), np.asarray(perimeter_px, dtype=float))


def solidity(area_px, area_convex_px) -> np.ndarray:
    """凸度 A/A_convex。兼容旧名。"""
    return _solidity(np.asarray(area_px, dtype=float), np.asarray(area_convex_px, dtype=float))


def classify_shape(
    b_mm,
    a_mm,
    area_px,
    area_convex_px,
    perimeter_px,
    thresholds: dict | MorphThresholds | None = None,
):
    """逐颗粒形貌分类。

    优先级：``angular > round > needle > regular``（angular 排除 needle）。
    标量输入返回标量字符串，数组输入返回数组（兼容旧测试）。
    """
    t = _resolve_thresholds(thresholds)
    b = np.asarray(b_mm, dtype=float)
    a = np.asarray(a_mm, dtype=float)
    is_scalar = b.ndim == 0 and a.ndim == 0
    ar = _aspect_ratio(b, a)
    circ = _circularity(np.asarray(area_px, dtype=float), np.asarray(perimeter_px, dtype=float))
    sol = _solidity(np.asarray(area_px, dtype=float), np.asarray(area_convex_px, dtype=float))

    is_needle = ar < t.ar_needle
    is_round = (circ > t.circ_round) & (sol > t.sol_round) & (ar > t.ar_round)
    is_angular = ((circ < t.circ_angular) | (sol < t.sol_angular)) & ~is_needle

    out = np.full(np.shape(ar), "regular", dtype=object)
    out[is_needle] = "needle_flaky"
    out[is_round] = "round"
    out[is_angular] = "angular"
    if is_scalar:
        return str(out.item())
    return out


def _pick_col(df: pd.DataFrame, norm: str, raw: str) -> np.ndarray:
    col = norm if norm in df.columns else raw
    return df[col].to_numpy(dtype=float)


def classify_dataset(
    df: pd.DataFrame, thresholds: dict | MorphThresholds | None = None
) -> pd.DataFrame:
    """给 DataFrame 加 ``shape_class / shape_label`` 列。"""
    # 兼容 normalize 后的 b_mm 与原始 CSV 的 B_AXIS_MM
    b = _pick_col(df, "b_mm", B_AXIS_MM)
    a = _pick_col(df, "a_mm", A_AXIS_MM)
    area = _pick_col(df, AREA_PX, AREA_PX)
    area_c = _pick_col(df, AREA_CONVEX_PX, AREA_CONVEX_PX)
    perim = _pick_col(df, PERIMETER_PX, PERIMETER_PX)
    keys = classify_shape(b, a, area, area_c, perim, thresholds=thresholds)
    out = df.copy()
    out["shape_class"] = keys
    out["shape_label"] = [SHAPE_LABELS[k] for k in keys]
    return out


def shape_summary(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """各形貌类别的颗粒数与占比。需先 ``classify_dataset``。"""
    if "shape_class" not in df.columns:
        raise ValueError("请先调用 classify_dataset 添加 shape_class 列")
    counts = df["shape_class"].value_counts()
    total = len(df)
    return {
        key: {"count": int(counts.get(key, 0)), "fraction": 100.0 * int(counts.get(key, 0)) / total if total else 0.0}
        for key in SHAPE_LABELS
    }
