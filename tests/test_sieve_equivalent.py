import numpy as np
import pandas as pd

from aggregate_screening import sieve_equivalent as se


def test_equivalent_diameter():
    r = np.sqrt(100.0 / np.pi)
    d = se.equivalent_diameter([np.pi * r**2], 1.0)
    assert np.isclose(d[0], 2 * r)


def test_sieve_diameter_default_is_b_axis():
    b = np.array([10.0, 20.0])
    deq = np.array([15.0, 30.0])
    np.testing.assert_allclose(se.sieve_diameter(b, deq), b)


def test_mass_weight_cubic():
    np.testing.assert_allclose(se.mass_weight([2.0, 3.0], gamma=3.0), [8.0, 27.0])


def test_weighted_percentiles_analytic():
    # 三颗：5mm(w=125), 10mm(w=1000), 20mm(w=8000)
    d = np.array([5.0, 10.0, 20.0])
    w = np.array([125.0, 1000.0, 8000.0])
    cdf = np.cumsum(w) / w.sum()
    assert np.isclose(cdf[-1], 1.0)
    p = se.weighted_percentiles(d, w, percs=(10, 50, 90))
    assert len(p) == 3
    assert np.isclose(se.weighted_percentiles(d, w, percs=(50,))[0], 20.0)


def test_weighted_percentiles_empty():
    assert np.all(np.isnan(se.weighted_percentiles([], [], percs=(10, 50, 90))))


def test_size_fractions():
    d = np.array([4.0, 7.0, 12.0, 45.0])
    w = np.ones_like(d)
    fracs = se.size_fractions(d, w)
    assert np.isclose(fracs["5-10"], 25.0)
    assert np.isclose(fracs["10-16"], 25.0)
    assert np.isclose(fracs["<5"], 25.0)
    assert np.isclose(fracs[">40"], 25.0)
    assert np.isclose(fracs.sum(), 100.0)


def test_weighted_analysis_end_to_end():
    df = pd.DataFrame(
        {
            "ell: b-axis (mm)": [10.0, 20.0, 30.0],
            "ell: a-axis (mm)": [15.0, 25.0, 35.0],
            "area": [np.pi * 6**2] * 3,
            "area_convex": [np.pi * 6**2] * 3,
            "perimeter_crofton": [2 * np.pi * 6] * 3,
        }
    )
    ana = se.weighted_analysis(df["ell: b-axis (mm)"], df["area"], 0.39)
    assert ana["D50"] > ana["D10"]
    assert np.isclose(ana["fractions"].sum(), 100.0)
    assert ana["d_sieve"].shape == (3,)


def test_fit_calibration_recovers_params():
    rng = np.random.default_rng(42)
    true_theta = (0.6, 0.4, 1.0)
    true_gamma = 2.5
    batches, targets = [], []
    for _ in range(6):
        n = 80
        b = rng.uniform(6, 35, n)
        area = rng.uniform(500, 4000, n)
        deq = se.equivalent_diameter(area, 0.39)
        d = se.sieve_diameter(b, deq, theta=true_theta)
        w = se.mass_weight(d, true_gamma)
        batches.append({"b_mm": b, "area_px": area, "resolution": 0.39})
        targets.append(tuple(se.weighted_percentiles(d, w, percs=(10, 50, 90))))
    res = se.fit_calibration(batches, targets)
    assert res["success"]
    assert abs(res["gamma"] - true_gamma) < 0.3
    assert abs(res["theta"][0] - true_theta[0]) < 0.2
    assert abs(res["theta"][1] - true_theta[1]) < 0.2


def test_load_grains_df_mm_and_px(tmp_path):
    mm_csv = tmp_path / "mm.csv"
    pd.DataFrame(
        {
            "ell: b-axis (mm)": [10.0, 20.0],
            "ell: a-axis (mm)": [15.0, 25.0],
            "area": [100.0, 200.0],
        }
    ).to_csv(mm_csv, index=False)
    df = se.load_grains_df(mm_csv, resolution=None)
    assert "b_mm" in df.columns

    px_csv = tmp_path / "px.csv"
    pd.DataFrame(
        {
            "ell: b-axis (px)": [10.0, 20.0],
            "ell: a-axis (px)": [15.0, 25.0],
            "area": [100.0, 200.0],
        }
    ).to_csv(px_csv, index=False)
    df2 = se.load_grains_df(px_csv, resolution=0.5)
    np.testing.assert_allclose(df2["b_mm"], [5.0, 10.0])
