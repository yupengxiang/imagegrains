# 数据流

本文档只描述当前代码路径。阅读时从输入图像目录开始，不要从某个绘图函数或 CSV 后处理反向猜测数据含义。

## 1. 输入与文件约定

输入是一组图像（默认 jpg；`--img_type` 可选 tif/tiff/png）所在目录。图像与 mask 同名配对：mask 文件 = 图像文件名 + `_mask` + `.tif`（`data_loader.find_data`）。

中间与输出产物约定：

| 产物 | 命名模式 | 内容 |
| --- | --- | --- |
| 分割 mask | `*_mask.tif` | 逐颗粒实例标签图 |
| 逐颗粒测量 | `*_grains.csv` | 每颗粒一行：长短轴、面积、周长、形状指标 |
| GSD 汇总 | `*_gsd.csv` | 粒径百分位曲线 |
| 不确定度 | `*_perc_uncert.txt` | 各百分位的置信区间 |
| 覆盖图/汇总图 | `*.png` | mask 覆盖、颗粒椭圆、GSD 曲线 |

核心粒径列名：无尺度时为 `ell: b-axis (px)`，尺度化后为 `ell: b-axis (mm)`（`data_loader.read_grains`）。

## 2. 主流程

```text
图像目录 (jpg/tif/png)
  -> Cellpose-SAM 分割 (segmentation_helper.predict_folder / predict_dataset)
  -> *_mask.tif（实例标签图）
  -> [可选] 重采样 (grainsizing.resample_masks：grid/random/centerpoint) -> 子目录
  -> 几何测量 (grainsizing.batch_grainsize / grains_from_masks)
  -> *_grains.csv（像素单位 + 形状指标）
  -> [可选] 尺度换算 (grainsizing.scale_grains / re_scale_dataset)
  -> *_grains.csv（mm 单位）
  -> GSD 计算 (grainsizing.do_gsd / gsd_for_set)
  -> *_gsd.csv
  -> 不确定度 (gsd_uncertainty：bootstrapping / MC / MC_SfM)
  -> *_perc_uncert.txt
  -> 绘图 (plotting)
```

CLI 入口 `python -m imagegrains --img_dir <目录>` 依次执行：分割 → 重采样 → 粒径测量 → 尺度 → GSD/不确定度；各步可跳过（`--skip_segmentation`、`--skip_grainsize`）。

## 3. 分割（Cellpose-SAM）

`segmentation_helper.py` 负责模型加载与预测：

- `models_from_zoo`：加载 `models/` 下或用户指定的 Cellpose 模型；
- `predict_folder` / `predict_dataset`：批量预测并保存 `*_mask.tif`；
- `predict_single_image`：单张预测，可用 `diameter` 控制颗粒尺度；
- `combine_preds` / `combine_2D` / `combine_3D`：两尺度预测合并（`--second_diameter`）；
- `check_labels` / `eval_image` / `eval_set`：对标注集做评估（预测与真值 mask 对比）。

分割输出是实例标签图（每个颗粒一个 label 值），这是下游所有测量的唯一输入。

## 4. 重采样（可选）

`grainsizing.resample_masks` 按 `method` 从 mask 中选择子集：

- `wolman`：数字 Wolman 网格；
- `random` / `centerpoint`：随机点或图像中心点采样（`--random_resample` / `--centerpoint_resample`）。

重采样结果写入独立子目录，后续粒径测量在子目录上再跑一遍。比赛场景一般不使用重采样（全量测量），保留为地质统计选项。

## 5. 几何测量

`grainsizing.batch_grainsize` / `grains_from_masks` 对每个 mask 提取（`ell_stats`，skimage regionprops）：

```text
label, area, area_convex, perimeter_crofton, orientation,
minor_axis_length, major_axis_length, solidity, eccentricity,
centroid, local_centroid, bbox
```

然后拟合颗粒轴（`fit_grain_axes`，默认 convex_hull；可选 mask_outline）得到更稳健的长短轴，并计算：

- 形状指标：`isoperimetric_ratios`（IR/IRn）、椭圆 a/b 轴；
- 过滤：`filter_grains` 按 `filters` 字典（`edge` 边界过滤、`px_cutoff` 最小粒径）剔除边缘截断颗粒与过小噪声。

输出 `*_grains.csv`：一行为一颗颗粒，含面积、周长、长短轴（px）、离心率、凸度等。

## 6. 尺度换算

`grainsizing.scale_grains` 把像素测量换算为 mm：

- `resolution` 为单个 mm/px 数值（全图统一）；
- 或按图像列出分辨率的 CSV（`--resolution <csv路径>`）；
- 或相机参数：`calculate_camera_res(focal_length_mm, height_m, sensorH_mm, sensorW_mm, pixelsH, pixelsW)`。

换算后列名变为 `ell: b-axis (mm)` 等，`re_scale_dataset` 批量处理一个数据集。

## 7. GSD 与不确定度

`grainsizing.do_gsd` 从单张图颗粒尺寸构造累计粒径分布；`gsd_for_set` 汇总多张图；`get_key_percs` 取指定百分位。

`gsd_uncertainty.py` 提供百分位不确定度：

- `bootstrapping`（默认）：对颗粒集合重采样；
- `MC_with_length_scale`：Monte Carlo，注入尺度误差 `scale_err` 与长度误差 `length_err`；
- `QuantBD` / `p_c_fripp` / `pbinom_diff`：解析置信区间（用于 SfM 数据）。

结果写入 `*_gsd.csv`（各百分位粒径）与 `*_perc_uncert.txt`（95% 区间等）。

## 8. 竞赛扩展点

当前主流程直接复用即可得到：逐颗粒 a/b 轴、面积、周长、形状指标 → 数量分布。竞赛要求的"筛分等效粒径 + 质量加权分布（wᵢ=dᵢ^γ）+ D10/D50/D90"是**在 `*_grains.csv` 之上的后续加工**，对应新的独立模块（见 `docs/ai/PLAN.md`），不修改本节描述的上游路径。

## 建议阅读顺序

```text
docs/task.md
  -> src/imagegrains/__main__.py（入口与参数）
  -> src/imagegrains/segmentation_helper.py
  -> src/imagegrains/grainsizing.py（batch_grainsize -> ell_stats -> fit_grain_axes -> scale_grains -> do_gsd）
  -> src/imagegrains/gsd_uncertainty.py
  -> src/imagegrains/data_loader.py（文件命名与读取约定）
```
