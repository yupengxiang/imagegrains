# AI 跟进任务

TODO 项不是自动的实施许可；实施前需用户或当前任务显式选择。

## 竞赛开发（P0，参考 `docs/ai/PLAN.md`）

- [ ] 安装环境并跑通官方工作流：`pip install -e .[test]`，在 `demo_data/` 上验证 CLI/notebook 的分割→粒径→GSD 闭环。
- [ ] 用真实骨料图像评估预训练模型（`models/` 或 `~/imagegrains/models/`）的分割质量，决定是否微调。
- [ ] 实现尺度标定（ArUco/标尺 → mm/px 换算），建立固定拍摄装置与成像参数。
- [ ] 实现筛分等效粒径模块与质量加权分布（`wᵢ=dᵢ^γ`），输出 D10/D50/D90。
- [ ] 制作 ≥10–20 个筛分实验 batch（称重 + 机械筛分 + 拍照），校准等效粒径参数。

## 竞赛开发（P1/P2）

- [ ] 形貌分类（针片状/圆形/棱角状，先规则后分类器）。
- [ ] 异常检测（>50 mm 阈值 + 泥团实例分类）。
- [ ] 一键式本地应用/报告界面与自动 QC（现场 30 分钟约束）。
- [ ] 必要时微调 Cellpose-SAM（`notebooks/4_train_cellposeSAM_model.ipynb`）。

## 工程卫生

- [ ] 补全 `tests/`：当前只有占位用例；为新增模块补针对性 pytest。
- [ ] 验证本地 GPU/CPU 推理环境并记录在 `docs/ai/testing.md`（如适用）。
