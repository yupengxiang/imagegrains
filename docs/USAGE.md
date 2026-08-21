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
| `<场景>_detection_overview.png` | 任务1：原图｜mask｜叠加 三联图 |
| `<场景>_axes_overlay.png` | 任务2：长（青）短（红）轴 + 右下比例尺 |
| `<场景>_shape_*.png` | 任务3：`needle_flaky/round/angular/regular` 各一张高亮 |
| `<场景>_anomaly_*.png` | 任务4：`oversized/suspect_mud/undersized`（有则出图） |

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

## 10. 傻瓜式全流程（以仓库已提交的 `demo_data/samples/agg_001.jpg` 为例）

> 选样：全面检查 30 张（`agg_001–030` 均 `3024×4032`，`D50 质量 14.6–27.5 mm` 中位 23.6）后挑 **3 张代表进库（`samples/` 21 MB）**：`agg_029` 细粒主导（`5–10` 32.7%）、`agg_001` 中值（`25–31.5` 34.2%）、`agg_005` 粗粒（`27.5`），覆盖连续级配；`031–036` 尺截断未进库。本节以 `agg_001` 演示，另 2 张同参复跑。

```bash
# 0. 环境与模型（一次）
conda activate imagegrains
# 模型 1.2 GB 已在 .gitignore，需手动：curl -sL --retry 5 -o models/IG2_full_set_cp_SAM https://zenodo.org/records/15728186/files/IG2_full_set_cp_SAM

# 1. 分割+测量（单张约 17s GPU + 9s 测量；* 支撑任务 1）
python -m imagegrains --img_dir demo_data/samples --model_dir models --out_dir demo_data/samples/demo --resolution 0.208 --gpu True
# 输入：demo_data/samples/agg_001.jpg（+另 2 张，仓库已提交）
# 输出：demo_data/samples/demo/agg_001_IG2_full_set_cp_SAM_pred.tif（mask 1…1924，任务1精细识别）
#       demo_data/samples/demo/agg_001..._composite.png（目检粘连）
#       demo_data/samples/demo/agg_001..._pred_grains.csv（20 列 px，任务2前半）
#       demo_data/samples/demo/agg_001..._pred_grains_re_scaled.csv（追加 a/b mm 2 列，rescale 仅 b/a×0.208）

# 2. 筛分报告（* 支撑任务 2/3/4，约 1s）
python -m aggregate_screening --grains demo_data/samples/demo/agg_001_IG2_full_set_cp_SAM_pred_grains_re_scaled.csv --out_dir demo_data/samples/demo/report
# 也可批量：for f in demo_data/samples/demo/*re_scaled.csv; do python -m aggregate_screening --grains $f --out_dir demo_data/samples/demo/report; done

# 3. 看结果（与已提交的 demo_data/samples/results/ 对比）
cat demo_data/samples/demo/report/agg_001*report.txt
# 颗粒数 1924 分辨率 0.208 mm/px
# D10 数量3.1/质量10.6  D50 数量6.0/质量23.5  D90 数量17.3/质量30.6
# 剔除异常后（1193 颗正常）：D10 11.1 D50 23.6 D90 30.6  ← 提交口径（任务2）
# 粒级 25-31.5 34.2% 为主（右柱即筛分质量直方图）
# 形貌：针片 16.3% 圆 8.0% 棱角 16.4% 普通 59.3%（任务3，shape_class 列）
# 异常：<5 噪声 731 颗 38%  >50 0 颗（任务4，大块靠粒径；泥团当前仅 40-50 & solidity 几何兜底，需新数据训 crop 分类器）
ls demo_data/samples/demo/report/
# agg_001..._summary.json / _particles_annotated.csv / _gsd_comparison.png（任务2）
# agg_001..._detection_overview.png（任务1 三联）
# agg_001..._axes_overlay.png（任务2 长短轴+比例尺）
# agg_001..._shape_*.png（任务3 4 张）
# agg_001..._anomaly_*.png（任务4 有则出）
# 已提交结果可直接看：ls demo_data/samples/results/ | grep agg_001
```

> 三样本的推理结果已提交至 `demo_data/samples/results/`（75 MB，48 文件：每样本 `pred.tif/composite.png` + `*grains.csv`2 + `reports` 11 件含 8 张可视化），免重复推理；`demo/` 为本次演示输出，与 `results/` 同构可比对。

`GSD_uncertainty/*_full_uncertainty.csv` 为数量口径 bootstrap 95% CI（`lower/median/upper/value`），答辩展示用，非评分。

## 11. 命名与列释疑（新人常问）

- `area` vs `area_convex`：前者颗粒真面积，后者最小凸包面积，`convexity=area/area_convex` 近 1 越凸；泥团判据用 `solidity<0.85` 即凹陷多疑似泥团。
- `IR=4πA/P²`：`A=area`，`P=perimeter_crofton` 周长平方（非面积），圆为 1；`IRn=IR/IRt`（`IRt` 为同 `a/b` 椭圆理论值，Ramanujan 周长 `grainsizing.py:271`）。
- `ell: a/b-axis (mm)` vs `b_mm/a_mm`：同值，后者为 `normalize_grains` 标准化列（`_columns.py` 单一来源），`area_px/d_eq_mm/__resolution` 为显式追溯列。
- `b 轴方位角` 冗余：`b⊥a`，`b_az = orientation+90°`，因 `orientation` 为弧度、`b_az` 为 `°` 且地质惯用 `b` 轴，列出免换算。

## 12. 任务书→代码→输出映射

| 赛题 `docs/task.md` | 代码过程 | 关键输出 | 判定 |
| --- | --- | --- | --- |
| **1 精细识别** 分割+粘连分离 | `segmentation_helper.predict_folder`（Cellpose-SAM） | `*_pred.tif`（mask `1…N`）、`*_composite.png` 目检 + `*_detection_overview.png`（原图｜mask｜叠加） | 颗粒/背景/粘连分离可视化 |
| **2 粒径分析** 直径+分布 `D10/50/90` | `grainsizing.batch_grainsize` + `sieve_equivalent.normalize_grains → SieveAnalysis(d=θb+θd_eq, w=d³)` | `*_pred_grains.csv`→`*_re_scaled.csv`（`b/a mm`）→ `summary.json:percentiles`、`_gsd_comparison.png` + `*_axes_overlay.png`（长短轴+比例尺，mm 可读） | 数量 vs 质量双口径，比例尺可追溯 |
| **3 形状分类** 针片/圆/棱角 | `morphology.classify_dataset`（`MorphThresholds`） | `*_particles_annotated.csv:shape_*`、`summary.json:shape` + `*_shape_*.png`（4 张分形态高亮） | 投影形貌，直观可检 |
| **4 异常** >50 异物/泥团 | `anomaly.classify_anomalies`（`>50` / `40–50 & solidity`） | `*_particles_annotated.csv:anomaly_*`、`summary.json:anomalies` + `*_anomaly_*.png`（有则出图） | 大块已可视化，泥团待 `crop` 分类器 |

`GSD_uncertainty/*_full_uncertainty.csv:1` 的 8 列（`a/b × lower/median/upper/value`）为数量口径 bootstrap 区间，答辩展示用，非评分。

## 13. 数据与 Git 管理

- **GitHub 限制**：单文件硬上限 **100 MB**（`git push` 直接拒），仓库软建议 **1 GB**、硬上限约 **5 GB**，超大文件需 `git lfs`（单文件最高 5 GB，但 LFS 配额/带宽另计）。`demo_data/test` 236 MB 虽单文件未超 100 MB，但整批 `+test_out 302 MB` 推送会拖慢克隆且超软建议。
- `demo_data/K1` 2 张（793 KB）属历史小样已跟踪（`.gitignore:20` 的 `*.jpg` 对已跟踪不生效）；全量 `test` 36 张被 `*.jpg/*.tif/*.csv/*.png` 忽略（`git check-ignore -v demo_data/test/agg_001.jpg → *.jpg`），**不可 `git add`**。
- 约定：`test`/`test_out` 保持 `gitignored` 本地，**仅提交 3 张代表 `demo_data/samples/`（21 MB）及其推理结果 `demo_data/samples/results/`（75 MB，48 文件，`!demo_data/samples/results/*` 回补）** 供上手；全量走网盘/LFS。

---

## 14. 导航

- 赛题原文 `docs/task.md`；架构 `docs/architecture.md`；数据流 `docs/data-flow.md`
- 源码 `src/aggregate_screening/`（`sieve_equivalent/morphology/anomaly/report/app/_columns/scale`）；测试 `tests/test_*`；`pytest tests/`
