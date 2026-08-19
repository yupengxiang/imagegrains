# 骨料智能筛分使用手册（竞赛版）

> 目标：在 ≤30 分钟现场窗口内，从自然堆积骨料照片一键得到**筛分口径（质量加权）**的
> 粒径分布、形貌分类与异常检测结果，支撑"混凝土骨料颗粒智能筛分比拼"（自然堆积赛道，
> 见 `docs/task.md`）。

完整流水线 = 官方 ImageGrains（分割 + 测量）+ 本项目竞赛工程层 `aggregate_screening`
（筛分等效粒径 + 质量加权统计 + 形貌 + 异常）。工程层不修改上游源码。

---

## 0. 快速上手（10 秒版）

```bash
conda activate imagegrains

# 第 1 步：分割 + 测量（生成 mask 与逐颗粒 CSV）
python -m imagegrains --img_dir <图目录> --model_dir models/ --out_dir <输出> --gpu True --resolution <mm/px>

# 第 2 步：筛分分析（生成报告）
python -m aggregate_screening --grains <输出>/*_re_scaled.csv --out_dir <输出>/report
```

上面两行即完整流程。以下按需细读。

---

## 1. 环境与安装

- 需要 conda 环境 `imagegrains`（Python 3.10，GPU 优先，实测 RTX 4080 SUPER 可用）。
- 已安装：`imagegrains`（本项目，editable）、`cellpose`、`torch`、`scipy`、`pandas`、`matplotlib`、`pytest`。
- 若在新机器上重建环境：

  ```bash
  conda create --name imagegrains -y --override-channels -c conda-forge python=3.10
  conda activate imagegrains
  pip install -e '.[test]'        # zsh 下参数必须加引号
  ```

## 2. 模型

- 模型：`models/IG2_full_set_cp_SAM`（约 1.2 GB，Cellpose-SAM，专为骨料分割训练）。
- 该文件太大，已在 `.gitignore` 中排除，**不进版本库**，需要手动放置：
  - 官方渠道（Zenodo）：`curl -sL --retry 5 -o models/IG2_full_set_cp_SAM https://zenodo.org/records/15728186/files/IG2_full_set_cp_SAM`
  - 或从队友机器拷贝 `~/imagegrains/models/IG2_full_set_cp_SAM`。
- 注意：`models/` 下另外两个 `.170223` 后缀的是旧版 Cellpose 2 模型，与当前 cellpose 4.x
  不兼容，仅作历史保留，不要被 CLI 误用。
- 官方 CLI 会在 `--model_dir` 下自动查找名为 `IG2_full_set_cp_SAM` 的文件，找不到会报错并提示下载。

## 3. 第 1 步：分割与测量（`imagegrains`）

### 3.1 命令

```bash
python -m imagegrains \
  --img_dir <图片目录> \
  --model_dir models/ \
  --out_dir <输出目录> \
  --gpu True \
  --resolution <mm/px>        # 例：0.39；或用后面的标定方法得到
```

### 3.2 常用参数说明

| 参数 | 含义 | 说明 |
| --- | --- | --- |
| `--img_dir` | 输入图片目录 | 支持 jpg/png/tif，会处理目录内全部图片 |
| `--model_dir` | 模型目录 | 默认找 `IG2_full_set_cp_SAM` 文件 |
| `--out_dir` | 输出目录 | 不指定时写到输入目录（跑新数据前建议清理旧文件） |
| `--gpu` | 是否用 GPU | `True` 更快；无 GPU 用 `False`（会慢很多） |
| `--resolution` | 像素当量 mm/px | **关键参数**，决定所有 mm 结果；没有真实标尺时用已知场景值（本项目 demo 为 0.39） |
| `--diameter` | 目标颗粒典型直径（像素） | Cellpose 分割用的先验直径，供模型参考，一般无需改 |
| `--min_size` | 最小分割区域（像素面积） | 过滤过小区域，抑制噪声 |
| `--skip_segmentation` | 跳过分割 | 已有 `*_mask.tif` 时直接测量 |
| `--skip_grainsize` | 跳过粒径统计 | 只分割/测量不统计时用 |
| `--unc_method` / `--n` / `--scale_err` / `--length_err` | 粒径不确定度 | bootstrap 抽样方法/次数/尺度误差/长度误差，默认即可 |
| `--save_composites` | 保存叠加合成图 | 便于目检分割质量（默认 True） |
| `--filter_str` / `--min_grain_size` / `--edge_filter` / `--switch_filters_off` | 测量后滤波 | 控制是否剔除边缘/过小颗粒，默认开启，必要时关 |

> 未列出的参数（`--comb_threshold`、`--second_diameter`、`--fit`、`--grid_resample` 等）
> 为 Cellpose/重采样高级选项，默认值已够用；确需修改时查 `python -m imagegrains --help`。

### 3.3 第 1 步输出（都在 `--out_dir`）

| 文件 | 内容 |
| --- | --- |
| `*_pred.tif` | 分割 mask（每个颗粒一个编号） |
| `*_composite.png` | 原图 + 分割叠加合成图（目检用） |
| `*_pred_grains.csv` | **逐颗粒测量明细**（核心中间产物） |
| `*_pred_grains_re_scaled.csv` | 同上，但 a/b 轴已按分辨率换算为 **mm** |
| `a_axis_mm_ellipse_bootstrapping.csv` / `b_axis_mm_ellipse_bootstrapping.csv` | 粒径分布 bootstrap 不确定度 |
| `GSD_uncertainty/` | 数量分布 D10/D50/D90 及不确定度（官方口径） |

### 3.4 grains CSV 列说明（逐颗粒明细）

| 列 | 含义 |
| --- | --- |
| `label` | 颗粒编号 |
| `area` | 面积（px²，注意：重缩放后**仍是 px²**，不换算成 mm²） |
| `area_convex` | 凸包面积（px²） |
| `perimeter_crofton` | 周长（Crofton 法，px） |
| `orientation` | 主轴角度 |
| `ell: a-axis (px)` / `ell: b-axis (mm)` 等 | 拟合椭圆的 a（长）/b（短）轴，px 或 mm 单位各一版 |
| `centerpoint x/y`、`local centerpoint x/y` | 质心坐标 |
| `convexity` | 凸度（= 面积/凸包面积，同 solidity） |
| `eccentricity` | 椭圆偏心率 |
| `bbox x1..y2` | 外接框坐标 |
| `IR` / `IRn` | 内部反射率相关指标（上游定义，工程层未使用） |
| `b axis azimuth (deg)` | b 轴方位角 |

## 4. 第 2 步：筛分分析（`aggregate_screening`）

竞赛评分以标准机械筛分（质量分布）为基准，官方输出的是数量分布，所以工程层做了两层转换：

1. **筛分等效粒径**：`d_sieve = θ₁·b + θ₂·d_eq + θ₃`，把 2D 投影尺寸换算成"能否通过方孔筛"的等效粒径（默认 `θ=(1,0,0)`，即直接用 b 轴——颗粒通过筛孔主要受较短尺度控制）。
2. **质量加权**：`w = d^γ`（默认 `γ=3`，几何相似颗粒 `m ~ d³`），按质量而非个数聚合 D10/D50/D90 与粒级占比。

### 4.1 命令（三种输入方式）

```bash
# 方式 A（推荐）：直接分析 imagegrains 输出的 CSV（自动推断分辨率）
python -m aggregate_screening --grains <输出>/*_re_scaled.csv --out_dir <输出>/report

# 方式 B：只有 px 单位 CSV，手动给分辨率
python -m aggregate_screening --grains <输出>/*_pred_grains.csv --resolution 0.39 --out_dir <输出>/report

# 方式 C：已有 mask 目录 + 原图目录，边测量边分析
python -m aggregate_screening --img_dir <图目录> --mask_dir <mask目录> --resolution 0.39 --out_dir <输出>/report
```

### 4.2 参数说明

| 参数 | 默认 | 含义 |
| --- | --- | --- |
| `--grains` | 无 | ImageGrains 的 `*_grains.csv` 或 `*_re_scaled.csv`（方式 A/B） |
| `--img_dir` + `--mask_dir` | 无 | 原图目录 + mask 目录（方式 C） |
| `--resolution` | 无 | mm/px；px 单位 CSV 必填；CSV 同时含 mm/px 列时可省略（自动按 mm/px 中位数推断） |
| `--out_dir` | `./aggregate_report` | 报告输出目录 |
| `--theta` | `1,0,0` | 等效粒径参数 `θ₁,θ₂,θ₃`（逗号分隔三个数）。默认直接用 b 轴；有校准结果时传入校准值 |
| `--gamma` | `3.0` | 质量权重指数。`γ=3` 表示按体积加权；颗粒越近球且密度均匀越成立 |
| `--no_plot` | 关 | 不生成 GSD 对比图 |

### 4.3 第 2 步输出

| 文件 | 内容 |
| --- | --- |
| `<场景>_summary.json` | 全部结果的结构化数据（程序化读取用） |
| `<场景>_report.txt` | 人读报告（D 值对照、粒级占比、形貌、异常） |
| `<场景>_particles_annotated.csv` | 逐颗粒明细 + 新增 `shape_class`/`shape_label`/`anomaly_class`/`anomaly_label` 列 |
| `<场景>_gsd_comparison.png` | 数量 vs 质量加权累计分布曲线 + 粒级占比柱状图（答辩素材） |

## 5. 结果解读

### 5.1 D 值对照

```
D10 数量=5.7mm / 质量加权=15.5mm
D50 数量=9.2mm / 质量加权=67.1mm   <- 全颗粒口径，被 67mm 异物主导
D90 数量=18.8mm / 质量加权=67.1mm

剔除异常后（正常骨料 55 颗）:
  D10=9.5mm  D50=18.8mm  D90=28.1mm   <- 提交/答辩用这个口径
```

- **数量** D50：一半颗粒小于该尺寸（颗粒级视角）。
- **质量加权** D50：50% 质量对应的颗粒小于该尺寸，**等价于筛分语义**——这是竞赛要对标的口径。
- 默认报告口径为**剔除异常后**的"正常骨料"统计（异物/泥团不参与级配，符合比赛评分语义）；
  若想对比含异物口径，调用 `report.scene_summary(..., exclude_anomalies=False)`。

### 5.2 粒级质量占比

按标准筛孔 `5/10/16/20/25/31.5/40 mm` 分桶的质量百分比。可直接折算各孔径累计通过率，
与机械筛分结果对比。

### 5.3 形貌分类（可选加分）

基于投影几何的规则法：长宽比 `b/a`、圆度 `4πA/P²`、凸度 `A/A_convex`，分为
针片状候选 / 圆形 / 棱角状 / 普通。默认阈值（`morphology.DEFAULT_THRESHOLDS`）：

| 类别 | 规则 |
| --- | --- |
| 针片状候选 | `b/a < 0.5` |
| 圆形 | `4πA/P² > 0.85` 且 `A/A_convex > 0.95` 且 `b/a > 0.8` |
| 棱角状 | `4πA/P² < 0.6` 或 `A/A_convex < 0.9`（且非针片状） |
| 普通 | 其余 |

> 单张俯视 RGB 图无法获得真实厚度，这是**投影形貌**而非严格三维针/片判定；阈值需用
> 自采骨料数据重标定（见 `docs/ai/PLAN.md`）。

### 5.4 异常检测

| 类别 | 判定 | 默认 |
| --- | --- | --- |
| 大块异物 | `d_sieve > 50 mm` | 开启 |
| 过小噪声 | `d_sieve < 5 mm` | 开启 |
| 疑似泥团/非骨料 | 40 < `d_sieve ≤ 50` 且 `solidity < 0.85` | **默认关闭**（兜底规则未被真实数据验证，避免误报） |

## 6. 参数校准（`fit_calibration`，建议做）

默认 `θ=(1,0,0)`、`γ=3` 是经验基线。要贴近真实筛分结果，需自采实验数据校准：

```text
对每个批次：取一批骨料 -> 称重 -> 标准筛组(5/10/16/20/25/31.5/40mm)机械筛分
            -> 记录各粒级质量占比与 D10/D50/D90 真值 -> 拍一张自然堆积照
            -> imagegrains 分割测量 -> 得到 b_mm/area_px/resolution
```

然后（Python）：

```python
from aggregate_screening import sieve_equivalent as se

batches = [{"b_mm": ..., "area_px": ..., "resolution": 0.39}, ...]  # 每批一个
targets = [(d10, d50, d90), ...]  # 各批机械筛分真值
res = se.fit_calibration(batches, targets)
# -> {'theta': (θ1,θ2,θ3), 'gamma': γ, 'success': ..., 'fun': 损失}
```

把得到的 `theta` / `gamma` 通过 `--theta` / `--gamma` 传入报告。校准用的实验量越多、
粒径分布越广，参数越可靠（建议 ≥5 批覆盖 5-40mm 全范围）。

## 7. 消融对照（答辩素材）

```python
from aggregate_screening import report
tbl = report.ablation_table(df, 0.39, gammas=[1.0, 2.0, 3.0])
```

| method | theta | gamma | D50 |
| --- | --- | --- | --- |
| number | None | NaN | 9.2 |
| theta=(1,0,0), gamma=1.0 | (1,0,0) | 1.0 | 12.6 |
| theta=(1,0,0), gamma=2.0 | (1,0,0) | 2.0 | 23.7 |
| theta=(1,0,0), gamma=3.0 | (1,0,0) | 3.0 | 67.1（含异物）|

清晰展示"数量 → 质量加权"口径差异的演化。

## 8. 现场 30 分钟 SOP

1. 摆拍：自然堆积骨料撒在深色背景托盘（颗粒尽量单层、不重叠），旁边放标尺/ArUco 板。
2. 拍照（1 分钟）：固定机位俯拍，1-3 张覆盖全托盘。
3. 分割测量（约 5 分钟）：`python -m imagegrains ... --gpu True`，目检 `*_composite.png`
   确认分割质量（粘连/漏分严重则换机位重拍）。
4. 筛分分析（1 分钟）：`python -m aggregate_screening --grains ..._re_scaled.csv`。
5. 输出报告（1 分钟）：核对 `*_report.txt` 中"剔除异常后"的 D 值与粒级占比，导出图片。

## 9. 竞赛口径答疑（评分相关概念澄清）

本节回答"为什么这么做、依据是什么"这类问题，直接服务答辩与结果解释。

### 9.1 任务条文只写"粒径分布 D10/D50/D90"，为什么我们还要质量加权？

任务条文（`docs/task.md` 第 2 条）字面要求的是逐颗粒直径 + 粒径分布；但第 4 条规则明确
"评分维度：**以标准筛分结果为准**"。标准筛分按**质量**分档（每层筛上残留称重），其 D 值
天然是质量口径。若只交数量口径（每颗粒权重 1），与评分基准不同语义，粒径误差项会吃亏。
所以工程层**两种口径都输出**：数量口径满足任务字面，质量口径对标评分基准。

### 9.2 质量加权里的 d 是什么、怎么来？

`d` = 每个颗粒的**筛分等效粒径** `d_sieve = θ₁·b + θ₂·d_eq + θ₃`，默认 θ=(1,0,0) 即 b 轴。
来源链（全部来自 ImageGrains 的 CSV）：

```text
椭圆拟合 → b 轴(px) ─×res──→ b 轴(mm)      ← 默认 d
area(px²) ─×res²─→ 面积(mm²) ─2√(A/π)─→ d_eq(mm)   ← θ₂≠0 时才用
```

注意 `area` 列重缩放后仍是 px²（上游只缩放 a/b 轴），算 d_eq 必须自行乘 res²。

### 9.3 γ=3 是把颗粒当正方体吗？

不是。`w=d³` 是"体积 ∝ 线性尺寸³"的缩放定律，球、正方体、任何几何相似形状都满足，
比例常数在归一化权重时消掉。只要颗粒形状统计上不随尺寸变化，d³ 就等价于质量加权。
γ 可调（`--gamma`）正是为应对"形状随尺寸变化"或"需要贴合实测筛分"的情况。

### 9.4 bootstrap/CI 是不确定度是什么意思？需要多次拍照吗？

不需要多次拍照。模型对同一张图输出是确定的。`--unc_method` 等参数是对**已有的那一次测量
结果**做统计模拟（有放回重采样 n 次，`--n` 默认 1000），衡量"如果重新取样一批颗粒，D 值会
怎么波动"，输出 95% 置信区间（如 `CI(D50)=[7.8, 10.0]`）。颗粒越少、分布越散，区间越宽。
同一堆积多拍几张合并样本能降低波动，但那是提升样本代表性的问题，与 `--unc_*` 是两回事。

### 9.5 标准筛分得到的就是质量分布？

是的。标准筛分把骨料按筛孔分档并逐层称重，本身就是按粒径分档的质量直方图，可读出各粒级
质量占比并插值出质量口径 D10/D50/D90。评分对比的正是"我们的 D 值/粒级占比"vs"评委会的
称重结果"，所以工程层输出的粒级占比 + 质量 D 值与该格式一一对应。

### 9.6 校准实验必须在比赛现场做吗？

不是。现场只能拍照 + 跑模型输出预测（规则要求非人工/非传统方式，且评分方才有标准筛分结果）。
校准用的实测数据必须**赛前自备**：自采/自购骨料 → 称重 → 机械筛分 → 拍照测量 → 拟合 θ/γ。
这个实验是控制粒径误差评分项的关键，也是答辩里"数据处理与验证"最有说服力的素材。

### 9.7 形貌与异常检测是怎么做的？

当前都是**规则法**，基于 ImageGrains 已输出的几何量（长宽比/圆度/凸度），阈值可配置
（见 5.3/5.4 节）。形貌是投影形貌（无真实厚度）；泥团当前仅兜底规则（默认关闭），
真正的泥团识别需要图像 crop 的颜色/纹理分类器（TODO P1）。

## 10. 常见问题

- **模型找不到 / 提示下载**：`models/IG2_full_set_cp_SAM` 未放置或放错位置，见第 2 节。
- **`zsh: no matches found`**：shell 通配符问题，给参数加引号（如 `pip install -e '.[test]'`）。
- **"需要 --resolution"**：CSV 只有像素列，需手动给 `--resolution`；或改用 `*_re_scaled.csv`。
- **分辨率不知道**：图里有标尺则量出 mm/px；或用 ArUco 标定（TODO）；demo 数据固定为 0.39 mm/px。
- **报告里 D50 异常大**：多半是异物/大颗粒被质量权重放大，看"剔除异常后"一行。
- **图内中文变方块**：当前绘图使用英文字体（DejaVu 无中文字形），属预期。

## 11. 目录与文档导航

- `docs/task.md` 比赛任务原文；`docs/architecture.md` 架构；`docs/data-flow.md` 数据流。
- `docs/ai/PLAN.md` 实施计划；`docs/ai/HANDOFF.md` 当前交接；`docs/ai/TODO.md` 待办。
- 工程层源码：`src/aggregate_screening/`（sieve_equivalent / morphology / anomaly / report / app）。
- 测试：`tests/test_{sieve_equivalent,morphology,anomaly,report}.py`，`pytest tests/`。