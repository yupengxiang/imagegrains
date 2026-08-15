# 项目总览

这是新进入本仓库的 agent 的项目地图。内容应保持简短、事实化、稳定。短期的任务状态写在 `docs/ai/PLAN.md` 和 `docs/ai/HANDOFF.md`，不要写在这里。

## 项目身份

- 项目名：ImageGrains（2.0 分支）。
- 用途：为"混凝土骨料颗粒智能筛分比拼"（见 `docs/task.md`）服务。我们选择**自然堆积赛道**：对 5–40 mm 破碎骨料的自然堆积图像进行非人工视觉筛分。
- 上游：<https://github.com/dmair1989/imagegrains>，基于 Cellpose-SAM（cellpose ≥ 4.0.1）做颗粒实例分割，再测量粒径、形状并统计级配。
- 技术主线（参考 `docs/insight/` 中的 GPT 方案）：直接用上游预训练模型跑通 `图像 → 实例分割 → 几何测量 → D10/D50/D90`；比赛差异化的重点是把"视觉数量分布"校准成"接近标准筛分的质量分布"。

## 仓库结构

- `src/imagegrains/`：包主体（可 `pip install -e .` 安装）。
  - `__main__.py`：命令行入口，串起分割 → 重采样 → 粒径 → 尺度 → GSD 五步。
  - `segmentation_helper.py`：Cellpose 分割、模型加载、训练、评估。
  - `grainsizing.py`：mask 的几何测量（长短轴、面积、周长、形状指标）与 GSD 计算。
  - `gsd_uncertainty.py`：bootstrap / Monte Carlo 不确定度。
  - `data_loader.py`：数据与模型下载、目录扫描、结果读取。
  - `plotting.py`：可视化。
- `notebooks/`：官方工作流 notebook（分割/粒径/GSD/自定义训练），`cellpose_2_notebooks/` 为遗留。
- `models/`：上游预训练分割模型（`fh_boosted_1.170223`、`full_set_1.170223`）。
- `demo_data/`：官方 demo 图像与 mask（FH、K1 等）。
- `tests/`：pytest 测试（当前只有占位测试）。
- `docs/`：`task.md`（竞赛任务）、`ai/`（agent 持久上下文）、`insight/`（GPT 研究笔记，gitignored）、`assets/`。
- `.github/workflows/`：CI（pytest）与 PyPI 发布。

竞赛工程层（相机标定、筛分等效粒径、形貌分类、异常检测、报告界面等）尚未落地；开发时应优先复用 `src/imagegrains/` 现有函数，避免重造轮子。

## 竞赛要求（自然堆积赛道）

- 精细识别：检测与实例分割，区分颗粒与背景、颗粒与颗粒的粘连。
- 粒径分析：输出可见颗粒直径（或长短径），统计 D10/D50/D90。
- 形状分类（可选加分）：针片状、圆形、棱角状。
- 异常检测：>50 mm 大块异物、泥团等非骨料物质。
- 现场图像采集与调试 ≤30 分钟；评分以标准筛分结果为准（粒径误差、识别准确率、创新性、答辩）。

## 数据假设

- 输入：单张或多张骨料图像（jpg/tif/png），可选 `demo_data/` 或自采数据。
- 中间产物：`*_mask.tif`（实例 mask）、`*_grains.csv`（逐颗粒几何测量，`ell: b-axis (px/mm)` 为粒径列）、GSD 汇总 CSV。
- 尺度：像素 → mm 通过 `--resolution`（mm/px 数值或按图像列出的 CSV）或相机参数（`grainsizing.calculate_camera_res`）完成。
- 不假设视频/时序输入；自然堆积是静态图像场景。

## 当前研发优先级

- 跑通官方工作流（CLI 或 notebook）并验证 `demo_data`。
- 评估上游预训练模型在骨料图像上的分割质量，决定是否需要微调。
- 实现比赛工程层：尺度标定 → 几何测量 → **筛分等效粒径 + 质量加权分布** → D10/D50/D90 → 形貌/异常 → 报告。
- 建立以标准筛分结果为基准的验收指标（D10/D50/D90 误差、级配曲线误差）。

## 非目标

- 不实现传送带视频实时跟踪、多目标跟踪去重等动态场景能力（除非赛道变更）。
- 不重新训练 Cellpose-SAM 基础模型，除非预训练模型在骨料上明显不够用。
- 不做含泥量的定量回归（赛题未要求，泥团只作为异常类别处理）。
- 不维护上游无关的通用能力（三维 CT 分割等按需再议）。
