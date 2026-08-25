# 答辩 PPT 工程（`docs/slide`）

> 赛题提交物 1/5：答辩 PPT（`ppt/pdf`），8--10 分钟陈述，需匿名。

## 编译

```bash
cd docs/slide
latexmk -xelatex -interaction=nonstopmode main.tex
# 或 make
make
```

引擎：`XeLaTeX` + `ctexbeamer` + `aspectratio=169`（16:9），主题 `Madrid`，与 `docs/paper` 同字体 `fandol`。

## 结构（9 节，对应技术报告）

封面 → 目录 → 任务解读 → 总体方案 → 精细识别 → 粒径分析 → 形状与异常 → 实验验证 → 设备/SOP → 结论

图表复用 `../../demo_data/samples/results/` 实测图，无需复制。

## 匿名检查

```bash
grep -inE "大学|学院|学校|导师|指导教师|校徽|学号" docs/slide/main.tex
```
