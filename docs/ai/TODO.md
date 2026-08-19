# AI 跟进任务

TODO 项不是自动的实施许可；实施前需用户或当前任务显式选择。

## 已落地（2026-08-19）

- [x] 竞赛版使用手册 `docs/USAGE.md`（环境/模型/两阶段命令/参数/输入输出/结果解读/校准/SOP）。
- [x] 模型 `models/IG2_full_set_cp_SAM`（1.2GB，Zenodo 完整版）放入项目 `models/` 并加入 `.gitignore`（不进版本库）。

## 依赖真实数据/硬件（P0）

- [ ] 采集骨料图像 + 筛分实验 batch（称重 + 机械筛分 5/10/16/20/25/31.5/40mm + 拍照），
      用 `fit_calibration` 校准 θ/γ（当前为默认经验基线，评分误差的主要来源）。
- [ ] 用真实骨料图像评估预训练模型（`~/imagegrains/models/IG2_full_set_cp_SAM`）的
      分割质量（漏分/粘连/误检），决定是否微调。
- [ ] 实现尺度标定：ArUco/标尺检测 + homography 透视校正，替代固定 resolution CSV。

## P1

- [ ] 泥团/非骨料分类器：当前为尺寸+凸度兜底规则；有图像 crop 后接入颜色/纹理分类。
- [ ] 形貌阈值用真实骨料数据标定（`morphology.DEFAULT_THRESHOLDS`）。
- [ ] 一键图形界面/自动 QC（Streamlit 或等价物），适配现场 30 分钟约束。

## 工程卫生

- [ ] 补 `tests/test_imagegrains.py` 真实用例（当前占位）。
- [ ] 骨料分割质量评估脚本（批量跑模型 → 目检/指标统计）。
