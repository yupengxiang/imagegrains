# 当前任务计划

## 当前任务：竞赛工程层 MVP（已基本完成，2026-08-16）

在跑通官方工作流的基础上，用 demo 数据（无自采数据）完成了竞赛工程层第一版：

- `src/aggregate_screening/` 子包：sieve_equivalent / morphology / anomaly / report / app。
- 一键 CLI：`python -m aggregate_screening --grains <csv> [--resolution] [--out_dir] [--theta] [--gamma]`。
- 核心口径：筛分等效粒径 `d = θ₁b + θ₂d_eq + θ₃`（默认 b 轴）+ 质量加权 `w = d^γ`（默认 3）→ D10/D50/D90 + 粒级质量占比；默认剔除异常物后统计正常骨料。
- 消融对照（答辩素材）：number D50=9.2 → mass-weighted γ=3 D50=67.1（含 67mm 异物）→ 剔除异常后 D50=18.8。
- 26 个 pytest 通过（含合成数据拟合校验：fit_calibration 可恢复真参数）。

验证：`pytest tests/`、`python -m aggregate_screening --grains /tmp/ig_out/*_re_scaled.csv`。

## 下一步（依赖真实数据/硬件）

1. **采集骨料图像 + 筛分实验**：自采 batch（称重 + 机械筛分 5/10/16/20/25/31.5/40mm + 拍照），
   用 `fit_calibration` 校准 θ/γ，这是把误差打下去的关键（当前默认参数是经验基线）。
2. **评估预训练模型在真实骨料上的分割质量**（漏分/粘连/误检），决定是否微调。
3. **尺度标定**：ArUco/标尺检测 + homography 透视校正，替代固定 resolution（现场 30 分钟约束）。
4. **泥团分类器**：当前为尺寸+凸度兜底规则；有图像 crop 后接入颜色/纹理分类。
5. **一键应用与自动 QC**：报告已文本化输出；现场可加图形界面（Streamlit 或等价物）。

## 验收口径（竞赛导向）

- D10/D50/D90 与标准筛分结果误差（内部目标：D50 相对误差 <5%，D10/D90 <10%）；
- 主粒径区间累计通过率误差 <10%；
- 现场 30 分钟内完成 拍照 → 一键分析 → 结果输出。
