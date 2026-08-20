# 架构

本仓库是 ImageGrains 2.0 的竞赛 fork：基于 Cellpose-SAM 的颗粒分割与测量库，服务"混凝土骨料颗粒智能筛分比拼"（自然堆积赛道，见 `docs/task.md`）。上游代码保持原样作为基线，竞赛能力增量开发。

## 运行主线

```text
图像目录
  -> segmentation_helper（Cellpose-SAM 实例分割）
  -> *_mask.tif
  -> grainsizing（几何测量：长短轴/面积/周长/形状）
  -> *_grains.csv
  -> grainsizing + gsd_uncertainty（GSD 与不确定度）
  -> *_gsd.csv / *_perc_uncert.txt
  -> plotting
```

CLI 入口 `src/imagegrains/__main__.py`（`python -m imagegrains`）串联上述模块。文件命名见 [data-flow.md](data-flow.md)。

## 模块划分

| 模块 | 职责 |
| --- | --- |
| `segmentation_helper.py` | 模型加载（`models_from_zoo`）、预测（`predict_*`）、两尺度合并（`combine_preds`）、训练/评估 |
| `grainsizing.py` | 几何属性（`ell_stats`）、轴拟合（`fit_grain_axes`）、形状指标、过滤、重采样、尺度（`scale_grains`）、GSD（`do_gsd`） |
| `gsd_uncertainty.py` | bootstrap / Monte Carlo 不确定度 |
| `data_loader.py` | 目录扫描与配对（`find_data`）、结果读取 |
| `plotting.py` | 可视化 |
| `__main__.py` | 串联分割→重采样→粒径→尺度→GSD 五步 |

显式 `from imagegrains import ...` 协作，无隐藏全局状态。

## 数据契约

- 输入：图像（jpg/tif/png）+ 可选 mask；输出：`*_mask.tif`、`*_grains.csv`、`*_gsd.csv` 等。
- 逐颗粒一行；粒径列 `ell: b-axis (px)` / `(mm)`，列名单一来源 `src/aggregate_screening/_columns.py`。
- 过滤：`filters = {'edge': [bool,val], 'px_cutoff': [bool,val]}`。
- 尺度统一到 mm/px；竞赛口径（`SieveAnalysis` 质量加权 + `SceneSummary` 剔除异常后）是对 `*_grains.csv` 的后续加工，已实现。

## 关键依赖

- cellpose ≥4.0.1（Cellpose-SAM，含 PyTorch）、scikit-image、pandas/numpy、matplotlib、scipy（`differential_evolution`）、scanpy 等。GPU 建议。

## 失败边界

- 无效目录/缺模型时 CLI 直接提示退出；分割/测量以 Cellpose/skimage 异常为边界。

## 竞赛工程层（`src/aggregate_screening/`）

独立子包，不改上游：

| 模块 | 职责 |
| --- | --- |
| `_columns.py` | 列名单一来源 |
| `sieve_equivalent.py` | `SieveAnalysis`/`CalibrationResult`：`d=θ₁b+θ₂d_eq+θ₃`（默认 b 轴）、`w=d^γ`（γ=3）、阶梯逆 D10/50/90、粒级 dict、`fit_calibration`（差分进化）、`load_grains_csv`/`infer_resolution`/`normalize_grains` |
| `morphology.py` | `MorphThresholds` 规则法：长宽比/圆度/凸度 → 针片状/圆形/棱角状/普通 |
| `anomaly.py` | `NORMAL_MIN/MAX, FOREIGN_MIN, MUD_BAND`：>50 异物、<5 噪声、疑似泥团 |
| `report.py` | `SceneSummary`/`NormalOnly`：数量 vs 质量对照、粒级 dict、形貌/异常、文本/JSON、消融表（`scene_summary` 返回 `(summary,df_final)`） |
| `app.py` | 一键 CLI `python -m aggregate_screening --grains ...`（懒加载绘图，无 CSV 回读） |

输入为 `*_grains.csv`（`load_grains_csv`→`infer_resolution`→`normalize_grains`，mm/px 双列自动推断）。核心口径：**质量加权 + 剔除异常后正常骨料**，对标标准筛分。

### 校准流程（需真实筛分数据）

```text
自采 batch（称重+机械筛分→D10/50/90 真值 + 拍照→*_grains.csv）
  -> fit_calibration(batches, targets) -> theta/gamma -> 报告与消融
```

详见 `docs/USAGE.md` 第6节。
