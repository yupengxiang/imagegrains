"""一键 CLI：grains CSV / mask 目录 -> 筛分报告."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from imagegrains import grainsizing

from . import anomaly, morphology, report
from .sieve_equivalent import DEFAULT_GAMMA, DEFAULT_THETA, load_grains_csv, normalize_grains


def _parse_theta(s: str | None) -> tuple[float, float, float]:
    if s is None:
        return DEFAULT_THETA
    parts = [p.strip() for p in s.split(",") if p.strip() != ""]
    if len(parts) != 3:
        raise ValueError("--theta 需要三个数: theta1,theta2,theta3，例如 1,0,0")
    try:
        return (float(parts[0]), float(parts[1]), float(parts[2]))
    except ValueError as e:
        raise ValueError(f"--theta 解析失败: {s!r}") from e


def plot_gsd_comparison(
    df: pd.DataFrame,
    resolution: float | None,
    out_path: str | Path,
    theta: tuple[float, float, float] = DEFAULT_THETA,
    gamma: float = DEFAULT_GAMMA,
) -> None:
    """数量 vs 质量加权累计分布对比图。"""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # df 已标准化，取 b_mm / area_px
    b_mm = df["b_mm"].to_numpy(dtype=float)
    area_px = df["area_px"].to_numpy(dtype=float)
    from .sieve_equivalent import weighted_analysis

    ana = weighted_analysis(b_mm, area_px, resolution, theta=theta, gamma=gamma)

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))

    # 左：累计分布
    cdf_number = np.cumsum(np.ones_like(b_mm)[np.argsort(b_mm)]) / len(b_mm)
    order_n = np.argsort(b_mm)
    ax[0].plot(b_mm[order_n], cdf_number * 100, label="number-based")

    order_m = np.argsort(ana.d_sieve)
    cdf_mass = np.cumsum(ana.w[order_m]) / ana.w.sum()
    ax[0].plot(ana.d_sieve[order_m], cdf_mass * 100, label=f"mass-weighted (gamma={gamma})")

    for p in (10, 50, 90):
        v = getattr(ana, f"D{p}")
        ax[0].axvline(v, color="gray", ls=":", lw=0.8)
    ax[0].set_xlabel("grain size (mm)")
    ax[0].set_ylabel("cumulative share (%)")
    ax[0].set_title("GSD: number vs mass-weighted")
    ax[0].legend()
    ax[0].grid(alpha=0.3)

    # 右：粒级占比
    labels = list(ana.fractions.keys())
    ax[1].bar(range(len(labels)), list(ana.fractions.values()))
    ax[1].set_xticks(range(len(labels)))
    ax[1].set_xticklabels(labels, rotation=45, ha="right")
    ax[1].set_ylabel("mass fraction (%)")
    ax[1].set_title("mass fractions per size class")
    ax[1].grid(alpha=0.3, axis="y")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def analyze_grains_csv(
    grains_csv: str | Path,
    resolution: float | None,
    out_dir: str | Path,
    theta: tuple[float, float, float],
    gamma: float,
    plot: bool = True,
):
    """分析单个 grains CSV，输出报告与图。返回 SceneSummary。"""
    path = Path(grains_csv)
    # 先标准化以获得 df 与分辨率，供绘图复用
    df_norm = load_grains_csv(path, resolution=resolution)
    res_val = df_norm["__resolution_mm_per_px"].iloc[0]
    resolution_eff: float | None = None if pd.isna(res_val) else float(res_val)
    if resolution_eff is None:
        raise ValueError(f"{grains_csv} 只有像素列，需要提供 --resolution（mm/px）")

    summary, df_final = report.scene_summary(df_norm, resolution=resolution_eff, theta=theta, gamma=gamma, scene_id=path.stem)
    report.save_report(summary, out_dir, df_final=df_final)
    print(">> 已保存报告到:", Path(out_dir).resolve())
    if plot:
        plot_gsd_comparison(df_norm, resolution_eff, Path(out_dir) / f"{path.stem}_gsd_comparison.png", theta=theta, gamma=gamma)
        print(">> 已保存 GSD 对比图到:", Path(out_dir).resolve())
    print(report.format_report_text(summary))
    return summary


def analyze_mask_dir(
    img_dir: str | Path,
    mask_dir: str | Path,
    resolution: float | None,
    out_dir: str | Path,
    theta: tuple[float, float, float],
    gamma: float,
    plot: bool = True,
):
    """直接对 mask 目录做测量并分析（无 CSV 落盘回读）。"""
    if resolution is None:
        raise ValueError("mask 模式需要 --resolution（mm/px）")
    imgs, masks, _ = grainsizing.load_from_folders(str(img_dir), mask_dir=str(mask_dir))
    grains_df = grainsizing.grains_from_masks(masks, image_res=resolution, file_id="batch")
    # DataFrame 直通标准化，无需落地 CSV
    df_norm = normalize_grains(grains_df, resolution=resolution)
    summary, df_final = report.scene_summary(df_norm, resolution=resolution, theta=theta, gamma=gamma, scene_id="batch")
    report.save_report(summary, out_dir, df_final=df_final)
    print(">> 已保存报告到:", Path(out_dir).resolve())
    if plot:
        plot_gsd_comparison(df_norm, resolution, Path(out_dir) / "batch_gsd_comparison.png", theta=theta, gamma=gamma)
        print(">> 已保存 GSD 对比图到:", Path(out_dir).resolve())
    print(report.format_report_text(summary))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="aggregate_screening: 骨料筛分等效粒径与质量加权分布报告")
    parser.add_argument("--grains", default=None, type=str, help="ImageGrains *_grains.csv 或 *_re_scaled.csv 路径")
    parser.add_argument("--img_dir", default=None, type=str, help="图像目录（与 --mask_dir 搭配，自动测量）")
    parser.add_argument("--mask_dir", default=None, type=str, help="mask 目录（*_mask.tif）")
    parser.add_argument("--resolution", default=None, type=float, help="mm/px 分辨率；px 单位 CSV 必填")
    parser.add_argument("--out_dir", default="aggregate_report", type=str, help="输出目录（默认 ./aggregate_report）")
    parser.add_argument("--theta", default=None, type=str, help="等效粒径参数 theta1,theta2,theta3（默认 1,0,0）")
    parser.add_argument("--gamma", default=DEFAULT_GAMMA, type=float, help="质量权重指数（默认 3.0）")
    parser.add_argument("--no_plot", action="store_true", help="不生成对比图")
    args = parser.parse_args()

    try:
        theta = _parse_theta(args.theta)
    except ValueError as e:
        parser.print_help()
        sys.exit(f">> {e}")

    try:
        if args.grains:
            analyze_grains_csv(args.grains, args.resolution, args.out_dir, theta, args.gamma, plot=not args.no_plot)
        elif args.img_dir and args.mask_dir:
            analyze_mask_dir(args.img_dir, args.mask_dir, args.resolution, args.out_dir, theta, args.gamma, plot=not args.no_plot)
        else:
            parser.print_help()
            sys.exit(">> 需要 --grains 或 --img_dir + --mask_dir")
    except ValueError as e:
        sys.exit(f">> {e}")
    except FileNotFoundError as e:
        sys.exit(f">> 文件未找到: {e}")


if __name__ == "__main__":
    main()
