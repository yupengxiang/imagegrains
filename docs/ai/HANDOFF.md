# 当前交接：agent 文档收束（2026-08-15）

## 任务目标

本仓库是从上游 ImageGrains 2.0 复制而来的新仓库，服务于"混凝土骨料颗粒智能筛分比拼"（自然堆积赛道，见 `docs/task.md`）。仓库带入的 agent 文档全部来自旧的 NeuralLagrangianSolver 仓库（SPH/Hydra/H5/DeepSpeed 训练项目），与当前仓库完全不匹配。本任务把这些文档改写为 ImageGrains 竞赛项目的实际情况。

## 已完成步骤

- 调研仓库实际结构：`src/imagegrains/` 六个模块（`data_loader` / `segmentation_helper` / `grainsizing` / `gsd_uncertainty` / `plotting` / `__main__`）、`notebooks/`、`models/`（预训练权重）、`demo_data/`、`tests/`（仅占位）、pyproject.toml（hatchling，pip 可安装）、CI 跑 pytest。
- 阅读 `docs/task.md`（竞赛任务）与 `docs/insight/`（GPT 数据集/论文建议与技术方案）。
- 确认赛道：自然堆积；技术主线：ImageGrains 2.0 / Cellpose-SAM + 尺度标定 + 筛分等效质量分布。

## 改动文件

- 重写：`AGENTS.md`、`docs/ai/project-overview.md`、`docs/ai/coding-style.md`、`docs/ai/testing.md`、`docs/ai/workflow.md`、`docs/ai/DECISIONS.md`、`docs/ai/PLAN.md`、`docs/ai/HANDOFF.md`（本文件）、`docs/ai/TODO.md`、`docs/data-flow.md`、`docs/architecture.md`。
- 保留不动：`docs/task.md`、`docs/insight/`（gitignored）、`CLAUDE.md`、`Readme.md`、`docs/assets/`。
- 注意：`.gitignore` 已有未提交改动（新增 `docs/insight` 忽略），属用户改动，保留。

## 重要决策

- 文档统一使用中文（与 task.md、既有交接文档一致）。
- 保留 AGENTS.md 的多 agent 工作流骨架（Task Routing / Validation / Handoff / Rules），只替换项目相关内容。
- 竞赛工程能力（标定、筛分等效粒径、形貌/异常、界面）暂未实现，记录在 PLAN/TODO，实施前需用户确认。

## 已运行验证

- 全量阅读仓库结构、全部 agent 文档、`docs/task.md`、`docs/insight/` 两个 GPT 文档、CLI 入口、CI 配置、pyproject.toml。
- 本轮为纯文档改动，按 `docs/ai/testing.md` 纯文档规则未运行 pytest（环境内无可用 python/conda 环境）。

## 已知问题

- 本地尚未配置 `imagegrains` 环境（无 python 命令），`pip install -e .[test]` 与 pytest 未实际运行。
- `tests/test_imagegrains.py` 只有占位用例（`test_something`），后续开发应补真测试。
- 预训练模型在 `models/`（`fh_boosted_1.170223`、`full_set_1.170223`），而 CLI 默认模型路径是 `~/imagegrains/models/`；跑完整流水线前需确认模型路径。

## 下一步建议

1. 用户确认文档收束结果。
2. 按 `docs/ai/PLAN.md` 启动 P0：安装环境并在 `demo_data` 上跑通官方工作流。
3. 制定自采骨料图像 + 筛分实验数据计划（batch 制作、机械筛分对照）。
