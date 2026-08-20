# 编码风格与接口约束

本文件记录本仓库的代码风格规则。优先遵循正在编辑的文件中已有的风格，改动保持外科手术式的最小范围。

## 通用原则

- 以最小改动解决被请求的问题。
- 除非任务明确要求行为变化，否则保留现有行为。
- 不做机会主义重构、大规模格式化、import 排序或命名清理。
- 匹配局部约定，即使相邻文件并不完全一致。
- 注释只用于解释非显而易见的控制流、兼容性约束或研究假设。
- 不引入新的重型依赖，除非明确确认（GPU 推理、Cellpose 已是最重依赖）。

## Python 风格

- 采用普通 Python 模块和显式 import，`src/imagegrains/` 内模块通过 `from imagegrains import ...` 互相引用。
- 现有代码以模块级函数为主（如 `segmentation_helper.py`、`grainsizing.py`），新代码先写函数；只有状态聚合明显时才引入类。
- 现有代码用 `print('>> ...')` 输出进度，`mute=True` 参数控制静默。新代码沿用该约定，不要引入自定义 logging 体系（除非任务明确要求）。
- 鼓励在**新函数签名**上写类型注解和返回注解，但不要为了加类型而重写现有模块。
- 关键行为参数通过 keyword 参数传递（如 `filters=None, mute=False, tar_dir='', ...`），保持与现有调用点一致。

## 数据与文件约定

这些是上游硬编码约定，保持一致，不要擅自改名：

- 图像与 mask 同名配对：`_mask.tif`（`data_loader.find_data`）。
- 逐颗粒 CSV：`*_grains.csv`；粒径列 `ell: b-axis (px/mm)` 定义见 `src/aggregate_screening/_columns.py`（单一来源），旧代码由 `read_grains` 读取。
- GSD：`*_gsd.csv`；不确定度：`*_perc_uncert.txt`。
- `filters = {'edge': [bool,val], 'px_cutoff': [bool,val]}`。
- 输出目录：`tar_dir=''` 表与输入同目录。
- 尺度：`--resolution` mm/px 或 CSV；竞赛层 `infer_resolution`/`normalize_grains` 显式化（`load_grains_df` 为兼容旧名）。
- 不改动 `demo_data/`/`models/` 权重与演示数据。

## CLI 约定

- 入口是 `python -m imagegrains`（`src/imagegrains/__main__.py`，argparse）。
- 五步流水线：分割（`--skip_segmentation` 跳过）→ 重采样（`--grid_resample`/`--random_resample`/`--centerpoint_resample`）→ 粒径测量（`--skip_grainsize` 跳过）→ 尺度（`--resolution`）→ GSD 与不确定度（`--unc_method`/`--n`/`--scale_err`/`--length_err`）。
- 新增 CLI 参数应加进现有 `add_argument_group`，不要改变既有参数名和默认值语义。
- 不改动 `src/imagegrains/` 公开函数签名与输出列名；兼容性影响必须说明。

## 模块职责

- `segmentation_helper.py`：Cellpose 相关（预测、模型加载、训练、评估、两尺度合并）。
- `grainsizing.py`：mask → 几何属性与长短轴（`ell_stats`/`fit_grain_axes`）、过滤、重采样、尺度、GSD。
- `gsd_uncertainty.py`：bootstrap / Monte Carlo 不确定度。
- `data_loader.py`：数据/模型下载与文件系统读写。
- `plotting.py`：绘图，禁止在其中写业务逻辑。
- 新增比赛工程能力（ArUco 标定、筛分等效粒径、形貌/异常分类、报告等）应放在独立模块或子包中，优先复用上述模块的函数，避免把逻辑塞进已有模块。

## 测试风格

- 遵循 `docs/ai/testing.md`，运行最小的相关验证。
- 新增测试用 pytest，放在 `tests/`；现有 `tests/test_imagegrains.py` 只有占位用例。
- 测试不要依赖真实模型权重或 Cellpose 推理，除非是显式的 smoke 测试并跳过默认收集。
- 纯文档改动不需要跑测试；检查渲染文本或文件内容即可。

## 文件与产物纪律

- 不编辑生成文件、缓存、模型权重、demo 数据或大型二进制文件，除非明确要求。
- 保留工作树中与任务无关的脏改动；不要回退或重排你没有为任务触碰的文件。
- 工作量大、未完成或要交接给其他 agent 时，保持 `docs/ai/PLAN.md` 与 `docs/ai/HANDOFF.md` 与实际状态一致。
