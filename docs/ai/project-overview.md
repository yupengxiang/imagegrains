# 项目总览

这是新进入本仓库的 agent 的项目地图。短期状态见 `PLAN.md`/`HANDOFF.md`。

## 项目身份

- ImageGrains 2.0 竞赛 fork，服务"混凝土骨料颗粒智能筛分比拼"（自然堆积赛道，`docs/task.md`，5–40 mm 破碎骨料）。
- 上游：<https://github.com/dmair1989/imagegrains>，Cellpose-SAM（≥4.0.1）分割 → 几何测量 → D10/D50/D90。
- 主线：上游预训练 `IG2_full_set_cp_SAM` 跑通 `图像→分割→测量→级配`；差异化在把"数量分布"校准为"质量分布"对标筛分。

## 仓库结构

- `src/imagegrains/`：上游包（`__main__`/`segmentation_helper`/`grainsizing`/`gsd_uncertainty`/`data_loader`/`plotting`）。
- `src/aggregate_screening/`：竞赛工程层（已落地，见 `architecture.md`）—— `_columns` 列名单一来源、`sieve_equivalent`（`SieveAnalysis`/`CalibrationResult`）、`morphology`（`MorphThresholds`）、`anomaly`（`MUD_BAND`）、`report`（`SceneSummary`）、`app`。
- `tests/test_sieve_equivalent|morphology|anomaly|report.py`：27 passed（合成数据覆盖）。
- `notebooks/`、`models/`（`IG2_full_set_cp_SAM` 1.2 GB，gitignored）、`demo_data/`。
- `docs/`：`task.md`（赛题）、`USAGE.md`（一键手册）、`architecture.md`/`data-flow.md`、`ai/`（agent 上下文，见 `AGENTS.md`）、`insight/`（gitignored）。

## 竞赛要求

精细识别 / 粒径分析（D10/50/90）/ 形状分类（针片/圆/棱角，可选加分）/ 异常（>50 异物/泥团）；现场采集 ≤30 分钟；以标准筛分（质量分布）为准评分。

## 数据假设

输入：单张/多张自然堆积照；中间产物 `*_mask.tif` / `*_grains.csv`（`ell: b-axis` 列）；尺度经 `--resolution` mm/px 或 `infer_resolution` 自动推断；静态图像，无视频。

## 研发优先级

已落地：官方工作流闭环 + 竞赛工程层 MVP + 代码优雅重构（dataclass、单一流水线）+ 使用手册。下一步依赖真实数据：采批料筛分实验校准 θ/γ、评估真实分割质量、ArUco 标定、泥团分类器（见 `PLAN.md`）。

## 非目标

不做传送带跟踪、不重训基础模型、不做含泥量回归；不维护 CT 等通用能力。
