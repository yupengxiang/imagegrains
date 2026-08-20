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


def test_sieve_diameter_raises_when_deq_missing_and_theta2_nonzero():
    b = np.array([10.0])
    deq = np.array([np.nan])
    try:
        se.sieve_diameter(b, deq, theta=(0.5, 0.5, 0.0))
        assert False, "应抛 ValueError"
    except ValueError:
        pass


def test_mass_weight_cubic():
    np.testing.assert_allclose(se.mass_weight([2.0, 3.0], gamma=3.0), [8.0, 27.0])


def test_weighted_percentiles_analytic():
    d = np.array([5.0, 10.0, 20.0])
    w = np.array([125.0, 1000.0, 8000.0])
    p = se.weighted_percentiles(d, w, percs=(10, 50, 90))
    assert len(p) == 3
    assert np.isclose(se.weighted_percentiles(d, w, percs=(50,))[0], 20.0)


def test_weighted_percentiles_empty():
    assert np.all(np.isnan(se.weighted_percentiles([], [], percs=(10, 50, 90))))


def test_size_fractions():
    d = np.array([4.0, 7.0, 12.0, 45.0])
    w = np.ones_like(d)
    fracs = se.size_fractions(d, w)
    assert isinstance(fracs, dict)
    assert np.isclose(fracs["5-10"], 25.0)
    assert np.isclose(fracs["10-16"], 25.0)
    assert np.isclose(fracs["<5"], 25.0)
    assert np.isclose(fracs[">40"], 25.0)
    assert np.isclose(sum(fracs.values()), 100.0)


def test_weighted_analysis_end_to_end():
    ana = se.weighted_analysis([10.0, 20.0, 30.0], [np.pi * 6**2] * 3, 0.39)
    assert isinstance(ana, se.SieveAnalysis)
    assert ana.D50 > ana.D10
    assert np.isclose(sum(ana.fractions.values()), 100.0)
    assert ana.d_sieve.shape == (3,)


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
    assert isinstance(res, se.CalibrationResult)
    assert res.success
    assert abs(res.gamma - true_gamma) < 0.3
    assert abs(res.theta[0] - true_theta[0]) < 0.2


def test_normalize_grains_and_infer_resolution(tmp_path):
    # mm 列 -> 直接取
    df_mm = pd.DataFrame({"ell: b-axis (mm)": [10.0], "ell: a-axis (mm)": [15.0], "area": [100.0], "area_convex": [120.0], "perimeter_crofton": [40.0]})
    out = se.normalize_grains(df_mm, resolution=None)
    assert "b_mm" in out.columns and out["b_mm"][0] == 10.0

    # px 列 -> 需 resolution
    df_px = pd.DataFrame({"ell: b-axis (px)": [10.0], "ell: a-axis (px)": [15.0], "area": [100.0], "area_convex": [120.0], "perimeter_crofton": [40.0]})
    out2 = se.normalize_grains(df_px, resolution=0.5)
    np.testing.assert_allclose(out2["b_mm"], [5.0])

    # 同时含 mm/px -> 自动推断
    df_both = pd.DataFrame({"ell: b-axis (mm)": [10.0, 20.0], "ell: b-axis (px)": [20.0, 40.0], "ell: a-axis (mm)": [15.0, 25.0], "ell: a-axis (px)": [30.0, 50.0], "area": [100.0, 200.0], "area_convex": [120.0, 240.0], "perimeter_crofton": [40.0, 50.0]})
    assert np.isclose(se.infer_resolution(df_both), 0.5)
