"""场景级汇总与报告。

把单场景的颗粒表汇总为数量/质量对照、粒级占比、形貌与异常统计，
并提供文本/JSON/对比表输出。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

import numpy as np
import pandas as pd

from ._columns import B_AXIS_MM  # noqa: F401 仅为文档引用
from .sieve_equivalent import (
    DEFAULT_GAMMA,
    DEFAULT_THETA,
    SIEVES,
    SieveAnalysis,
    infer_resolution,
    load_grains_csv,
    normalize_grains,
    weighted_analysis,
    weighted_percentiles,
)
from . import morphology, anomaly


# ---------------------------------------------------------------------------
# 结构化汇总
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class NormalOnly:
    n_particles: int
    percentiles_mass_weighted: dict[str, float]
    mass_fractions: dict[str, float]


@dataclass(frozen=True)
class SceneSummary:
    scene_id: str
    n_particles: int
    resolution_mm_per_px: float | None
    theta: tuple[float, float, float]
    gamma: float
    exclude_anomalies: bool
    percentiles_number_based: dict[str, float]
    percentiles_mass_weighted: dict[str, float]
    mass_fractions: dict[str, float]
    normal_only: NormalOnly | None
    shape: dict[str, dict[str, float]]
    anomalies: dict[str, dict[str, float]]

    def to_dict(self) -> dict:
        d = asdict(self)
        # NormalOnly 已在 asdict 中展开为 dict，无需额外处理
        return d

    # 兼容旧 dict 下标访问 s["n_particles"]
    def __getitem__(self, key: str):
        return getattr(self, key) if hasattr(self, key) else self.to_dict()[key]

    def get(self, key: str, default=None):
        return self.to_dict().get(key, default)


def _percentiles_dict(arr: np.ndarray) -> dict[str, float]:
    return {"D10": float(arr[0]), "D50": float(arr[1]), "D90": float(arr[2])}


def _ana_to_percentiles(ana: SieveAnalysis) -> dict[str, float]:
    return {"D10": ana.D10, "D50": ana.D50, "D90": ana.D90}


# ---------------------------------------------------------------------------
# 核心汇总
# ---------------------------------------------------------------------------
def scene_summary(
    df: pd.DataFrame | str | Path,
    resolution: float | None,
    theta: tuple[float, float, float] = DEFAULT_THETA,
    gamma: float = DEFAULT_GAMMA,
    sieves: list[float] = SIEVES,
    scene_id: str = "",
    exclude_anomalies: bool = True,
) -> tuple[SceneSummary, pd.DataFrame]:
    """从 grains 表计算场景汇总，返回 ``(summary, df_final)``。

    ``df`` 可为已加载的 DataFrame 或 CSV 路径；``resolution`` 为 mm/px，
    ``None`` 时若同时有 mm/px 列则自动推断。
    ``df_final`` 为已加 ``shape_* / anomaly_*`` 的明细表，供 ``save_report`` 直接复用，
    避免在 ``app`` 中重复分类流水线。
    """
    # 1) 标准化
    if isinstance(df, (str, Path)):
        df_norm = load_grains_csv(df, resolution=resolution)
        # load 内部已推断，取其分辨率
        resolution = infer_resolution(df_norm) if resolution is None else resolution
        # 若 load 后仍无分辨率，从列中再取
        if resolution is None and "__resolution_mm_per_px" in df_norm.columns:
            resolution = df_norm["__resolution_mm_per_px"].iloc[0]
            if pd.isna(resolution):
                resolution = None
    else:
        df_norm = normalize_grains(df, resolution=resolution)
        # 规范化后的分辨率
        if "__resolution_mm_per_px" in df_norm.columns:
            val = df_norm["__resolution_mm_per_px"].iloc[0]
            resolution = None if pd.isna(val) else float(val)

    b_mm = df_norm["b_mm"].to_numpy(dtype=float)
    area_px = df_norm["area_px"].to_numpy(dtype=float)

    # 2) 数量 vs 质量
    d_num = weighted_percentiles(b_mm, np.ones_like(b_mm), percs=(10, 50, 90))
    ana_all = weighted_analysis(b_mm, area_px, resolution, theta=theta, gamma=gamma, sieves=sieves)

    # 3) 形貌与异常（单一流水线）
    df_shape = morphology.classify_dataset(df_norm)
    df_final = anomaly.classify_anomalies(df_shape, ana_all.d_sieve)
    shape_sum = morphology.shape_summary(df_final)
    anom_sum = anomaly.anomaly_summary(df_final)

    # 4) 剔除异常后的正常骨料统计
    normal_only: NormalOnly | None = None
    if exclude_anomalies:
        mask_normal = df_final["anomaly_class"].to_numpy() == "normal"
        if np.any(mask_normal):
            ana_norm = weighted_analysis(
                b_mm[mask_normal], area_px[mask_normal], resolution, theta=theta, gamma=gamma, sieves=sieves
            )
            normal_only = NormalOnly(
                n_particles=int(mask_normal.sum()),
                percentiles_mass_weighted=_ana_to_percentiles(ana_norm),
                mass_fractions=dict(ana_norm.fractions),
            )

    summary = SceneSummary(
        scene_id=scene_id,
        n_particles=int(len(df_norm)),
        resolution_mm_per_px=resolution,
        theta=tuple(theta),
        gamma=float(gamma),
        exclude_anomalies=exclude_anomalies,
        percentiles_number_based=_percentiles_dict(d_num),
        percentiles_mass_weighted=_ana_to_percentiles(ana_all),
        mass_fractions=dict(ana_all.fractions),
        normal_only=normal_only,
        shape=shape_sum,
        anomalies=anom_sum,
    )
    return summary, df_final


# ---------------------------------------------------------------------------
# 报告输出
# ---------------------------------------------------------------------------
def save_report(
    summary: SceneSummary | dict,
    out_dir: str | Path,
    df_final: pd.DataFrame | None = None,
) -> Path:
    """保存 ``summary.json``、明细 CSV 与文本报告。"""
    if isinstance(summary, dict):
        # 兼容旧 dict 调用
        scene_id = summary.get("scene_id") or "scene"
        data = summary
    else:
        scene_id = summary.scene_id or "scene"
        data = summary.to_dict()

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / f"{scene_id}_summary.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if df_final is not None:
        df_final.to_csv(out_dir / f"{scene_id}_particles_annotated.csv", index=False)

    txt = format_report_text(summary)
    (out_dir / f"{scene_id}_report.txt").write_text(txt, encoding="utf-8")
    return out_dir


def format_report_text(summary: SceneSummary | dict) -> str:
    """格式化为易读文本。"""
    if isinstance(summary, dict):
        # 兼容旧 dict
        num = summary["percentiles_number_based"]
        mass = summary["percentiles_mass_weighted"]
        n = summary["n_particles"]
        scene_id = summary.get("scene_id", "")
        res = summary.get("resolution_mm_per_px")
        normal = summary.get("normal_only")
        shape = summary["shape"]
        anomalies = summary["anomalies"]
        fracs = (normal["mass_fractions"] if normal else summary["mass_fractions"])
    else:
        num = summary.percentiles_number_based
        mass = summary.percentiles_mass_weighted
        n = summary.n_particles
        scene_id = summary.scene_id
        res = summary.resolution_mm_per_px
        normal = summary.normal_only
        shape = summary.shape
        anomalies = summary.anomalies
        fracs = normal.mass_fractions if normal else summary.mass_fractions
        # normal 是 dataclass，需转 dict 访问
        if normal is not None:
            # fracs 已是 dict
            pass

    lines = [
        f"场景: {scene_id}",
        f"颗粒数: {n}  分辨率: {res} mm/px",
        "",
        f"D10 数量={num['D10']:.1f}mm / 质量加权={mass['D10']:.1f}mm",
        f"D50 数量={num['D50']:.1f}mm / 质量加权={mass['D50']:.1f}mm",
        f"D90 数量={num['D90']:.1f}mm / 质量加权={mass['D90']:.1f}mm",
    ]
    if normal:
        if isinstance(normal, dict):
            nm_n = normal["n_particles"]
            nm_p = normal["percentiles_mass_weighted"]
        else:
            nm_n = normal.n_particles
            nm_p = normal.percentiles_mass_weighted
        lines += [
            "",
            f"剔除异常后（正常骨料 {nm_n} 颗）:",
            f"  D10={nm_p['D10']:.1f}mm  D50={nm_p['D50']:.1f}mm  D90={nm_p['D90']:.1f}mm",
        ]
    lines += ["", "粒级质量占比 (%):"]
    for k, v in fracs.items():
        lines.append(f"  {k:>10}: {v:5.1f}")
    lines.append("")
    lines.append("形貌分类:")
    for k, v in shape.items():
        lines.append(f"  {morphology.SHAPE_LABELS[k]}: {v['count']} 颗 ({v['fraction']:.1f}%)")
    lines.append("")
    lines.append("异常检测:")
    for k, v in anomalies.items():
        lines.append(f"  {anomaly.LABELS[k]}: {v['count']} 颗 ({v['fraction']:.1f}%)")
    return "\n".join(lines)


def ablation_table(
    df: pd.DataFrame | str | Path,
    resolution: float | None,
    thetas: list[tuple[float, float, float]] | None = None,
    gammas: list[float] | None = None,
) -> pd.DataFrame:
    """消融对照：number 基线 + 若干 (theta,gamma) 组合的 D50。"""
    if isinstance(df, (str, Path)):
        df_norm = load_grains_csv(df, resolution=resolution)
        if "__resolution_mm_per_px" in df_norm.columns:
            val = df_norm["__resolution_mm_per_px"].iloc[0]
            resolution = None if pd.isna(val) else float(val)
    else:
        df_norm = normalize_grains(df, resolution=resolution)
        if "__resolution_mm_per_px" in df_norm.columns:
            val = df_norm["__resolution_mm_per_px"].iloc[0]
            resolution = None if pd.isna(val) else float(val)

    b_mm = df_norm["b_mm"].to_numpy(dtype=float)
    area_px = df_norm["area_px"].to_numpy(dtype=float)

    rows: list[dict] = []
    d_num = weighted_percentiles(b_mm, np.ones_like(b_mm), percs=(50,))
    rows.append({"method": "number", "theta": None, "gamma": None, "D50": float(d_num[0])})

    candidates: list[tuple[tuple[float, float, float], float]] = []
    if gammas:
        for g in gammas:
            candidates.append((DEFAULT_THETA, float(g)))
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
                "D50": float(ana.D50),
            }
        )
    return pd.DataFrame(rows)
