# 骨料智能筛分使用手册（竞赛版）

> 目标：在 ≤30 分钟现场窗口内，从自然堆积骨料照片一键得到**筛分口径（质量加权）**的粒径分布、形貌与异常结果，支撑"混凝土骨料颗粒智能筛分比拼"（自然堆积赛道，见 `docs/task.md`）。

流水线 = 官方 ImageGrains（分割+测量）+ 竞赛工程层 `aggregate_screening`（筛分等效粒径+质量加权+形貌/异常）。工程层不改上游源码。

## 0. 快速上手

```bash
conda activate imagegrains
# 第1步：分割+测量
python -m imagegrains --img_dir <图目录> --model_dir models/ --out_dir <输出> --gpu True --resolution <mm/px>
# 第2步：筛分分析
python -m aggregate_screening --grains <输出>/*_re_scaled.csv --out_dir <输出>/report
```

---

## 1. 环境与安装

- conda 环境 `imagegrains`（Python 3.10，GPU 优先，实测 RTX 4080 SUPER）。
- 已安装：`imagegrains`（editable）、`cellpose`、`torch`、`scipy`、`pandas`、`matplotlib`、`pytest`。
- 新机器重建：

  ```bash
  conda create --name imagegrains -y --override-channels -c conda-forge python=3.10
  conda activate imagegrains
  pip install -e '.[test]'   # zsh 加引号
  ```

## 2. 模型

- `models/IG2_full_set_cp_SAM`（1.2 GB，Cellpose-SAM）。已在 `.gitignore` 排除，需手动放置：
  - `curl -sL --retry 5 -o models/IG2_full_set_cp_SAM https://zenodo.org/records/15728186/files/IG2_full_set_cp_SAM`
  - 或拷贝 `~/imagegrains/models/IG2_full_set_cp_SAM`
- `models/*.170223` 为旧 Cellpose 2 权重，与当前不兼容，仅保留。

---

## 3. 第 1 步：分割与测量（`imagegrains`）

### 3.1 命令

```bash
python -m imagegrains --img_dir <图目录> --model_dir models/ --out_dir <输出> --gpu True --resolution 0.39
```

### 3.2 常用参数

| 参数 | 含义 | 说明 |
| --- | --- | --- |
| `--img_dir` | 图片目录 | jpg/png/tif，批量处理 |
| `--model_dir` | 模型目录 | 默认找 `IG2_full_set_cp_SAM` |
| `--out_dir` | 输出目录 | 缺省写到输入目录，新数据前请清理 |
| `--gpu` | GPU | `True` 快；`False` 慢 |
| `--resolution` | **mm/px 关键参数** | 决定所有 mm 结果；无标尺时用场景已知值（demo 0.39） |
| `--diameter` | 目标平均粒径 px（默认 `None` 自动估计） | Cellpose 缩放提示：会把图像缩放到该直径≈30 px 再分割；`物理粒径 mm / 分辨率 mm/px` 估算（如 20 mm/0.39≈51 px），一般不改，目检粘连/破碎再 ±10 px 微调 |
| `--min_size` | 最小对象面积 px²（默认 `0` 不滤） | 面积<该值的 mask 丢弃（非正方形边长，如 `15`≈3×5 px 的视为噪声），一般不改 |
| `--skip_segmentation` | 跳过分割 | 已有 `*_mask.tif` 时（GT 真值或上次预测）复用直接测粒径 |
| `--skip_grainsize` | 跳过测量 | 仅分割时 |
| `--unc_method/--n/--scale_err/--length_err` | 不确定度 | bootstrap 方法/次数/尺度/长度误差，默认即可 |
| `--save_composites` | 叠加图 | 目检分割（默认 True） |
| `--filter_str/--min_grain_size/--edge_filter` | 滤波 | 剔边缘/过小，默认开 |

未列出参数为 Cellpose 高级项，查 `python -m imagegrains --help`。

### 3.3 输出（`--out_dir`）

| 文件 | 含义 |
| --- | --- |
| `*_pred.tif` | 实例 mask |
| `*_composite.png` | 原图+mask 叠加（目检） |
| `*_pred_grains.csv` | 逐颗粒明细（px） |
| `*_pred_grains_re_scaled.csv` | 同时含 px/mm 两套 a/b 轴（工程层据此自动推断分辨率） |
| `*_bootstrapping.csv` / `GSD_uncertainty/` | 数量口径 D 值及 95% CI（官方） |

### 3.4 grains CSV 列

| 列 | 含义 |
| --- | --- |
| `label` | 颗粒编号 |
| `area` | 面积 px²（重缩放后仍为 px²） |
| `area_convex` | 凸包面积 px² |
| `perimeter_crofton` | 周长 px（Crofton 法） |
| `ell: a/b-axis (px/mm)` | 椭圆长/短轴，px/mm 各一版 |
| `convexity` | 凸度 = area/area_convex（=solidity） |
| `centerpoint/bbox/orientation/eccentricity/IR` | 质心/外接框/方向/偏心率等（工程层未用） |

---

## 4. 第 2 步：筛分分析（`aggregate_screening`）

评分以质量分布为准，工程层做两层转换：

1. **筛分等效粒径** `d = θ₁·b + θ₂·d_eq + θ₃`（默认 `θ=(1,0,0)` 即 b 轴，短尺度控筛孔通过）；
2. **质量加权** `w = d^γ`（默认 `γ=3`，`m~d³` 体积加权）→ D10/D50/D90 与粒级占比。

内部列定义集中于 `src/aggregate_screening/_columns.py`，标准化入口为 `load_grains_csv` → `infer_resolution` → `normalize_grains`（旧名 `load_grains_df` 兼容）。

### 4.1 命令

```bash
# A 推荐：re_scaled.csv 同时含 px/mm，自动按 b_mm/b_px 中位数推断分辨率
python -m aggregate_screening --grains <输出>/*_re_scaled.csv --out_dir <输出>/report
# B 仅 px 列，需手动给分辨率
python -m aggregate_screening --grains <输出>/*_pred_grains.csv --resolution 0.39 --out_dir <输出>/report
# C mask 目录直接分析
python -m aggregate_screening --img_dir <图> --mask_dir <mask> --resolution 0.39 --out_dir <输出>/report
```

### 4.2 参数

| 参数 | 默认 | 含义（新人必读） |
| --- | --- | --- |
| `--grains` | — | `*_grains.csv` 或 `*_re_scaled.csv` |
| `--img_dir`+`--mask_dir` | — | 原图+mask 目录（方式 C） |
| `--resolution` | — | mm/px；`*_re_scaled.csv` 可省略（自动推断），纯 px 必填 |
| `--out_dir` | `./aggregate_report` | 输出目录 |
| `--theta` | `1,0,0` | `θ₁,θ₂,θ₃` 逗号分隔；校准后填入 |
| `--gamma` | `3.0` | 质量指数；`3` 体积加权，`2` 面积加权 |
| `--no_plot` | 关 | 不生成对比图 |

### 4.3 输出

| 文件 | 含义 |
| --- | --- |
| `<场景>_summary.json` | 结构化结果（`SceneSummary.to_dict()`） |
| `<场景>_report.txt` | 人读报告（D 值/粒级/形貌/异常） |
| `<场景>_particles_annotated.csv` | 明细 + `shape_*/anomaly_*` 列 |
| `<场景>_gsd_comparison.png` | 数量 vs 质量累计曲线 + 粒级柱状图 |

---

## 5. 结果解读

### 5.1 D 值

```
D10 数量=5.7mm / 质量加权=15.5mm
D50 数量=9.2mm / 质量加权=67.1mm   <- 被 67mm 异物主导
D90 数量=18.8mm / 质量加权=67.1mm
剔除异常后（正常 55 颗）: D10=9.5  D50=18.8  D90=28.1  <- 提交口径
```

- **数量 D50**：一半颗粒小于该尺寸；**质量 D50**：50% 质量对应的尺寸（等价筛分语义）。
- 默认展示**剔除异常后**口径（`report.scene_summary(..., exclude_anomalies=True)`），代码返回 `SceneSummary` dataclass：`summary.percentiles_mass_weighted` + `summary.normal_only`，需含异物时传 `False`。

### 5.2 粒级质量占比

按 `5/10/16/20/25/31.5/40 mm` 分桶的质量 %（`SieveAnalysis.fractions` 含 `<5`/`>40` 边界桶），可折累计通过率对标机械筛分。

### 5.3 形貌（可选加分）

规则法 `morphology.MorphThresholds`（`ar_needle=0.5` 等）：

| 类别 | 规则 |
| --- | --- |
| 针片状候选 | `b/a < 0.5` |
| 圆形 | `4πA/P²>0.85 & solidity>0.95 & b/a>0.8` |
| 棱角状 | `4πA/P²<0.6 | solidity<0.9`（非针片） |
| 普通 | 其余 |

优先级 `棱角>圆形>针片>普通`，为投影形貌，需自采数据重标定。

### 5.4 异常

| 类别 | 判定 | 说明 |
| --- | --- | --- |
| 大块异物 | `d>50` | `FOREIGN_MIN` |
| 过小噪声 | `d<5` | `NORMAL_MIN` |
| 疑似泥团 | `40<d≤50 & solidity<0.85` | `MUD_BAND`，默认开启可关 |

---

## 6. 参数校准（建议做）

默认 `θ/γ` 为经验基线，需自采数据校准：

```text
每批：称重 → 标准筛组(5/10/16/20/25/31.5/40)筛分 → 记录各粒级%与 D10/50/90 真值 → 拍自然堆积照 → imagegrains 测量
```

```python
from aggregate_screening.sieve_equivalent import fit_calibration
batches = [{"b_mm": ..., "area_px": ..., "resolution": 0.39}, ...]
targets = [(d10,d50,d90), ...]
res: CalibrationResult = fit_calibration(batches, targets)
# res.theta / res.gamma / res.success / res.fun
```

`--theta`/`--gamma` 填入校准值；建议 ≥5 批覆盖 5-40 mm。

## 7. 消融对照

```python
from aggregate_screening import report
tbl = report.ablation_table(df, 0.39, gammas=[1,2,3])
```

| method | theta | gamma | D50 |
| --- | --- | --- | --- |
| number | — | — | 9.2 |
| gamma=1.0 | (1,0,0) | 1.0 | 12.6 |
| gamma=2.0 | (1,0,0) | 2.0 | 23.7 |
| gamma=3.0 | (1,0,0) | 3.0 | 67.1 |

## 8. 现场 30 分钟 SOP

1. 摆拍：深色托盘单层撒料，放标尺/ArUco。2. 拍照 1 分钟（正俯 1-3 张）。3. 分割 5 分钟（`--gpu True`，看 `*_composite.png`）。4. 筛分 1 分钟（`aggregate_screening`）。5. 核对 `*_report.txt` 剔除后 D 值并导出图。

---

## 9. 答疑与排障

**Q1 任务只写 D10/D50/D90，为何要质量加权？**  `docs/task.md` 第4条"以标准筛分结果为准"——筛分是质量分档，质量口径才可比。工程层**双口径输出**（数量满足字面，质量对标评分）。

**Q2 `d` 是什么？** `d = θ₁b + θ₂d_eq + θ₃`，`b` 为短轴 mm（`b_px×res`），`d_eq=2√(area_px×res²/π)`；默认 `d=b`。`area` 重缩放后仍 px² 需自乘 `res²`。

**Q3 `γ=3` 是正方体假设？** 否，为体积∝尺寸³的缩放律，球/正方体皆成立，归一化消常数；形状随尺寸变化时 `γ` 偏离 3。

**Q4 bootstrap 要多拍？** 否，对单次测量有放回重采样 1000 次得 95% CI（如 `CI(D50)=[7.8,10.0]`），多拍仅增样本代表性。

**Q5 自动推断是否免标定？** 否，`*_re_scaled.csv` 的 mm 列已含第1步 `--resolution`，推断仅是反推；标定错误则整体偏（链：标尺→`--resolution`→CSV mm→推断）。

**Q6 形貌/泥团如何判？** 均为规则法（长宽比/圆度/凸度），阈值在 `_columns.py`/`MorphThresholds`，泥团仅尺寸+凸度兜底，需图像分类器升级。

**常见排障**：`模型找不到`→放 `models/IG2_full_set_cp_SAM`；`zsh: no matches`→引号；`需要 --resolution`→纯 px 需传值；`D50 异常大`→看剔除后行；`中文方块`→英文绘图预期。

---

## 10. 导航

- 赛题原文 `docs/task.md`；架构 `docs/architecture.md`；数据流 `docs/data-flow.md`
- 源码 `src/aggregate_screening/`（`sieve_equivalent/morphology/anomaly/report/app/_columns`）；测试 `tests/test_*`；`pytest tests/`
