"""场景级汇总报告与消融对照。

把一个场景（一张图或一批图）的最终结果汇总为：

- 颗粒数与异常统计；
- 数量分布 vs 质量加权分布的 D10/D50/D90 对照（答辩核心素材）；
- 粒级质量占比；
- 形貌类别占比；
- 逐颗粒明细 CSV 与 Markdown/文本报告。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from .sieve_equivalent import (
    DEFAULT_GAMMA,
    DEFAULT_THETA,
    SIEVES,
    load_grains_df,
    weighted_analysis,
    weighted_percentiles,
)
from . import morphology, anomaly


def scene_summary(
    df,
    resolution,
    theta=DEFAULT_THETA,
    gamma=DEFAULT_GAMMA,
    sieves=SIEVES,
    scene_id="",
    exclude_anomalies=True,
):
    """从 grains 数据计算场景级汇总。

    参数
    ----
    df : grains DataFrame 或 CSV 路径（原始 ImageGrains 输出或已标准化均可）
    resolution : mm/px（None 时尝试从 mm/px 列自动推断）
    exclude_anomalies : 为 True 时，D 值与粒级占比用"剔除 oversized/undersized/
        疑似泥团后的正常骨料子集"计算（异物不参与级配统计，符合竞赛语义）；
        异常统计始终基于全部颗粒。

    返回
    ----
    dict：完整汇总（含 D 值对照、粒级占比、形貌、异常）
    """
    df = load_grains_df(df, resolution=resolution)
    resolution = df.attrs.get("resolution", resolution)
    b_mm = df["b_mm"].to_numpy(dtype=float)
    area_px = df["area_px"].to_numpy(dtype=float)

    # 1) 数量分布百分位（基线，ImageGrains 原生口径）
    d_num = weighted_percentiles(b_mm, np.ones_like(b_mm), percs=(10, 50, 90))
    # 2) 质量加权分析（筛分口径，默认全颗粒）
    ana = weighted_analysis(b_mm, area_px, resolution, theta=theta, gamma=gamma, sieves=sieves)

    # 3) 形貌与异常
    df_shape = morphology.classify_dataset(df)
    df_final = anomaly.classify_anomalies(df_shape, ana["d_sieve"])
    shape_sum = morphology.shape_summary(df_final)
    anom_sum = anomaly.anomaly_summary(df_final)

    # 4) 剔除异常后的统计（默认口径）
    anom_stat = None
    if exclude_anomalies:
        mask_normal = df_final["anomaly_class"].to_numpy() == "normal"
        if mask_normal.sum() > 0:
            ana_norm = weighted_analysis(
                b_mm[mask_normal], area_px[mask_normal], resolution,
                theta=theta, gamma=gamma, sieves=sieves,
            )
            anom_stat = {
                "n_particles": int(mask_normal.sum()),
                "percentiles_mass_weighted": {
                    "D10": float(ana_norm["D10"]),
                    "D50": float(ana_norm["D50"]),
                    "D90": float(ana_norm["D90"]),
                },
                "mass_fractions": {str(k): float(v) for k, v in ana_norm["fractions"].items()},
            }

    summary = {
        "scene_id": scene_id,
        "n_particles": int(len(df)),
        "resolution_mm_per_px": resolution,
        "theta": list(theta),
        "gamma": gamma,
        "exclude_anomalies": exclude_anomalies,
        "percentiles_number_based": {
            "D10": float(d_num[0]), "D50": float(d_num[1]), "D90": float(d_num[2])
        },
        "percentiles_mass_weighted": {
            "D10": float(ana["D10"]), "D50": float(ana["D50"]), "D90": float(ana["D90"])
        },
        "mass_fractions": {str(k): float(v) for k, v in ana["fractions"].items()},
        "normal_only": anom_stat,
        "shape": shape_sum,
        "anomalies": anom_sum,
    }
    return summary


def save_report(
    summary,
    out_dir,
    df_final=None,
    save_detail_csv=False,
):
    """保存场景报告：summary.json + 可选逐颗粒明细 CSV + 文本摘要。"""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scene_id = summary["scene_id"] or "scene"
    json_path = out_dir / f"{scene_id}_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    if save_detail_csv and df_final is not None:
        df_final.to_csv(out_dir / f"{scene_id}_particles_annotated.csv", index=False)

    txt = format_report_text(summary)
    (out_dir / f"{scene_id}_report.txt").write_text(txt, encoding="utf-8")
    return out_dir


def format_report_text(summary):
    """把 summary dict 格式化为易读文本（答辩/现场展示用）。"""
    num = summary["percentiles_number_based"]
    mass = summary["percentiles_mass_weighted"]
    lines = [
        f"场景: {summary['scene_id']}",
        f"颗粒数: {summary['n_particles']}  分辨率: {summary['resolution_mm_per_px']} mm/px",
        "",
        f"D10 数量={num['D10']:.1f}mm / 质量加权={mass['D10']:.1f}mm",
        f"D50 数量={num['D50']:.1f}mm / 质量加权={mass['D50']:.1f}mm",
        f"D90 数量={num['D90']:.1f}mm / 质量加权={mass['D90']:.1f}mm",
    ]
    if summary.get("normal_only"):
        nm = summary["normal_only"]
        lines += [
            "",
            f"剔除异常后（正常骨料 {nm['n_particles']} 颗）:",
            f"  D10={nm['percentiles_mass_weighted']['D10']:.1f}mm  "
            f"D50={nm['percentiles_mass_weighted']['D50']:.1f}mm  "
            f"D90={nm['percentiles_mass_weighted']['D90']:.1f}mm",
        ]
    lines += ["", "粒级质量占比 (%):"]
    fracs = summary["normal_only"]["mass_fractions"] if summary.get("normal_only") else summary["mass_fractions"]
    for k, v in fracs.items():
        lines.append(f"  {k:>10}: {v:5.1f}")
    lines.append("")
    lines.append("形貌分类:")
    for k, v in summary["shape"].items():
        lines.append(f"  {morphology.SHAPE_LABELS[k]}: {v['count']} 颗 ({v['fraction']:.1f}%)")
    lines.append("")
    lines.append("异常检测:")
    for k, v in summary["anomalies"].items():
        lines.append(f"  {anomaly.LABELS[k]}: {v['count']} 颗 ({v['fraction']:.1f}%)")
    return "\n".join(lines)


def ablation_table(df, resolution, thetas=None, gammas=None):
    """消融对照表（答辩素材）：不同口径的 D50 与粒级占比。

    口径：
    - number：数量分布（ImageGrains 原生）
    - b_axis_weighted：b 轴 + d^gamma 加权（默认 gamma=3）
    - calibrated：fit_calibration 拟合后的 theta/gamma（若有）
    """
    rows = []
    df = load_grains_df(df, resolution=resolution)
    b_mm = df["b_mm"].to_numpy(dtype=float)
    area_px = df["area_px"].to_numpy(dtype=float)

    d_num = weighted_percentiles(b_mm, np.ones_like(b_mm), percs=(50,))
    rows.append({"method": "number", "theta": None, "gamma": None, "D50": float(d_num[0])})

    candidates = []
    if gammas:
        for g in gammas:
            candidates.append((DEFAULT_THETA, g))
    if thetas:
        for th in thetas:
            candidates.append((tuple(th), DEFAULT_GAMMA))
    if not candidates:
        candidates = [(DEFAULT_THETA, DEFAULT_GAMMA)]

    for theta, gamma in candidates:
        ana = weighted_analysis(b_mm, area_px, resolution, theta=theta, gamma=gamma)
        rows.append(
            {
                "method": f"theta={tuple(round(x, 3) for x in theta)}, gamma={gamma}",
                "theta": theta,
                "gamma": gamma,
                "D50": float(ana["D50"]),
            }
        )
    return pd.DataFrame(rows)
