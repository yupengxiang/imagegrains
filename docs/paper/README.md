# 技术报告 LaTeX 工程（`docs/paper`）— 工业级重构版

> 竞赛：混凝土骨料颗粒智能筛分比拼（自然堆积赛道）— 技术报告，`Word/PDF` 提交，匿名评审。  
> 对标：Qwen2.5 / DeepSeek-V3/R1 / Meta Llama 3.1 Technical Report 范式（Executive Summary + Related Work + 方法/实验物理隔离 + 独立 Ablation + Limitations 主动披露）。

## 编译后状态

- `main.tex` 634 行，20 页（A4 12pt），39 MB，`xelatex → bibtex → xelatex×2` 0 错、0 Overfull
- `refs.bib` 324 行，33 条（含 GB/T 14685/JGJ52/ASTM + IG2/Cellpose-SAM/SAM + 级配校准 + 形貌经典）
- `latexmk -xelatex` 一键通过，`make check` 匿名/未定义/Overfull 检查通过

## 目录结构

```
docs/paper/
  main.tex       # 主文件（ctexart + tcolorbox + algorithm2e + cleveref + siunitx）
  refs.bib       # GB/T 7714，33 条
  figures/       # 预留矢量重绘（当前直引 ../../demo_data/samples/results/ 实测图，8 张）
  tables/        # 大型表格独立
  latexmkrc      # pdf_mode=5 xelatex
  Makefile       # make / make check / clean
  README.md      # 本文件
```

## 快速编译

```bash
cd docs/paper
latexmk -xelatex -interaction=nonstopmode main.tex
# 或
make
xelatex main && bibtex main && xelatex main && xelatex main
```

## 章节蓝图（18-22 页预算，当前 20 页）

| 章 | 标题 | 核心图表 | 映射 |
|---|---|---|---|
| Exec | Executive Summary + Checklist（双 tcolorbox，30s 抓分） | Box E1, Fig E1 | 评分四维度 |
| 1 | 引言：筛分语义→视觉语义鸿沟 | Tab 筛组鸿沟, Fig1 三难点 | 任务背景 |
| 2 | 相关工作（新增） | Tab2 三路线对比, Fig2 IG2 | 为何选 SAM |
| 3 | 系统总览 | Fig3 四步链+校准回路, Tab3 模块映射 | 6 模块契约 |
| 4 | 精细识别 | Fig4 三联, Tab4 参数 | 任务1 |
| 5 | 粒径分析 | Fig6 轴叠加, Fig7 GSD, Eq1-3, Tab5 双口径, 定义/假设环境 | 任务2 |
| 6 | 形状分类 | Fig8 四类, Tab6 规则 | 任务3 |
| 7 | 异常检测 | Tab7 阈值, Fig9 高亮, Tab8 剔除对比 | 任务4 |
| 8 | 尺度标定与参数校准（新增 Alg1） | Fig10 溯源链, Alg1 差分进化, Tab9 合成恢复 | 标定可追溯 |
| 9 | 实验与验证（重构6段） | Tab10 数据集, Tab11 主结果, Tab12 四维消融, Fig11 CI, Fig12 时序 | 全维度 |
| 10 | 设备选型与 30min SOP | Tab13 设备, Fig13 甘特 | 现场约束 |
| 11 | 局限、失败分析与展望（新增 tcolorbox） | Fig14 失效边界, Tab14 误差分解 | 主动披露 |
| 12 | 结论 | — | 贡献三点 |
| App | 产出一览与一键复现 + 匿名检查 | listing | 提交材料 |

## 对标改进（本次重构 6 项）

1. **Related Work 前置** `main.tex:122`：补 Tab2 三路线（阈值/YOLO/SAM）与级配校准/形貌经典综述，引用 `kirillov2023`/`buscombe2020` 等 18 条新文献
2. **Executive Summary 双框** `main.tex:72`：tcolorbox 蓝/绿双框，评委30s 抓住质量加权口径与 3 样本证据
3. **方法形式化** `main.tex:235`：`definition` 筛分等效粒径 + `assumption` 体积律，符号与 `_columns.py:8` 单一来源对齐
4. **校准算法化** `main.tex:412`：`algorithm2e` 伪代码 bounds/loss 0.25r10²+0.5r50²，可复现
5. **实验 6 段** `main.tex:466`：数据集→主结果→消融四维→不确定度→性能→测试覆盖，Tab12 独立消融，Fig12 时序，解决原 `H2` 方法实验混淆
6. **局限单章** `main.tex:560`：红框主动披露遮挡>30%/ <3mm漏检/厚度缺失/泥团兜底，误差分解与路线图

## 图表规范

- 浮动 `[htbp]` + `\FloatBarrier`，三样本并列 `subcaption 0.32\textwidth`
- `siunitx` 单位，`booktabs` 三线表，`cleveref` \cref 交叉引用
- 配色：蓝(分割) 绿(测量) 橙(筛分) 统一，图内英文防方块，300dpi

## 关联

- 赛题 `../task.md`，提交 `../paper_and_slide.md`，手册 `../USAGE.md` §10
- 架构 `../architecture.md`，数据流 `../data-flow.md`
- 幻灯片 `../slide/main.tex` 12 页，Madrid 16:9 同链

