"""ImageGrains 输出列名的单一来源。

上游 `grainsizing.py` 写入的列名含空格与单位，极易拼错；
本模块集中定义，避免 `sieve_equivalent` 与 `morphology` 各自重复。
"""

# 轴列（mm / px 两套）
B_AXIS_MM = "ell: b-axis (mm)"
A_AXIS_MM = "ell: a-axis (mm)"
B_AXIS_PX = "ell: b-axis (px)"
A_AXIS_PX = "ell: a-axis (px)"

# 几何列（始终 px 单位，上游不缩放 area）
AREA_PX = "area"
AREA_CONVEX_PX = "area_convex"
PERIMETER_PX = "perimeter_crofton"

# 兼容旧名的别名（新人只需用上面的规范名）
B_AXIS_COL = B_AXIS_MM
A_AXIS_COL = A_AXIS_MM
B_AXIS_PX_COL = B_AXIS_PX
AREA_PX_COL = AREA_PX
SOLIDITY_COL = "solidity"
PERIMETER_COL = PERIMETER_PX
