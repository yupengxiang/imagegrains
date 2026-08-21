"""可视化：覆盖四任务的直观图片。

- 任务1 精细识别：检测总览（原图/mask/叠加）- 已有 composite.png，再补三联图
- 任务2 粒径分析：长短轴叠加 + 比例尺
- 任务3 形状分类：按形态分图
- 任务4 异常检测：按异常分图

仅依赖 Pillow + matplotlib + numpy，无 opencv。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from ._columns import A_AXIS_PX, B_AXIS_PX


def _load_image(path: str | Path) -> np.ndarray:
    p = Path(path)
    with Image.open(p) as im:
        im = ImageOps.exif_transpose(im)
        if im.mode != "RGB":
            im = im.convert("RGB")
        return np.array(im)


def _load_mask(path: str | Path) -> np.ndarray:
    p = Path(path)
    with Image.open(p) as im:
        return np.array(im)


def _draw_scale_bar(ax, resolution: float | None, bar_mm: float = 50.0):
    """在轴右下角绘制比例尺（白底黑线）。"""
    if resolution is None or resolution <= 0:
        return
    # 选 50 mm 或 100 mm 中较适合当前视野的
    for cand in [50.0, 100.0, 20.0, 10.0]:
        px = cand / resolution
        # 占图宽 15-25% 为宜
        xlim = ax.get_xlim()
        width = xlim[1] - xlim[0]
        if width * 0.15 < px < width * 0.3:
            bar_mm = cand
            break
    bar_px = bar_mm / resolution
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    # 右下角内缩 5%
    x = x1 - bar_px - (x1 - x0) * 0.05
    y = y0 + (y1 - y0) * 0.05
    h = (y1 - y0) * 0.02
    rect = patches.Rectangle((x, y), bar_px, h, facecolor="white", edgecolor="black", linewidth=1.2, zorder=10)
    ax.add_patch(rect)
    ax.text(x + bar_px / 2, y + h * 1.8, f"{bar_mm:g} mm", ha="center", va="bottom", fontsize=8, color="black",
            bbox=dict(facecolor="white", edgecolor="none", pad=1.2, alpha=0.85), zorder=11)


def plot_axes_overlay(
    image_path: str | Path,
    df,
    out_path: str | Path,
    resolution: float | None = 0.208,
    max_draw: int = 400,
):
    """任务2：每颗粒长短轴叠加 + 比例尺。

    df 需含 ell: a/b-axis (px)、orientation、centerpoint y/x。
    为可读性，超过 max_draw 颗时最长的 N 颗优先绘制。
    """
    img = _load_image(image_path)
    h, w = img.shape[0], img.shape[1]

    # 取最长的 max_draw 颗避免过密
    if len(df) > max_draw:
        df = df.nlargest(max_draw, A_AXIS_PX)

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    ax.imshow(img)
    ax.set_axis_off()

    for _, row in df.iterrows():
        try:
            cy = float(row["centerpoint y"])
            cx = float(row["centerpoint x"])
            a = float(row[A_AXIS_PX])
            b = float(row[B_AXIS_PX])
            theta = float(row["orientation"])  # rad, a 方向
        except Exception:
            continue
        # a 全长，半长绘
        dx_a = np.cos(theta) * a / 2
        dy_a = -np.sin(theta) * a / 2  # 图像 y 向下
        dx_b = np.cos(theta + np.pi / 2) * b / 2
        dy_b = -np.sin(theta + np.pi / 2) * b / 2
        ax.plot([cx - dx_a, cx + dx_a], [cy - dy_a, cy + dy_a], color="#00e5ff", lw=0.9, alpha=0.85)
        ax.plot([cx - dx_b, cx + dx_b], [cy - dy_b, cy + dy_b], color="#ff3d00", lw=0.9, alpha=0.85)

    _draw_scale_bar(ax, resolution)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    fig.tight_layout(pad=0.2)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_single_class_overlay(
    image_path: str | Path,
    mask_path: str | Path | None,
    df,
    class_col: str,
    class_value: str,
    out_path: str | Path,
    resolution: float | None,
    title: str,
):
    """通用：按 class_col==class_value 高亮，其余淡化。"""
    img = _load_image(image_path)
    h, w = img.shape[0], img.shape[1]
    mask = None
    if mask_path and Path(mask_path).exists():
        mask = _load_mask(mask_path)

    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    # 底图淡化
    ax.imshow(img, alpha=0.55)
    ax.set_axis_off()

    # 高亮该类的颗粒：用 mask 着色
    if mask is not None and class_col in df.columns:
        # df 需含 label 列
        if "label" in df.columns:
            target_labels = set(df.loc[df[class_col] == class_value, "label"].astype(int).tolist())
            if target_labels:
                # 构造彩色叠加：仅目标 label 区域不透明
                overlay = np.zeros((h, w, 4), dtype=float)
                # 简化：对 mask 中属于目标的像素染橙色
                hit = np.isin(mask, list(target_labels))
                overlay[hit, 0] = 1.0
                overlay[hit, 1] = 0.5
                overlay[hit, 3] = 0.55
                ax.imshow(overlay)

    # 同时用中心点标记
    sub = df[df[class_col] == class_value] if class_col in df.columns else df.iloc[0:0]
    if len(sub) > 0 and "centerpoint y" in sub.columns:
        ax.scatter(sub["centerpoint x"], sub["centerpoint y"], s=10, c="#ff3d00", alpha=0.9, linewidths=0)

    _draw_scale_bar(ax, resolution)
    ax.set_title(f"{title}  n={len(sub)}", fontsize=11)
    ax.set_xlim(0, w)
    ax.set_ylim(h, 0)
    fig.tight_layout(pad=0.3)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_shape_gallery(
    image_path: str | Path,
    mask_path: str | Path | None,
    df,
    out_dir: str | Path,
    resolution: float | None,
    stem: str,
):
    """任务3：针片/圆/棱角/普通 各一张（英文标题避 DejaVu 缺中文字形）。"""
    out_dir = Path(out_dir)
    for key, name in [("needle_flaky", "needle_flaky"), ("round", "round"), ("angular", "angular"), ("regular", "regular")]:
        out = out_dir / f"{stem}_shape_{key}.png"
        _plot_single_class_overlay(image_path, mask_path, df, "shape_class", key, out, resolution, f"Shape: {name}")


def plot_anomaly_gallery(
    image_path: str | Path,
    mask_path: str | Path | None,
    df,
    out_dir: str | Path,
    resolution: float | None,
    stem: str,
):
    """任务4：>50 异物 / 泥团 / 噪声 各一张（有则出图，英文标题避字体缺字）。"""
    out_dir = Path(out_dir)
    for key, name in [("oversized", "oversized (>50mm)"), ("suspect_mud", "suspect_mud"), ("undersized", "undersized (<5mm)")]:
        if "anomaly_class" in df.columns and (df["anomaly_class"] == key).any():
            out = out_dir / f"{stem}_anomaly_{key}.png"
            _plot_single_class_overlay(image_path, mask_path, df, "anomaly_class", key, out, resolution, f"Anomaly: {name}")
        elif key == "oversized":
            out = out_dir / f"{stem}_anomaly_{key}.png"
            _plot_single_class_overlay(image_path, mask_path, df, "anomaly_class", key, out, resolution, f"Anomaly: {name} (none)")


def plot_detection_overview(
    image_path: str | Path,
    mask_path: str | Path,
    out_path: str | Path,
):
    """任务1：原图 | mask | 叠加 三联图（英文标题避字体缺字）。"""
    img = _load_image(image_path)
    mask = _load_mask(mask_path)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].imshow(img)
    axes[0].set_title("Original")
    axes[0].set_axis_off()
    axes[1].imshow(mask, cmap="nipy_spectral")
    axes[1].set_title(f"Mask  N={len(np.unique(mask))-1}")
    axes[1].set_axis_off()
    axes[2].imshow(img, alpha=0.6)
    axes[2].imshow(mask, cmap="nipy_spectral", alpha=0.45)
    axes[2].set_title("Overlay")
    axes[2].set_axis_off()
    fig.tight_layout(pad=0.5)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
