"""筛分等效粒径与质量加权粒径分布。

竞赛评分的基准是标准机械筛分结果（质量分布），而 ImageGrains 原生输出的是
逐颗粒数量分布。两者不能直接对比：

- 数量分布给每颗粒相同的权重；质量分布按颗粒质量加权。
  几何相似且密度接近的颗粒 m ~ d^3，因此质量权重 w = d^gamma（gamma 初始为 3）。
- 视觉 2D 投影尺寸（b 轴、面积等效直径）与"颗粒能否通过方孔筛"并不等价，
  需要用一个筛分等效粒径 d_sieve 来桥接：

    d_sieve = theta1 * b + theta2 * d_eq + theta3

  默认 theta = (1, 0, 0)，即直接用 b 轴（颗粒通过筛孔主要由较短的尺度控制）。

校准（fit_calibration）需要真实筛分实验数据（自采 batch：称重 + 机械筛分 + 拍照），
在缺少真值数据时使用默认参数即可产出合理基线。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from scipy.optimize import differential_evolution

# 标准粗骨料筛孔序列（mm），与比赛范围 5-40 mm 对应
SIEVES = [5.0, 10.0, 16.0, 20.0, 25.0, 31.5, 40.0]

# 默认筛分等效粒径参数：d_sieve = b（b 轴）
DEFAULT_THETA = (1.0, 0.0, 0.0)

# 默认质量权重指数（几何相似颗粒 m ~ d^3）
DEFAULT_GAMMA = 3.0

# 粒级区间名称（用于输出）
FRACTION_LABELS = [
    "5-10", "10-16", "16-20", "20-25", "25-31.5", "31.5-40",
]

# ImageGrains grains CSV 中可用的几何列（mm 或 px 视数据而定）
B_AXIS_COL = "ell: b-axis (mm)"
A_AXIS_COL = "ell: a-axis (mm)"
B_AXIS_PX_COL = "ell: b-axis (px)"
AREA_PX_COL = "area"
SOLIDITY_COL = "solidity"
PERIMETER_COL = "perimeter_crofton"


def equivalent_diameter(area_px, resolution):
    """面积等效圆直径 d_eq = 2*sqrt(A/pi)，从像素面积换算到 mm。

    area_px 是 ImageGrains grains CSV 中的 area 列（px^2，scale_grains 不缩放它）；
    resolution 是 mm/px。resolution 为 None（只有 mm 轴列、无尺度信息）时返回 NaN，
    此时 d_eq 不可用（theta2 非 0 的等效粒径公式会忽略 NaN 颗粒）。
    """
    area = np.asarray(area_px, dtype=float)
    if resolution is None:
        return np.full(area.shape, np.nan)
    area_mm2 = area * resolution ** 2
    return 2.0 * np.sqrt(area_mm2 / np.pi)


def sieve_diameter(b_mm, d_eq_mm, theta=DEFAULT_THETA):
    """筛分等效粒径 d_sieve = theta1 * b + theta2 * d_eq + theta3。

    默认 theta=(1,0,0) 时退化为 b 轴。theta 由 fit_calibration 用真实筛分数据校准。
    d_eq 为 NaN（无分辨率信息）时该颗粒的 d_eq 项按 0 处理（仅当 theta2 非 0 才相关）。
    """
    b = np.asarray(b_mm, dtype=float)
    deq = np.asarray(d_eq_mm, dtype=float)
    t1, t2, t3 = theta
    deq = np.nan_to_num(deq, nan=0.0)
    return t1 * b + t2 * deq + t3


def mass_weight(d_mm, gamma=DEFAULT_GAMMA):
    """质量代理权重 w = d^gamma。gamma=3 对应几何相似颗粒 m ~ d^3。

    对 d <= 0 的退化值做下限保护，避免负值幂产生 NaN。
    """
    d = np.maximum(np.asarray(d_mm, dtype=float), 1e-9)
    return d ** gamma


def weighted_percentiles(d_mm, w, percs=(10, 50, 90)):
    """质量加权累计分布 F(d) = sum(w_i * I(d_i<=d)) / sum(w_i) 的分位数。

    采用累积分布的阶梯逆（最小的 d 使 F(d) >= p），与"50% 质量通过筛孔"的
    物理语义一致。返回与 percs 等长的数组；空输入返回 NaN。
    """
    d = np.asarray(d_mm, dtype=float)
    w = np.asarray(w, dtype=float)
    percs = np.atleast_1d(np.asarray(percs, dtype=float))
    if d.size == 0:
        return np.full(percs.shape, np.nan)
    order = np.argsort(d)
    d_sorted = d[order]
    w_sorted = w[order]
    cdf = np.cumsum(w_sorted)
    cdf = cdf / cdf[-1]
    frac = percs / 100.0
    idx = np.searchsorted(cdf, frac, side="left")
    idx = np.clip(idx, 0, len(d_sorted) - 1)
    return d_sorted[idx].astype(float)


def size_fractions(d_mm, w, sieves=SIEVES, labels=FRACTION_LABELS):
    """按筛孔序列计算各粒级质量占比（%）。

    粒级 [sieves[i], sieves[i+1])；小于最小筛孔的归 '<min'，大于最大筛孔的归 '>max'。
    返回 pandas Series：labels 顺序的粒级 + 两个边界桶。
    """
    d = np.asarray(d_mm, dtype=float)
    w = np.asarray(w, dtype=float)
    if d.size == 0:
        out = {lab: 0.0 for lab in labels}
        out[f"<{sieves[0]:g}"] = 0.0
        out[f">{sieves[-1]:g}"] = 0.0
        return pd.Series(out)
    total = w.sum()
    fracs = {}
    for i in range(len(sieves) - 1):
        mask = (d >= sieves[i]) & (d < sieves[i + 1])
        fracs[labels[i]] = 100.0 * w[mask].sum() / total
    fracs[f"<{sieves[0]:g}"] = 100.0 * w[d < sieves[0]].sum() / total
    fracs[f">{sieves[-1]:g}"] = 100.0 * w[d >= sieves[-1]].sum() / total
    return pd.Series(fracs)


def weighted_analysis(
    b_mm,
    area_px,
    resolution,
    theta=DEFAULT_THETA,
    gamma=DEFAULT_GAMMA,
    sieves=SIEVES,
    percs=(10, 50, 90),
):
    """从逐颗粒几何数据一次算齐：等效粒径、质量权重、D10/D50/D90、粒级占比。

    参数
    ----
    b_mm : 每颗粒 b 轴（mm）
    area_px : 每颗粒面积（px^2）
    resolution : mm/px
    theta, gamma : 等效粒径与质量权重参数

    返回
    ----
    dict: d_sieve, w, D10/D50/D90（dict）, fractions（Series）
    """
    b = np.asarray(b_mm, dtype=float)
    area = np.asarray(area_px, dtype=float)
    deq = equivalent_diameter(area, resolution)
    d = sieve_diameter(b, deq, theta=theta)
    w = mass_weight(d, gamma=gamma)
    d_perc = weighted_percentiles(d, w, percs=percs)
    d10, d50, d90 = d_perc
    fracs = size_fractions(d, w, sieves=sieves)
    return {
        "d_sieve": d,
        "w": w,
        "d_eq": deq,
        "D10": d10,
        "D50": d50,
        "D90": d90,
        "fractions": fracs,
    }


def _calibration_loss(params, batches, targets, percs=(10, 50, 90), w_targets=None):
    """校准目标函数：预测 D10/D50/D90 与真值的加权相对误差。

    batches : list of (b_mm 数组, area_px 数组, resolution)
    targets : list of (d10, d50, d90) 真值（来自机械筛分）
    w_targets : 可选，粒级占比真值的权重；None 时只优化 D 值
    """
    theta = (params[0], params[1], params[2])
    gamma = params[3]
    losses = []
    for (b, area, res), (d10_t, d50_t, d90_t) in zip(batches, targets):
        ana = weighted_analysis(b, area, res, theta=theta, gamma=gamma, percs=percs)
        pred = np.array([ana["D10"], ana["D50"], ana["D90"]])
        true = np.array([d10_t, d50_t, d90_t])
        rel = (pred - true) / np.maximum(true, 1e-6)
        # D50 权重最高（评分核心）
        losses.append((rel * np.array([0.25, 0.5, 0.25])) ** 2)
    return float(np.mean(np.concatenate(losses)))


def fit_calibration(
    batches,
    targets,
    theta0=DEFAULT_THETA,
    gamma0=DEFAULT_GAMMA,
    bounds=((0.0, 3.0), (0.0, 3.0), (-20.0, 20.0), (1.0, 5.0)),
):
    """用真实筛分数据拟合 (theta1, theta2, theta3, gamma)。

    参数
    ----
    batches : list of dict/tuple，每项提供 b_mm、area_px、resolution
    targets : list of (d10, d50, d90) 真值（机械筛分，mm）
    theta0, gamma0 : 初始参数
    bounds : 参数边界 (theta1, theta2, theta3, gamma)

    返回
    ----
    dict: theta, gamma, success, fun（损失值）
    """
    bat_list = []
    for bt in batches:
        if isinstance(bt, dict):
            bat_list.append((bt["b_mm"], bt["area_px"], bt["resolution"]))
        else:
            bat_list.append(bt)
    x0 = [theta0[0], theta0[1], theta0[2], gamma0]
    # 累积分布是阶梯函数，对梯度优化器不平滑，用无梯度差分进化
    res = differential_evolution(
        _calibration_loss, bounds, args=(bat_list, targets), seed=0,
        maxiter=1000, tol=1e-8, atol=1e-10,
    )
    theta = (res.x[0], res.x[1], res.x[2])
    success = bool(res.success) or float(res.fun) < 1e-8
    return {
        "theta": theta,
        "gamma": float(res.x[3]),
        "success": success,
        "fun": float(res.fun),
        "nit": int(res.nit),
    }


def load_grains_df(grains_csv, resolution=None):
    """加载 ImageGrains 的 *_grains.csv（或 *_re_scaled.csv），返回标准化 DataFrame。

    - 输入可以是 CSV 路径或已读入的 pandas DataFrame；
    - 若含 mm 列，直接使用；若只有 px 列，用 resolution（mm/px）换算；
    - 若同时含 mm 与 px 列且未提供 resolution，自动按 mm/px 中位数推断；
    - 输出统一含：b_mm、a_mm、area_px、d_eq_mm 等列；
    - 无法得到尺度时（只有 px 列且无 resolution）报错；只有 mm 列时 d_eq_mm 为 NaN。
    """
    if isinstance(grains_csv, (str, Path)):
        df = pd.read_csv(grains_csv)
    else:
        df = grains_csv.copy()

    has_mm = B_AXIS_COL in df.columns and A_AXIS_COL in df.columns
    has_px = B_AXIS_PX_COL in df.columns and A_AXIS_COL.replace("(mm)", "(px)") in df.columns

    if resolution is None and has_mm and has_px:
        ratio = df[B_AXIS_COL] / df[B_AXIS_PX_COL].replace(0, np.nan)
        ratio = ratio.replace([np.inf, -np.inf], np.nan).dropna()
        if len(ratio) > 0:
            resolution = float(np.median(ratio.to_numpy()))

    if "b_mm" in df.columns and "a_mm" in df.columns:
        b_mm = df["b_mm"].to_numpy(dtype=float)
        a_mm = df["a_mm"].to_numpy(dtype=float)
    elif has_mm:
        b_mm = df[B_AXIS_COL].to_numpy(dtype=float)
        a_mm = df[A_AXIS_COL].to_numpy(dtype=float)
    elif has_px:
        if resolution is None:
            raise ValueError(
                f"{grains_csv} 只有像素列，需要提供 resolution（mm/px）"
            )
        b_mm = df[B_AXIS_PX_COL].to_numpy(dtype=float) * resolution
        a_mm = df[A_AXIS_COL.replace("(mm)", "(px)")].to_numpy(dtype=float) * resolution
    else:
        raise ValueError(f"无法识别粒径列：{list(df.columns)}")
    area_px = df[AREA_PX_COL].to_numpy(dtype=float)
    out = df.copy()
    out["b_mm"] = b_mm
    out["a_mm"] = a_mm
    out["area_px"] = area_px
    out["d_eq_mm"] = equivalent_diameter(area_px, resolution)
    out.attrs["resolution"] = resolution
    return out
