# 架构决策

本文件记录已反映在代码/文档中的稳定决策，未来 agent 应保持，除非任务明确要求重审。

## 仓库定位：竞赛 fork

本仓库是 ImageGrains 2.0 分支，服务“混凝土骨料颗粒智能筛分比拼”（自然堆积赛道）。上游保持原样，竞赛能力增量开发。

影响：不改 `src/imagegrains/` 公开签名/CLI/输出格式；新能力放独立子包；不设计传送带。

## 正式报告：唯一入口、唯一章节树与最终证据政策

- 正式论文唯一入口为 `docs/paper/main.tex`。
- `docs/paper/sections/` 是唯一章节源，只保留 `main.tex` 实际引用的摘要、7 个正文 section 和附录。
- 不建立平行章节树，不保留 `*_final.tex` 副本或未引用历史章节；历史内容由 Git 版本记录承担。
- 旧 `main_submission.tex`、`main_v2.tex` 与 `docs/paper/reviewer/` 已删除。
- 当前三张真实图像、现有算法输出、27 项合成测试与已有运行记录构成本轮报告的最终证据集。
- 本轮不再新增机械筛分、人工实例 mask 或材料语义标注实验。
- 报告不保留“待补真值”“后续回填实验结果”等中期稿叙事。
- 没有机械筛分真值时，D10/D50/D90 与筛级占比统一称为“视觉质量代理级配”。

## 评分语义：质量代理优先

标准筛分按质量分布定义级配，因此视觉几何经 `d=θ₁b+θ₂d_eq+θ₃` 与 `w=d^γ` 形成质量相关统计；数量口径仅作对照。`_columns.py` 为列名单一来源。

当前报告固定使用：

- `theta=(1,0,0)`：短轴基线；
- `gamma=3`：几何相似条件下的质量代理先验。

代码保留 `CalibrationResult` / 差分进化校准接口，但该接口不属于当前报告的实际实验步骤，不得写成“已校准模型”。

## 数据与文件契约

沿用上游约定（`coding-style.md`/`data-flow.md`）：图像-mask 同名 `_mask.tif`；逐颗粒 `*_grains.csv`（`ell: b-axis` 列）；GSD `*_gsd.csv`；尺度经 `--resolution` 或 `infer_resolution`。擅自改名会破坏读取路径。

## 依赖边界

cellpose ≥4.0.1 + PyTorch 为重型计算；`pip install -e .[test]` 为标准安装；scipy 用于可选校准。不引新重型依赖。

## 已落地方法

- 筛分等效粒径 `SieveAnalysis`：`d=θ₁b+θ₂d_eq+θ₃`，当前报告默认 b 轴；
- 质量代理：`w=d^γ`，当前报告 `γ=3`；
- `CalibrationResult`：差分进化校准接口已实现，但仅在存在外部物理数据时有实际校准意义；
- 形貌 `MorphThresholds`：二维投影规则法；
- 异常：`MUD_BAND/FOREIGN_MIN` 等几何候选规则；
- 报告 `SceneSummary`/`NormalOnly` 与一键 CLI `python -m aggregate_screening` 已实现，`scene_summary` 返回 `(summary,df_final)` 单一流水线。

## 写作与证据边界

论文编辑使用 `docs/ai/report-writing-skill/SKILL.md`。

必须保持以下区分：

- ImageGrains 2.0 / Cellpose-SAM 是复用的预训练实例分割基础；
- 本项目贡献位于毫米测量、筛分等效粒径、质量代理统计、投影形貌/异常集成、报告与现场质检；
- 27 项合成测试说明实现一致性，不说明现实物理准确率；
- 投影形貌不等同于三维针片状量规结果；
- 疑似泥团是候选规则，不是材料语义分类器；
- 约 27 s/张是已有算法阶段时序，不是完整 30 min 现场流程实测总耗时。

## Code Reorg 2026-08

- 列常量集中 `_columns.py`；`load_grains_csv`/`infer_resolution`/`normalize_grains` 显式化，删 `df.attrs` 隐式通道；
- `SieveAnalysis`/`SceneSummary` dataclass 替代裸 dict，`size_fractions` 返回 `dict`；
- 显式优先级 `angular>round>needle`，`anomaly` 统一命名与长度校验；`app` 懒加载绘图、去 CSV 回读、库函数抛 `ValueError`。

## 当前不实施的扩展方向

以下能力可作为长期研究方向保留，但不属于本轮报告交付：

- 机械筛分数据校准 θ/γ；
- ArUco/标尺 + homography 透视校正；
- 泥团颜色/纹理分类器；
- 三维形貌测量；
- 一键图形界面。
