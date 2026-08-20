# 当前任务计划

## 当前任务：文档重构（2026-08）

在 `9435f9b` 代码优雅重构基础上，对齐并瘦身文档，保持与 `SieveAnalysis`/`SceneSummary` 代码一致：

- `Readme` 顶部竞赛横幅（已完成）
- `docs/USAGE.md` 瘦身至 ~270 行：`load_grains_csv→infer_resolution→normalize_grains`、dataclass API、`size_fractions` dict、`CalibrationResult`，合并答疑与排障，导航不再指向 `ai/*`
- `docs/architecture.md`/`data-flow.md` 四步链 + `_columns`/`scipy`
- `docs/ai/*` 收束过时断言（本文件、HANDOFF/TODO/DECISIONS/project-overview）

验证：`python -m compileall` + 人工 `Readme→USAGE→architecture` 三跳；无需 pytest。

## 已完成

- 竞赛工程层 MVP + 代码重构（`9435f9b`，27 passed）+ 使用手册 `71cf7a8/4a6a7ad`

## 下一步（依赖真实数据/硬件）

1. 采批料筛分实验校准 θ/γ（评分误差主因）
2. 评估真实分割质量，定是否微调
3. ArUco/标尺标定
4. 泥团分类器与形貌阈值重标定

## 验收口径

D50 <5%，D10/90 <10%，主粒级通过率 <10%，现场 30 分钟拍照→一键报告。
