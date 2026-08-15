"""一键 CLI：grains CSV / mask 目录 -> 筛分报告。

用法示例
--------
python -m aggregate_screening --grains /path/to/xxx_re_scaled.csv --out_dir /tmp/report
python -m aggregate_screening --grains /path/to/xxx_grains.csv --resolution 0.39 --out_dir /tmp/report
python -m aggregate_screening --mask_dir /path/to/masks --img_dir /path/to/imgs --resolution 0.39 --out_dir /tmp/report
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from imagegrains import grainsizing

from .sieve_equivalent import (
    DEFAULT_GAMMA,
    DEFAULT_THETA,
    SIEVES,
    load_grains_df,
    weighted_analysis,
)
from . import morphology, anomaly, report


def plot_gsd_comparison(df, resolution, out_path, theta=DEFAULT_THETA, gamma=DEFAULT_GAMMA):
    """数量 vs 质量加权累计分布对比图（答辩核心素材）。"""
    b_mm = df["b_mm"].to_numpy(dtype=float)
    area_px = df["area_px"].to_numpy(dtype=float)
    ana = weighted_analysis(b_mm, area_px, resolution, theta=theta, gamma=gamma)

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))

    # 左：累计分布曲线
    for d, w, label in [
        (b_mm, np.ones_like(b_mm), "number-based"),
        (ana["d_sieve"], ana["w"], f"mass-weighted (d^gamma, gamma={gamma})"),
    ]:
        order = np.argsort(d)
        cdf = np.cumsum(w[order]) / np.sum(w[order])
        ax[0].plot(d[order], cdf * 100, label=label)
    for p in (10, 50, 90):
        ax[0].axvline(ana[f"D{p}"], color="gray", ls=":", lw=0.8)
    ax[0].set_xlabel("grain size (mm)")
    ax[0].set_ylabel("cumulative share (%)")
    ax[0].set_title("GSD: number vs mass-weighted")
    ax[0].legend()
    ax[0].grid(alpha=0.3)

    # 右：粒级质量占比柱状图
    fracs = ana["fractions"]
    labels = list(fracs.index)
    ax[1].bar(range(len(labels)), fracs.values)
    ax[1].set_xticks(range(len(labels)))
    ax[1].set_xticklabels(labels, rotation=45, ha="right")
    ax[1].set_ylabel("mass fraction (%)")
    ax[1].set_title("mass fractions per size class")
    ax[1].grid(alpha=0.3, axis="y")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def analyze_grains_csv(grains_csv, resolution, out_dir, theta, gamma, plot=True):
    """分析单个 grains CSV，输出报告与图。"""
    df = load_grains_df(grains_csv, resolution=resolution)
    resolution = df.attrs.get("resolution")
    if resolution is None:
        sys.exit(">> 需要 --resolution（mm/px）：该 CSV 只有像素列")

    scene_id = Path(grains_csv).stem
    summary = report.scene_summary(df, resolution, theta=theta, gamma=gamma, scene_id=scene_id)

    from .sieve_equivalent import sieve_diameter
    d_sieve = sieve_diameter(df["b_mm"].to_numpy(dtype=float),
                             df["d_eq_mm"].to_numpy(dtype=float), theta=theta)
    df_final = anomaly.classify_anomalies(morphology.classify_dataset(df), d_sieve)
    report.save_report(summary, out_dir, df_final=df_final, save_detail_csv=True)
    print(">> 已保存报告到:", Path(out_dir).resolve())

    if plot:
        plot_gsd_comparison(df, resolution, Path(out_dir) / f"{scene_id}_gsd_comparison.png",
                            theta=theta, gamma=gamma)
        print(">> 已保存 GSD 对比图到:", Path(out_dir).resolve())

    print(report.format_report_text(summary))
    return summary


def analyze_mask_dir(img_dir, mask_dir, resolution, out_dir, theta, gamma, plot=True):
    """用 ImageGrains 测量 mask 后调用 analyze_grains_csv。"""
    imgs, masks, _ = grainsizing.load_from_folders(img_dir, mask_dir=mask_dir)
    grains_df = grainsizing.grains_from_masks(masks, image_res=resolution, file_id="batch")
    csv_path = Path(out_dir) / "batch_grains.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    grains_df.to_csv(csv_path, index=False)
    return analyze_grains_csv(csv_path, resolution, out_dir, theta, gamma, plot=plot)


def main():
    parser = argparse.ArgumentParser(
        description="aggregate_screening: 骨料筛分等效粒径与质量加权分布报告",
    )
    parser.add_argument("--grains", default=None, type=str,
                        help="ImageGrains *_grains.csv 或 *_re_scaled.csv 路径")
    parser.add_argument("--img_dir", default=None, type=str,
                        help="图像目录（与 --mask_dir 搭配，自动测量）")
    parser.add_argument("--mask_dir", default=None, type=str,
                        help="mask 目录（*_mask.tif）")
    parser.add_argument("--resolution", default=None, type=float,
                        help="mm/px 分辨率；px 单位 CSV 必填")
    parser.add_argument("--out_dir", default="aggregate_report", type=str,
                        help="输出目录（默认 ./aggregate_report）")
    parser.add_argument("--theta", default=None, type=str,
                        help="等效粒径参数 theta1,theta2,theta3（默认 1,0,0）")
    parser.add_argument("--gamma", default=DEFAULT_GAMMA, type=float,
                        help="质量权重指数（默认 3.0）")
    parser.add_argument("--no_plot", action="store_true",
                        help="不生成对比图")
    args = parser.parse_args()

    theta = tuple(float(x) for x in args.theta.split(",")) if args.theta else DEFAULT_THETA
    if len(theta) != 3:
        sys.exit(">> --theta 需要三个数: theta1,theta2,theta3")

    if args.grains:
        analyze_grains_csv(args.grains, args.resolution, args.out_dir, theta, args.gamma,
                           plot=not args.no_plot)
    elif args.img_dir and args.mask_dir:
        analyze_mask_dir(args.img_dir, args.mask_dir, args.resolution, args.out_dir,
                         theta, args.gamma, plot=not args.no_plot)
    else:
        parser.print_help()
        sys.exit(">> 需要 --grains 或 --img_dir + --mask_dir")


if __name__ == "__main__":
    main()
