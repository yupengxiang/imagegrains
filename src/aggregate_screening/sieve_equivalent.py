"""筛分等效粒径与质量加权粒径分布。

竞赛评分以标准机械筛分的**质量分布**为准，而 ImageGrains 原生给出的是
**数量分布**。本模块在两者间搭桥：

1. 筛分等效粒径  d = θ₁·b + θ₂·d_eq + θ₃   （默认 b 轴）
2. 质量权重      w = d^γ                （默认 γ=3，体积∝尺寸³）

新人入口：看 ``weighted_analysis`` → ``weighted_percentiles`` → ``size_fractions``。
校准 ``fit_calibration`` 仅在有真实筛分数据时使用。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution

from ._columns import (
    A_AXIS_MM,
    A_AXIS_PX,
    AREA_PX,
    B_AXIS_MM,
    B_AXIS_PX,
)

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
SIEVES: list[float] = [5.0, 10.0, 16.0, 20.0, 25.0, 31.5, 40.0]
DEFAULT_THETA: tuple[float, float, float] = (1.0, 0.0, 0.0)
DEFAULT_GAMMA: float = 3.0
FRACTION_LABELS: list[str] = ["5-10", "10-16", "16-20", "20-25", "25-31.5", "31.5-40"]
assert len(FRACTION_LABELS) == len(SIEVES) - 1, "粒级标签数须为筛孔数-1"

EPS_D = 1e-9  # 质量权重中对 d 的下限保护
EPS_DIV = 1e-12  # 圆度/长宽比中对分母的保护


# ---------------------------------------------------------------------------
# 结构化返回
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SieveAnalysis:
    """一次加权分析的完整结果。"""

    d_sieve: np.ndarray  # (n,) 筛分等效粒径 mm
    w: np.ndarray  # (n,) 质量权重
    d_eq: np.ndarray  # (n,) 面积等效直径 mm
    D10: float
    D50: float
    D90: float
    fractions: dict[str, float]  # 含 "<5" / ">40" 边界桶


@dataclass(frozen=True)
class CalibrationResult:
    theta: tuple[float, float, float]
    gamma: float
    success: bool
    fun: float
    nit: int


# ---------------------------------------------------------------------------
# 几何换算
# ---------------------------------------------------------------------------
def equivalent_diameter(area_px, resolution: float | None) -> np.ndarray:
    """面积等效直径 d_eq = 2·√(A/π)。

    ``area_px`` 是 CSV 的 ``area`` 列（px²，上游 ``scale_grains`` 不缩放它）。
    ``resolution`` 为 ``None`` 时返回全 NaN（仅当 θ₂≠0 才需要它）。
    """
    area = np.asarray(area_px, dtype=float)
    if resolution is None:
        return np.full(area.shape, np.nan)
    area_mm2 = area * resolution**2
    return 2.0 * np.sqrt(area_mm2 / np.pi)


def sieve_diameter(
    b_mm,
    d_eq_mm,
    theta: tuple[float, float, float] = DEFAULT_THETA,
) -> np.ndarray:
    """筛分等效粒径 d = θ₁·b + θ₂·d_eq + θ₃。"""
    b = np.asarray(b_mm, dtype=float)
    deq = np.asarray(d_eq_mm, dtype=float)
    t1, t2, t3 = theta
    if t2 != 0 and np.isnan(deq).any():
        raise ValueError("d_eq 含 NaN 但 theta2≠0：需要提供 resolution 才能计算 d_eq")
    deq = np.nan_to_num(deq, nan=0.0)
    return t1 * b + t2 * deq + t3


def mass_weight(d_mm, gamma: float = DEFAULT_GAMMA) -> np.ndarray:
    """质量权重 w = d^γ，对 d≤0 做下限保护。"""
    d = np.maximum(np.asarray(d_mm, dtype=float), EPS_D)
    return d**gamma


# ---------------------------------------------------------------------------
# 加权统计
# ---------------------------------------------------------------------------
def weighted_percentiles(d_mm, w, percs: tuple[float, ...] = (10, 50, 90)) -> np.ndarray:
    """质量加权分位数：F(d)=Σw·I(dᵢ≤d)/Σw 的阶梯逆。

    与"50% 质量通过筛孔"的筛分语义一致。空输入返回全 NaN。
    """
    d = np.asarray(d_mm, dtype=float)
    w = np.asarray(w, dtype=float)
    percs_arr = np.asarray(percs, dtype=float)
    if d.size == 0:
        return np.full(percs_arr.shape, np.nan)
    order = np.argsort(d)
    cdf = np.cumsum(w[order])
    cdf = cdf / cdf[-1]
    idx = np.searchsorted(cdf, percs_arr / 100.0, side="left")
    idx = np.clip(idx, 0, len(d) - 1)
    return d[order][idx].astype(float)


def size_fractions(
    d_mm,
    w,
    sieves: list[float] = SIEVES,
    labels: list[str] = FRACTION_LABELS,
) -> dict[str, float]:
    """按筛孔序列计算各粒级质量占比（%），含边界桶 ``<min`` / ``>max``。"""
    d = np.asarray(d_mm, dtype=float)
    w = np.asarray(w, dtype=float)
    if d.size == 0:
        out = {lab: 0.0 for lab in labels}
        out[f"<{sieves[0]:g}"] = 0.0
        out[f">{sieves[-1]:g}"] = 0.0
        return out
    total = float(w.sum())
    out: dict[str, float] = {}
    for i, lab in enumerate(labels):
        mask = (d >= sieves[i]) & (d < sieves[i + 1])
        out[lab] = 100.0 * float(w[mask].sum()) / total
    out[f"<{sieves[0]:g}"] = 100.0 * float(w[d < sieves[0]].sum()) / total
    out[f">{sieves[-1]:g}"] = 100.0 * float(w[d >= sieves[-1]].sum()) / total
    return out


def weighted_analysis(
    b_mm,
    area_px,
    resolution: float | None,
    theta: tuple[float, float, float] = DEFAULT_THETA,
    gamma: float = DEFAULT_GAMMA,
    sieves: list[float] = SIEVES,
    percs: tuple[float, ...] = (10, 50, 90),
) -> SieveAnalysis:
    """从逐颗粒几何一次算齐等效粒径、权重、D值与粒级占比。"""
    b = np.asarray(b_mm, dtype=float)
    area = np.asarray(area_px, dtype=float)
    deq = equivalent_diameter(area, resolution)
    d = sieve_diameter(b, deq, theta=theta)
    w = mass_weight(d, gamma=gamma)
    d10, d50, d90 = weighted_percentiles(d, w, percs=percs)
    fracs = size_fractions(d, w, sieves=sieves)
    return SieveAnalysis(d_sieve=d, w=w, d_eq=deq, D10=float(d10), D50=float(d50), D90=float(d90), fractions=fracs)


# ---------------------------------------------------------------------------
# 校准
# ---------------------------------------------------------------------------
def _calibration_loss(
    params: np.ndarray,
    batches: list[tuple[np.ndarray, np.ndarray, float | None]],
    targets: list[tuple[float, float, float]],
    percs: tuple[float, ...] = (10, 50, 90),
) -> float:
    theta = (float(params[0]), float(params[1]), float(params[2]))
    gamma = float(params[3])
    weight = np.array([0.25, 0.5, 0.25])  # D50 权重最高
    losses: list[np.ndarray] = []
    for (b, area, res), (d10_t, d50_t, d90_t) in zip(batches, targets):
        ana = weighted_analysis(b, area, res, theta=theta, gamma=gamma, percs=percs)
        pred = np.array([ana.D10, ana.D50, ana.D90])
        true = np.array([d10_t, d50_t, d90_t])
        rel = (pred - true) / np.maximum(true, 1e-6)
        losses.append(weight * rel**2)
    return float(np.mean(np.concatenate(losses)))


def fit_calibration(
    batches,
    targets: list[tuple[float, float, float]],
    theta0: tuple[float, float, float] = DEFAULT_THETA,
    gamma0: float = DEFAULT_GAMMA,
    bounds: tuple[tuple[float, float], ...] = ((0.0, 3.0), (0.0, 3.0), (-20.0, 20.0), (1.0, 5.0)),
) -> CalibrationResult:
    """用真实筛分数据拟合 (θ₁,θ₂,θ₃,γ)。

    ``batches`` 每项为 ``{"b_mm","area_px","resolution"}`` 或 ``(b_mm, area_px, resolution)``。
    ``targets`` 为各批次机械筛分的 (D10,D50,D90) 真值。
    累积分布为阶梯函数，用无梯度差分进化优化。
    """
    bat_list: list[tuple[np.ndarray, np.ndarray, float | None]] = []
    for bt in batches:
        if isinstance(bt, dict):
            bat_list.append((np.asarray(bt["b_mm"]), np.asarray(bt["area_px"]), bt["resolution"]))
        else:
            b, a, r = bt
            bat_list.append((np.asarray(b), np.asarray(a), r))
    _ = [theta0[0], theta0[1], theta0[2], gamma0]  # 保留签名参数，优化由 bounds 驱动
    res = differential_evolution(
        _calibration_loss, bounds, args=(bat_list, targets), seed=0, maxiter=1000, tol=1e-8, atol=1e-10
    )
    theta = (float(res.x[0]), float(res.x[1]), float(res.x[2]))
    success = bool(res.success) or float(res.fun) < 1e-8
    return CalibrationResult(theta=theta, gamma=float(res.x[3]), success=success, fun=float(res.fun), nit=int(res.nit))


# ---------------------------------------------------------------------------
# CSV 标准化（显式、可测试）
# ---------------------------------------------------------------------------
def infer_resolution(df: pd.DataFrame) -> float | None:
    """从同时含 mm/px 列的 DataFrame 推断 mm/px（b 轴中位数），否则 None。"""
    if B_AXIS_MM in df.columns and B_AXIS_PX in df.columns:
        valid = df[B_AXIS_PX] != 0
        if valid.any():
            ratios = df.loc[valid, B_AXIS_MM] / df.loc[valid, B_AXIS_PX]
            ratios = ratios.replace([np.inf, -np.inf], np.nan).dropna()
            if len(ratios) > 0:
                return float(ratios.median())
    return None


def normalize_grains(df: pd.DataFrame, resolution: float | None = None) -> pd.DataFrame:
    """将任意形态的 grains DataFrame 标准化为含 ``b_mm/a_mm/area_px/d_eq_mm`` 的表。

    - 已含 ``b_mm/a_mm`` → 直接复用；
    - 含 ``ell: b/a-axis (mm)`` → 直接取；
    - 仅含 ``(px)`` 列 → 需 ``resolution`` 换算，否则抛错；
    - 若 ``resolution`` 为 ``None`` 且同时有 mm/px 列，自动推断。
    始终新增 ``area_px`` 与 ``d_eq_mm``，不使用 ``df.attrs`` 隐式通道。
    """
    out = df.copy()
    # 解析分辨率
    if resolution is None:
        inferred = infer_resolution(out)
        if inferred is not None:
            resolution = inferred

    has_mm = B_AXIS_MM in out.columns and A_AXIS_MM in out.columns
    has_px = B_AXIS_PX in out.columns and A_AXIS_PX in out.columns
    has_norm = "b_mm" in out.columns and "a_mm" in out.columns

    if has_norm:
        b_mm = out["b_mm"].to_numpy(dtype=float)
        a_mm = out["a_mm"].to_numpy(dtype=float)
    elif has_mm:
        b_mm = out[B_AXIS_MM].to_numpy(dtype=float)
        a_mm = out[A_AXIS_MM].to_numpy(dtype=float)
    elif has_px:
        if resolution is None:
            raise ValueError("该 DataFrame 只有像素列，需要提供 resolution（mm/px）")
        b_mm = out[B_AXIS_PX].to_numpy(dtype=float) * resolution
        a_mm = out[A_AXIS_PX].to_numpy(dtype=float) * resolution
    else:
        raise ValueError(f"无法识别粒径列：{list(out.columns)}")

    if AREA_PX not in out.columns:
        raise ValueError(f"缺少面积列 {AREA_PX!r}：{list(out.columns)}")
    area_px = out[AREA_PX].to_numpy(dtype=float)

    out["b_mm"] = b_mm
    out["a_mm"] = a_mm
    out["area_px"] = area_px
    out["d_eq_mm"] = equivalent_diameter(area_px, resolution)
    # 显式记录分辨率（列而非 attrs，便于追溯）
    out["__resolution_mm_per_px"] = resolution
    return out


def load_grains_csv(path: str | Path, resolution: float | None = None) -> pd.DataFrame:
    """从 CSV 路径加载并标准化。``resolution`` 语义同 ``normalize_grains``。"""
    df = pd.read_csv(path)
    return normalize_grains(df, resolution=resolution)


# 兼容旧入口（显式提示迁移）
def load_grains_df(grains_csv, resolution: float | None = None) -> pd.DataFrame:
    """兼容旧名：等价于 ``normalize_grains(DataFrame)`` 或 ``load_grains_csv(path)``。"""
    if isinstance(grains_csv, (str, Path)):
        return load_grains_csv(grains_csv, resolution=resolution)
    if isinstance(grains_csv, pd.DataFrame):
        return normalize_grains(grains_csv, resolution=resolution)
    raise TypeError(f"grains_csv 应为路径或 DataFrame，得到 {type(grains_csv)}")
