# 当前交接：竞赛工程层 MVP 完成（2026-08-16）

## 任务目标

在自然堆积赛道（`docs/task.md`）上基于 ImageGrains 2.0 构建骨料智能筛分系统。本轮在跑通官方工作流后，用 demo 数据完成了竞赛工程层第一版。

## 已完成步骤

- 环境：conda `imagegrains`（py3.10）+ `pip install -e '.[test]'`；GPU RTX 4080 SUPER 可用；模型 `~/imagegrains/models/IG2_full_set_cp_SAM`（Zenodo 重新下载的完整版 1.2GB）。
- 官方工作流全闭环：分割(2.8s/张) → 粒径 → mm 尺度(0.39) → GSD+bootstrap，demo 57 颗粒。
- 新建 `src/aggregate_screening/` 子包（竞赛工程层，不修改上游源码）：
  - `sieve_equivalent.py`：等效粒径 d=θ₁b+θ₂d_eq+θ₃、质量加权 w=d^γ、质量加权 D10/D50/D90（阶梯逆 CDF）、粒级质量占比、`fit_calibration`（differential_evolution，合成数据可恢复真参数）、`load_grains_df`（mm/px 双列自动推断分辨率）。
  - `morphology.py`：形貌分类规则法（针片状候选/圆形/棱角状/普通），阈值可配置。
  - `anomaly.py`：>50mm 异物、<5mm 噪声、疑似泥团兜底规则（可关闭）。
  - `report.py`：场景汇总（数量 vs 质量加权对照、剔除异常后正常骨料口径、消融表）、txt/json 报告。
  - `app.py` + `__main__.py`：一键 CLI。
- demo 演示结果（`4_P1060348_3`，57 颗）：数量 D50=9.2 → 质量加权(全颗粒) D50=67.1（被 67mm 异物主导，正确行为）→ **剔除异常后 D50=18.8 / D90=28.1**；粒级占比全部落在 5-31.5mm。
- 测试：26 passed（含拟合恢复参数、形貌/异常边界、报告完整性）。

## 改动文件

- 新增：`src/aggregate_screening/`（6 个 .py）、`tests/test_sieve_equivalent.py`、`tests/test_morphology.py`、`tests/test_anomaly.py`、`tests/test_report.py`。
- 更新：`docs/architecture.md`、`docs/data-flow.md`（竞赛工程层一节）、`docs/ai/PLAN.md`、`docs/ai/HANDOFF.md`（本文件）、`docs/ai/TODO.md`。
- 未提交；另有 `opencode.json`（项目权限配置，edit=allow）。

## 重要决策

- 报告默认口径：剔除异常物后统计正常骨料（异物不参与级配，符合竞赛语义）；`exclude_anomalies=False` 可关。
- 质量加权用阶梯逆 CDF（与"50% 质量通过筛孔"物理语义一致），拟合用无梯度差分进化。
- 形貌/异常阈值均为经验基线，需要真实骨料数据标定（标注于各模块 docstring）。

## 已运行验证

- `pytest tests/`：26 passed。
- `python -m aggregate_screening --grains ..._re_scaled.csv --out_dir /tmp/ig_report`：报告、JSON、对比图、逐颗粒标注 CSV 全部生成。
- 消融表：number→γ=1/2/3 的 D50 单调变化，符合预期。

## 已知问题

- 形貌/泥团阈值未用真实骨料标定；67mm 异物在 demo 中被正确检出，但更复杂的泥团场景未验证。
- 图内文字为英文（DejaVu 无中文字形，避免方块）。
- `tests/test_imagegrains.py` 仍是占位用例。
- fit_calibration 需真实筛分数据才有意义，当前仅合成数据验证。

## 使用手册

- `docs/USAGE.md`：竞赛版完整使用手册（环境/模型/两阶段命令/全部参数/输入输出说明/
  结果解读/校准流程/现场 30 分钟 SOP/常见问题）。上手先读它。
- 已补充"9. 竞赛口径答疑"：双口径策略（任务字面 vs 评分基准）、d 的来源、γ=3 语义、
  bootstrap/CI 含义（无需多次拍照）、标准筛分=质量分布、校准实验须赛前自备等。
- 模型 `models/IG2_full_set_cp_SAM`（1.2GB）已放入项目 models/ 并 gitignore，不进版本库。

## 下一步建议

1. 采集骨料图像 + 筛分实验 batch（称重 + 机械筛分 + 拍照）→ `fit_calibration` 校准 θ/γ。
2. 评估预训练模型在真实骨料上的分割质量。
3. ArUco/标尺标定模块（现场 30 分钟约束）。

---

# 历史交接：官方工作流已跑通（2026-08-16）

## 任务目标

在自然堆积赛道（`docs/task.md`）上基于 ImageGrains 2.0 构建骨料智能筛分系统。本轮完成环境搭建与官方工作流验证。

## 已完成步骤

- 创建 conda 环境 `imagegrains`（Python 3.10，`conda create --override-channels -c conda-forge`；Anaconda 默认频道需要 ToS，用 override-channels 绕过）。
- `pip install -e '.[test]'` 安装成功：imagegrains 2.0.3.dev10、cellpose 4.2.1.1、torch 2.13.0（CUDA 版）、pytest 9.1.1。
- GPU 验证：RTX 4080 SUPER（CUDA 可用）。
- 模型：`~/imagegrains/models/IG2_full_set_cp_SAM`（1.2GB）。注意：首次 `--download_data True` 下载的模型文件损坏（333MB 截断），已删除并用 `curl -L --retry` 从 zenodo.org/records/15728186 重新下载成功。
- demo 完整闭环：`python -m imagegrains --img_dir /tmp/ig_in --out_dir /tmp/ig_out --resolution demo_data/FH_resolutions.csv`
  - 分割：2.8s/张（GPU），输出 `*_pred.tif` mask + composite.png；
  - 粒径：57 颗粒 → `*_pred_grains.csv`（px）与 `*_pred_grains_re_scaled.csv`（mm，0.39 mm/px）；
  - GSD：D16=6.3 / D50=9.2 / D84=14.9 / D96=25.2 mm（b 轴、bootstrap、95% CI），含 `GSD_uncertainty/` 完整不确定度。
- 工作流五步均可独立跳过（`--skip_segmentation` / `--skip_grainsize`），resampling 未在 demo 中使用（比赛场景全量测量）。

## 改动文件

- 本轮无仓库代码改动；验证产物在 `/tmp/ig_in`、`/tmp/ig_out`（临时）。
- 新增 `opencode.json`（项目级：`permission.edit = allow`，本仓库编辑免询问；需重启 opencode 生效）。

## 重要决策

- 使用官方预训练模型 `IG2_full_set_cp_SAM` 作为基线；后续评估其在真实骨料上的分割质量再决定是否微调。
- 比赛统计口径以"质量加权分布 → 标准筛分对照"为准（见 DECISIONS.md），原生 number-based GSD 仅作中间产物。

## 已运行验证

- `pytest tests/`：1 passed（占位测试）。
- `python -m imagegrains --help`、demo 完整流水线（分割→粒径→尺度→GSD+不确定度）输出全部符合预期。

## 已知问题

- `tests/test_imagegrains.py` 只有占位用例，尚无真测试。
- 模型下载不可靠（首次损坏），后续需要记录 Zenodo 直接下载方式或做文件完整性校验。
- CLI 默认模型路径是 `~/imagegrains/models/`；`models/` 仓库目录内是 Cellpose 2 旧模型（`.170223`），与 cellpose 4.x 不兼容，不能直接用于 SAM 推理。

## 下一步建议

1. 采集真实骨料图像（或自制小批次），用 `IG2_full_set_cp_SAM` 评估分割质量（漏分/粘连/误检）。
2. 建立 mm 尺度标定（ArUco/标尺），替代 demo 的固定 resolution CSV。
3. 实现筛分等效粒径 + 质量加权分布模块（`docs/ai/PLAN.md` P0）。
4. 制作筛分对照实验 batch（称重 + 机械筛分 + 拍照）。

---

# 历史交接：agent 文档收束（2026-08-15）

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
