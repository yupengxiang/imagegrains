# 当前任务计划

## 当前任务：agent 文档收束（进行中/已完成）

把从旧仓库（NeuralLagrangianSolver）带入的 agent 文档改写为本仓库（ImageGrains 竞赛 fork）的实际情况。

范围：

- 重写 `AGENTS.md`、`docs/ai/*`（8 个文件）、`docs/data-flow.md`、`docs/architecture.md`。
- 保留 `docs/task.md`（竞赛任务原文）与 `docs/insight/`（GPT 研究笔记，gitignored）。
- 保留 `CLAUDE.md`（仅 `@AGENTS.md` 引用）。

成功标准：

- 文档中不再出现旧仓库内容（Hydra、H5、SPH、DeepSpeed、HVI、conda 环境 `neural_lagrangian_solver_torch212` 等）。
- 文档描述的模块、函数、文件、命令与仓库实际一致（`src/imagegrains/`、`demo_data/`、`notebooks/`、`models/`、pytest 等）。

验证：`grep` 检查旧关键词残留；`git diff` 目检。

## 下一步：竞赛工程层 MVP（待用户确认后启动）

参考 `docs/insight/` 中的 GPT 方案，按优先级推进（P0 必须，P1 加分，P2 最后）：

1. P0：跑通官方工作流 —— `pip install -e .[test]` → `demo_data` 上跑 CLI/notebook，确认分割→粒径→GSD 闭环。
2. P0：骨料图像采集与预训练模型评估 —— 拍少量真实骨料，检查分割质量（漏分/粘连/误检），决定是否微调。
3. P0：尺度标定（ArUco 或标尺）→ 像素到 mm 的可靠换算。
4. P0：筛分等效粒径模块 `sieve_equivalent.py`（独立子包）+ 质量加权分布 `wᵢ=dᵢ^γ` + D10/D50/D90。
5. P1：筛分实验数据（≥10–20 个 batch，称重+机械筛分+拍照）校准 θ/γ 参数。
6. P1：形貌分类（先规则：长宽比/圆度/凸度）与异常检测（>50 mm 阈值、泥团分类）。
7. P2：一键式本地应用/报告（Streamlit 或等价物）与自动 QC。
8. P2：模型微调（仅当预训练模型明显不够用时，用 `notebooks/4_train_cellposeSAM_model.ipynb`）。

验收口径（竞赛导向）：D10/D50/D90 与标准筛分结果的误差、主粒径区间累计通过率误差；一切以 `docs/task.md` 与用户确认为准。
