import numpy as np
import pandas as pd

from aggregate_screening import morphology as mo


def _circle(radius):
    """圆形：周长=2πr，面积=πr²，凸包面积=面积。"""
    a = np.pi * radius**2
    p = 2 * np.pi * radius
    return a, p


def test_aspect_ratio():
    assert np.isclose(mo.aspect_ratio(2.0, 4.0), 0.5)
    assert np.isclose(mo.aspect_ratio(4.0, 4.0), 1.0)


def test_circularity_circle_is_one():
    a, p = _circle(5.0)
    assert np.isclose(mo.circularity(a, p), 1.0, atol=1e-9)


def test_classify_round():
    # 近似圆：AR~1, circularity~1, solidity~1
    cls = mo.classify_shape(10.0, 10.5, np.pi * 5**2, np.pi * 5**2, 2 * np.pi * 5)
    assert cls == "round"


def test_classify_needle_flaky():
    # 细长条：AR 很小
    a, p = _circle(3.0)
    cls = mo.classify_shape(2.0, 12.0, a, a, p)
    assert cls == "needle_flaky"


def test_classify_angular():
    # 星形/凹轮廓：solidity 低、circularity 低
    cls = mo.classify_shape(10.0, 12.0, 100.0, 200.0, 60.0)
    assert cls == "angular"


def test_classify_dataset_and_summary():
    df = pd.DataFrame(
        {
            "ell: b-axis (mm)": [10.0, 2.0, 11.0],
            "ell: a-axis (mm)": [10.5, 12.0, 13.0],
            "area": [np.pi * 5**2, np.pi * 3**2, 100.0],
            "area_convex": [np.pi * 5**2, np.pi * 3**2, 200.0],
            "perimeter_crofton": [2 * np.pi * 5, 2 * np.pi * 3, 60.0],
        }
    )
    out = mo.classify_dataset(df)
    assert list(out["shape_class"]) == ["round", "needle_flaky", "angular"]
    summ = mo.shape_summary(out)
    assert summ["round"]["count"] == 1
    assert np.isclose(summ["round"]["fraction"], 100.0 / 3)
