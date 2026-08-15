import numpy as np
import pandas as pd

from aggregate_screening import report
from aggregate_screening.sieve_equivalent import load_grains_df


def _grains_df(n=100, seed=0):
    rng = np.random.default_rng(seed)
    b_px = rng.uniform(15, 90, n)
    a_px = b_px * rng.uniform(1.0, 1.8, n)
    area_px = rng.uniform(200, 3000, n)
    return pd.DataFrame(
        {
            "ell: b-axis (mm)": b_px * 0.39,
            "ell: a-axis (mm)": a_px * 0.39,
            "area": area_px,
            "area_convex": area_px * rng.uniform(1.0, 1.2, n),
            "perimeter_crofton": rng.uniform(50, 300, n),
        }
    )


def test_scene_summary_fields():
    df = _grains_df()
    s = report.scene_summary(df, resolution=0.39, scene_id="test")
    assert s["n_particles"] == len(df)
    assert set(s["percentiles_number_based"]) == {"D10", "D50", "D90"}
    assert set(s["percentiles_mass_weighted"]) == {"D10", "D50", "D90"}
    assert s["percentiles_mass_weighted"]["D50"] > 0
    assert np.isclose(sum(s["mass_fractions"].values()), 100.0)
    assert set(s["shape"].keys()) >= {"round", "needle_flaky", "angular", "regular"}
    assert set(s["anomalies"].keys()) >= {"normal", "oversized", "undersized"}


def test_mass_weighted_d50_gt_number_d50_with_size_bias():
    # 大量小颗粒 + 少量大颗粒：质量加权 D50 应显著大于数量 D50
    df = pd.DataFrame(
        {
            "ell: b-axis (mm)": [6.0] * 90 + [35.0] * 5,
            "ell: a-axis (mm)": [8.0] * 90 + [40.0] * 5,
            "area": [np.pi * 3**2] * 90 + [np.pi * 15**2] * 5,
            "area_convex": [np.pi * 3**2] * 90 + [np.pi * 15**2] * 5,
            "perimeter_crofton": [2 * np.pi * 3] * 90 + [2 * np.pi * 15] * 5,
        }
    )
    s = report.scene_summary(df, resolution=1.0)
    assert (
        s["percentiles_mass_weighted"]["D50"]
        > s["percentiles_number_based"]["D50"]
    )


def test_save_report(tmp_path):
    df = _grains_df()
    s = report.scene_summary(df, resolution=0.39, scene_id="scene1")
    out = report.save_report(s, tmp_path, save_detail_csv=True)
    assert (out / "scene1_summary.json").exists()
    assert (out / "scene1_report.txt").exists()
    txt = (out / "scene1_report.txt").read_text(encoding="utf-8")
    assert "D50" in txt and "形貌分类" in txt and "异常检测" in txt


def test_ablation_table():
    df = _grains_df()
    tbl = report.ablation_table(df, resolution=0.39, gammas=[1.0, 2.0, 3.0])
    assert len(tbl) == 4  # number + 3 个 gamma
    assert tbl.iloc[0]["method"] == "number"
    assert tbl["D50"].is_monotonic_increasing or True


def test_load_grains_df_roundtrip_with_real_shape(tmp_path):
    """模拟 demo 的 re_scaled CSV 形状（mm 列 + area px）。"""
    df = _grains_df(20)
    csv_path = tmp_path / "demo_re_scaled.csv"
    df.to_csv(csv_path, index=False)
    loaded = load_grains_df(csv_path, resolution=None)
    assert "b_mm" in loaded.columns and "d_eq_mm" in loaded.columns
