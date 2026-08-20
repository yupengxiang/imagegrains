# 数据流

> 从输入图像目录正向阅读，勿从绘图/CSV 反推含义。

## 1. 输入与约定

图像目录（jpg/tif/png），mask 同名配对：`图像名 + _mask + .tif`（`data_loader.find_data`）。

| 产物 | 命名 | 内容 |
| --- | --- | --- |
| mask | `*_mask.tif` | 实例标签图 |
| 逐颗粒测量 | `*_grains.csv` | 长短轴/面积/周长/形状（一行一颗） |
| GSD | `*_gsd.csv` | 百分位曲线 |
| 不确定度 | `*_perc_uncert.txt` | 置信区间 |
| 图 | `*.png` | 覆盖/椭圆/GSD 曲线 |

粒径列：`ell: b-axis (px)` → 尺度化后 `ell: b-axis (mm)`，定义见 `_columns.py`。

## 2. 主流程

```text
图像目录
  -> Cellpose-SAM 分割 -> *_mask.tif
  -> [可选] 重采样（grid/random/centerpoint）-> 子目录
  -> 几何测量（batch_grainsize / grains_from_masks）-> *_grains.csv（px）
  -> [可选] 尺度换算（scale_grains / re_scale_dataset）-> *_grains.csv（mm）
  -> GSD（do_gsd / gsd_for_set）-> *_gsd.csv
  -> 不确定度（bootstrapping / MC）-> *_perc_uncert.txt
  -> 绘图
```

入口 `python -m imagegrains --img_dir <目录>` 依次执行五步，可 `--skip_segmentation/skip_grainsize` 跳过。

## 3. 分割

`segmentation_helper`：`models_from_zoo` 加载模型、`predict_folder/dataset` 批量、`combine_preds` 两尺度合并、`eval_set` 评估。输出实例标签图。

## 4. 重采样（可选）

`resample_masks`：`wolman` / `random` / `centerpoint`。比赛一般全量测量，不使用。

## 5. 几何测量

`batch_grainsize` / `grains_from_masks` 经 `ell_stats`（regionprops）提取 label/area/area_convex/perimeter/orientation 等，再经 `fit_grain_axes` 拟合长短轴，`filter_grains` 按 `filters` 剔边缘/过小。

## 6. 尺度换算

`scale_grains` 支持：单个 mm/px、按图像 CSV、或相机参数 `calculate_camera_res(...)`。换算后列名变 `ell: b-axis (mm)`。

## 7. GSD 与不确定度

`do_gsd` / `gsd_for_set` 构造累计分布；`gsd_uncertainty` 提供 bootstrap/MC/解析区间，写入 `*_gsd.csv` / `*_perc_uncert.txt`。

## 8. 竞赛扩展（`src/aggregate_screening/`）

在 `*_grains.csv` 之上继续加工，不改上游：

```text
*_grains.csv（px 或 mm）
  -> load_grains_csv -> infer_resolution（mm/px 中位数）-> normalize_grains（b_mm/a_mm/area_px/d_eq_mm）
  -> d = θ₁·b + θ₂·d_eq + θ₃（默认 b 轴）
  -> w = d^γ（默认 3）
  -> D10/50/90 + 粒级 dict（5-10/.../31.5-40 含 <5/>40）
  -> morphology + anomaly（>50/<5/疑似泥团）
  -> report.scene_summary -> (SceneSummary, df_final) -> 文本/JSON/对比图
```

质量加权对标标准筛分；`fit_calibration` 用自采真值拟合 θ/γ。见 `architecture.md` 竞赛层。

## 阅读顺序

```text
docs/task.md -> src/imagegrains/__main__.py -> segmentation_helper.py -> grainsizing.py -> gsd_uncertainty.py -> data_loader.py -> src/aggregate_screening/*
```
