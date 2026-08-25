# 竞赛技术报告 LaTeX 工程

本目录维护“混凝土骨料颗粒智能筛分比拼（自然堆积赛道）”的正式技术报告。

## 唯一入口

- 主文件：`main.tex`
- 参考文献：`refs.bib`
- 正文章节：`reviewer/`
- 当前构建产物由 GitHub Actions 上传为 `technical-report-pdf`

旧的 `main_submission.tex` 与 `main_v2.tex` 已移除。后续论文修改、编译和提交均以 `main.tex` 为准。

## 报告结构

正式报告采用以下结构：

1. 问题定义与主要贡献
2. 总体框架与技术路线
3. 视觉感知与物理测量
4. 从视觉颗粒到筛分级配
5. 实验结果与分析
6. 工程部署、质量控制与方法边界
7. 结论
8. 参考文献
9. 附录：关键参数与输出说明

报告保留封面、摘要、关键词和二级目录，按 GB/T 7714 数字顺序制生成参考文献。

## 当前证据口径

本轮报告以仓库中已有材料作为最终证据集，不再假设后续补充机械筛分或人工标注：

- 三张自然堆积真实图像：`agg_001`、`agg_005`、`agg_029`；
- 三张图共 3858 个实例及其逐颗粒/场景级输出；
- 27 项竞赛工程层合成测试；
- 已有算法阶段运行时序。

当前报告固定使用：

- `theta=(1,0,0)`：短轴作为筛分等效粒径基线；
- `gamma=3`：`w=d^gamma` 的质量代理先验。

没有配对机械筛分真值时，相关结果统一称为“视觉质量代理级配”；二维形状输出称为“投影形貌”；泥团等规则输出称为“异常候选”。

## 写作规范

修改正文前请参考：

`../ai/report-writing-skill/SKILL.md`

该规范用于保持技术事实、公式、引用和证据边界，同时减少模板化路标词、自我辩护、宣传式措辞和重复结论。方法段优先采用“动机 -> 定义 -> 公式 -> 参数含义 -> 后果”的组织；结果段优先采用“观察 -> 数据 -> 机制 -> 含义”的组织。

## 编译

```bash
cd docs/paper
latexmk -xelatex -interaction=nonstopmode main.tex
```

或：

```bash
make
```

检查：

```bash
make check
```

GitHub Actions `.github/workflows/paper-build.yml` 在 `docs/paper/**` 变更后自动编译 `main.tex`，检查未解析引用和 Overfull，并上传 PDF artifact。

## 当前构建状态

2026-08-25 第一轮全文写作优化后的 CI 构建：

- 19 页；
- XeLaTeX/BibTeX 编译成功；
- 无 unresolved reference/citation；
- 无 Overfull box。

少量 Underfull 提示来自长等宽代码名，不影响版面完整性。

## 目录说明

```text
docs/paper/
  main.tex       # 正式报告唯一入口
  refs.bib       # 参考文献数据库
  reviewer/      # 正文、摘要与附录
  figures/       # 报告图形资源
  latexmkrc      # XeLaTeX 构建配置
  Makefile       # 本地编译与检查
  README.md      # 本文件
```

相关材料：

- 赛题说明：`../task.md`
- 使用手册：`../USAGE.md`
- 系统架构：`../architecture.md`
- 数据流：`../data-flow.md`
- 内部写作/交接规范：`../ai/`
