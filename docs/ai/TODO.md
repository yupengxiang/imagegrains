# AI 跟进任务

TODO 项不是自动的实施许可；实施前需用户或当前任务显式选择。

## 已落地（2026-08）

- [x] 竞赛工程层 MVP + 代码重构 `9435f9b`（`_columns`/`SieveAnalysis`/`SceneSummary`，27 passed）
- [x] 使用手册 `docs/USAGE.md` 瘦身至 ~270 行并对齐新 API（`load_grains_csv`/`infer_resolution`/`CalibrationResult`）
- [x] `docs/architecture.md`/`data-flow.md` 四步链 + `_columns`/`scipy`，`Readme` 竞赛横幅
- [x] `docs/ai/*` 收束过时断言，`docs/ai` 明确仅面向 agent
- [x] 模型 `models/IG2_full_set_cp_SAM`（Zenodo 1.2 GB，gitignored）

## 依赖真实数据/硬件（P0）

- [ ] 采批料筛分实验校准 θ/γ（当前经验基线，评分误差主因）
- [ ] 评估真实分割质量（漏分/粘连/误检），定是否微调
- [ ] ArUco/标尺标定 + homography 透视校正

## P1

- [ ] 泥团分类器（颜色/纹理，当前尺寸+凸度兜底）
- [ ] 形貌阈值重标定（`MorphThresholds`）
- [ ] 一键图形界面/自动 QC（现场 30 分钟）

## 工程卫生

- [ ] 补 `tests/test_imagegrains.py` 真实用例
- [ ] 分割质量评估脚本
