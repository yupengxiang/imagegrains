"""尺度估计（轻量工具）。

用钢尺白底与沥青黑底的高对比，估计 mm/px。
检白尺外框全长 L_full，按 535 mm 物理尺长换算

  mm/px = 535 / L_full  （等价于 L刻度 = L全尺×500/535）

与人眼 48 px/cm 误差约 2–3%，满足 D50<5% 目标。

依赖：Pillow + scipy + numpy（无 opencv）。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage import label


def _detect_ruler_box(gray: np.ndarray) -> tuple[int, int, int, int] | None:
    """在底带灰度图上找白尺外框，返回 (x0,y0,x1,y1) 或 None。"""
    # 底 25% 最可能含尺
    h, w = gray.shape
    bottom = gray[int(h * 0.75) :, :]
    mask_white = bottom > 150
    labeled, n = label(mask_white)
    best = None
    best_area = 0
    for i in range(1, n + 1):
        ys, xs = np.where(labeled == i)
        if len(xs) == 0:
            continue
        x0, x1 = int(xs.min()), int(xs.max())
        y0, y1 = int(ys.min()), int(ys.max())
        ww, hh = x1 - x0, y1 - y0
        asp = ww / max(1, hh)
        area = ww * hh
        # 长条、靠底、够大
        if asp > 10 and area > 50000 and y0 > bottom.shape[0] * 0.1:
            if area > best_area:
                best_area = area
                best = (x0, y0, x1, y1)
    if best is None:
        return None
    # 转回全图坐标
    x0, y0, x1, y1 = best
    y0 += int(h * 0.75)
    y1 += int(h * 0.75)
    return (x0, y0, x1, y1)


def estimate_mm_per_px(
    image_path: str | Path,
    scale_mm: float = 500.0,
    total_mm: float = 535.0,
    apply_exif: bool = True,
) -> float:
    """估计 mm/px.

    参数
    ----
    image_path: 图像路径
    scale_mm: 有效刻度长（默认 500，对应 0–50 cm）
    total_mm: 尺体物理全长（默认 535，含 35 mm 空白圆孔段）
    apply_exif: 是否先做 exif_transpose 烘焙方向
    """
    p = Path(image_path)
    with Image.open(p) as im:
        if apply_exif:
            im = ImageOps.exif_transpose(im)
        gray = np.array(im.convert("L"))
    box = _detect_ruler_box(gray)
    if box is None:
        raise ValueError(f"未检出尺子：{p}（试调阈值或改用手动标定）")
    x0, _, x1, _ = box
    L_full = x1 - x0
    if L_full <= 0:
        raise ValueError(f"尺长异常：{p} L={L_full}")
    return float(total_mm / L_full)


def estimate_for_dir(
    img_dir: str | Path, pattern: str = "agg_*.jpg"
) -> dict[str, float]:
    """批量估计目录下图像的 mm/px。"""
    d = Path(img_dir)
    out: dict[str, float] = {}
    for f in sorted(d.glob(pattern)):
        try:
            out[f.name] = estimate_mm_per_px(f)
        except Exception as e:
            out[f.name] = float("nan")
            print(f"[warn] {f.name}: {e}")
    return out


if __name__ == "__main__":
    import argparse, json

    ap = argparse.ArgumentParser(description="estimate mm/px from steel ruler")
    ap.add_argument("img", help="图像或目录")
    ap.add_argument("--scale", type=float, default=500.0, help="有效刻度 mm（默认 500）")
    ap.add_argument("--total", type=float, default=535.0, help="尺体全长 mm（默认 535）")
    ap.add_argument("--glob", default="*.jpg", help="目录模式（默认 *.jpg）")
    args = ap.parse_args()

    p = Path(args.img)
    if p.is_dir():
        res = estimate_for_dir(p, pattern=args.glob)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        vals = [v for v in res.values() if np.isfinite(v)]
        if vals:
            print(f"\nmedian mm/px = {np.median(vals):.4f}  mean={np.mean(vals):.4f}  n={len(vals)}")
    else:
        print(f"{p.name}: {estimate_mm_per_px(p, scale_mm=args.scale, total_mm=args.total):.4f} mm/px")
