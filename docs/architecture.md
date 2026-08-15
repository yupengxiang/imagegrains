# 架构

本仓库是 ImageGrains 2.0 的竞赛 fork：一个基于 Cellpose-SAM 的图像颗粒分割与测量库，服务于"混凝土骨料颗粒智能筛分比拼"（自然堆积赛道，见 `docs/task.md`）。上游代码保持原样作为基线，竞赛工程能力在其上增量开发。

## 运行主线

```text
图像目录
  -> segmentation_helper（Cellpose-SAM 实例分割）
  -> *_mask.tif（实例标签图）
  -> grainsizing（几何测量：长短轴/面积/周长/形状指标）
  -> *_grains.csv
  -> grainsizing + gsd_uncertainty（GSD 与不确定度）
  -> *_gsd.csv / *_perc_uncert.txt
  -> plotting（结果图）
```

CLI 入口是 `src/imagegrains/__main__.py`（`python -m imagegrains`），只负责按参数串联这些模块。详细的数据形状与文件命名见 [data-flow.md](data-flow.md)。

## 模块划分

| 模块 | 职责 |
| --- | --- |
| `segmentation_helper.py` | Cellpose 模型加载（`models_from_zoo`）、单张/批量预测（`predict_single_image`/`predict_folder`/`predict_dataset`）、两尺度合并（`combine_preds` 系列）、自定义训练（`custom_train`）、预测评估（`eval_set` 系列） |
| `grainsizing.py` | mask 几何属性（`ell_stats`）、长短轴拟合（`fit_grain_axes`）、形状指标（`isoperimetric_ratios`）、过滤（`filter_grains`）、重采样（`resample_masks`）、尺度换算（`scale_grains`/`calculate_camera_res`）、GSD（`do_gsd`/`gsd_for_set`） |
| `gsd_uncertainty.py` | 粒径分布不确定度：bootstrap（`bootstrapping`）、Monte Carlo（`MC_with_length_scale`）、解析区间（`QuantBD` 等） |
| `data_loader.py` | 数据/模型下载（`download_files`）、目录扫描与配对（`find_data`）、结果文件读取（`read_grains`/`gsds_from_folder` 等） |
| `plotting.py` | 可视化：mask 覆盖、单颗粒椭圆与轴、GSD 曲线、不确定度带、训练集/评估图 |
| `__main__.py` | argparse 入口，串联分割 → 重采样 → 粒径 → 尺度 → GSD 五步 |

模块之间通过显式 import 协作（`from imagegrains import ...`），不存在注册表或隐藏的全局副作用。

## 数据契约

- 输入：图像（jpg/tif/png）+ 可选已知 mask；输出：`*_mask.tif`、`*_grains.csv`、`*_gsd.csv`、`*_perc_uncert.txt`、绘图。
- 逐颗粒测量一行一颗颗粒；粒径核心列为 `ell: b-axis (px)`，尺度化后为 `ell: b-axis (mm)`。
- 过滤参数为 `filters = {'edge': [bool, val], 'px_cutoff': [bool, val]}` 字典。
- 尺度换算统一到 mm/px（数值或按图像 CSV，或由相机参数计算）。
- 竞赛口径（质量加权分布、筛分等效粒径）是对 `*_grains.csv` 的后续加工，尚未实现。

## 关键依赖

- cellpose ≥ 4.0.1（Cellpose-SAM，内部依赖 PyTorch）；分割是唯一的重型计算。
- scikit-image（regionprops 几何属性）、pandas/numpy（CSV）、matplotlib（绘图）、scanpy/opentsne/leidenalg（形状聚类等可选分析）。
- GPU 建议启用（`--gpu True`），无 GPU 时退回 CPU。

## 失败边界

- CLI 对无效输入目录直接提示并退出；模型缺失时提示重新下载并退出（`__main__.py`）。
- 分割/测量以 Cellpose 与 skimage 的异常为最终边界，不包装成自定义错误体系。
- 上游代码无版本化输出目录的强约定：`--out_dir` 未指定时结果写到输入目录；跑新数据前清理旧结果文件（CLI 帮助中已注明）。

## 竞赛工程层（待开发）

自然堆积赛道的差异化能力作为**独立新模块**增量开发，不修改上游源码：

- 尺度标定：ArUco/标尺检测、homography 透视校正、mm/px 自动换算；
- 筛分等效粒径：2D 投影几何（a/b、等效直径、圆度等）→ 方孔筛等效粒径的校准映射；
- 质量加权分布：`wᵢ = dᵢ^γ` 聚合 → D10/D50/D90 与级配曲线（评分以标准筛分为基准）；
- 形貌分类（针片状/圆形/棱角状）与异常检测（>50 mm、泥团）；
- 一键式本地应用与自动 QC（现场 30 分钟约束）。

实施顺序与验收口径见 `docs/ai/PLAN.md`；方向性建议见 `docs/insight/`（gitignored，仅供参考）。
