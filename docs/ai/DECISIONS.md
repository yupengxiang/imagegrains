# 架构决策

本文件记录已反映在代码/文档中的稳定决策，未来 agent 应保持，除非任务明确要求重审。

## 仓库定位：竞赛 fork

本仓库是 ImageGrains 2.0 分支，服务"混凝土骨料颗粒智能筛分比拼"（自然堆积赛道）。上游保持原样，竞赛能力增量开发。

影响：不改 `src/imagegrains/` 公开签名/CLI/输出格式；新能力放独立子包；不设计传送带。

## 评分基准：质量加权优先

以标准筛分（质量分布）为准，视觉几何需经 `d=θ₁b+θ₂d_eq+θ₃` + `w=d^γ` 转为质量加权 D10/50/90 与级配；数量口径仅作对照。`_columns.py` 为列名单一来源。

## 数据与文件契约

沿用上游约定（`coding-style.md`/`data-flow.md`）：图像-mask 同名 `_mask.tif`；逐颗粒 `*_grains.csv`（`ell: b-axis` 列）；GSD `*_gsd.csv`；尺度经 `--resolution` 或 `infer_resolution`。擅自改名会破坏读取路径。

## 依赖边界

cellpose ≥4.0.1 + PyTorch 为重型计算；`pip install -e .[test]` 为标准安装；scipy 用于校准。不引新重型依赖。

## 已落地（原未决，现决策）

- 筛分等效粒径 `SieveAnalysis`（`d=θ₁b+θ₂d_eq+θ₃`，默认 b 轴）与 `w=d^γ`（γ=3）及 `CalibrationResult`（差分进化）—— 已实现，参数以自采筛分数据校准为准；
- 形貌 `MorphThresholds` 规则法与异常 `MUD_BAND/FOREIGN_MIN` — 已实现，阈值需真实数据重标定；
- 报告 `SceneSummary`/`NormalOnly` 与一键 CLI `python -m aggregate_screening` — 已实现，`scene_summary` 返回 `(summary,df_final)` 单一流水线。

## Code Reorg 2026-08（9435f9b）

- 列常量集中 `_columns.py`；`load_grains_csv`/`infer_resolution`/`normalize_grains` 显式化，删 `df.attrs` 隐式通道；
- `SieveAnalysis`/`SceneSummary` dataclass 替代裸 dict，`size_fractions` 返回 `dict`；
- 显式优先级 `angular>round>needle`，`anomaly` 统一命名与长度校验；`app` 懒加载绘图、去 CSV 回读、库函数抛 `ValueError`。

## 未决

- ArUco/标尺标定 + homography 透视校正；
- 泥团颜色/纹理分类器；
- 一键图形界面（Streamlit 等）。
