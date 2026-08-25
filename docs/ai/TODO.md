# AI 跟进任务

TODO 项不是自动实施许可；实施前需用户或当前任务显式选择。

## 已落地（2026-08）

- [x] 竞赛工程层 MVP + 代码重构（`_columns`/`SieveAnalysis`/`SceneSummary`，27 passed）
- [x] 三张自然堆积真实样本的端到端演示输出
- [x] 正式技术报告收敛为唯一入口 `docs/paper/main.tex`
- [x] 删除旧 `main_submission.tex` / `main_v2.tex`，CI 只编译 `main.tex`
- [x] 报告采用“现有证据即最终证据集”的终稿定位
- [x] 新增 `docs/ai/report-writing-skill/SKILL.md`
- [x] 第一轮全文去模板化/去防御性语言优化
- [x] 第二轮逐图、逐表、术语与第 4/5 节逻辑精修
- [x] 最终 PDF 版式检查：目录、参考文献、分页、图表漂移、Overfull
- [x] 正文定稿为 17 页，CI 无 unresolved reference/citation、无 Overfull
- [x] 论文章节树统一为 `docs/paper/sections/`，删除旧 `reviewer/`、旧章节和 `*_final.tex` 副本
- [x] 增加 VS Code / LaTeX Workshop 项目级 XeLaTeX + latexmk 配置
- [x] 本地编译兼容 TeX Live 2023/2026，并增加 `make doctor`

## 当前 P0：提交材料

- [ ] 基于正式报告制作答辩 PPT
- [ ] 整理核心代码框架、设备配置和支持材料
- [ ] 统一论文、PPT 与现场演示中的参数和术语

## 不纳入当前提交阶段的工程扩展

以下工作保留为代码/研究扩展方向，但用户已决定本轮不再为报告新增实际采样或机械筛分实验：

- 机械筛分数据校准 theta/gamma
- 人工实例 mask 精度评估与分割微调
- ArUco/homography 自动尺度校正
- 泥团颜色/纹理分类器
- 三维形貌测量
- 一键图形界面/自动 QC
