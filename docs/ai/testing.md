# 测试与验证

本文档告诉 agent 在本仓库如何验证改动，避免误跑重型 GPU 推理。默认选择能覆盖改动行为的最小相关检查。

## 环境

- Python 版本：≥ 3.9（pyproject.toml 要求）；官方推荐 3.10。
- 安装：`pip install -e .[test]`（开发模式 + pytest）。
- 主要依赖：cellpose ≥ 4.0.1（含 PyTorch）、scikit-image、numpy ≤ 2.2、pandas、matplotlib、scanpy 等，见 `pyproject.toml`。
- GPU 推理建议（Cellpose-SAM 模型较大），但 CPU 也能运行。
- 主工作目录：仓库根目录。

```bash
pip install -e .[test]
```

## 默认策略

- 运行与你改动文件相关的最小验证命令。
- 报告你实际运行过的每条验证命令。
- 如果跳过验证，报告应运行的命令、跳过原因和剩余风险。
- 不要默认跑完整 Cellpose 推理、模型微调或全量 demo 处理，除非任务确实需要。
- 纯文档改动不需要跑 pytest；直接检查文件内容即可。

## 快速检查

小改动先做语法检查：

```bash
python -m compileall src tests
python -m compileall src/imagegrains/*.py
```

现有测试：

```bash
pytest tests/ -v
pytest tests/test_imagegrains.py -v
```

当前 `tests/test_imagegrains.py` 只有一个占位用例，收集应该为 1 passed；这是正常状态，不代表代码没有价值。

## 导入与安装自检

改动 import 结构、`__init__.py` 或打包配置后：

```bash
python -c "import imagegrains; print(imagegrains.__version__, imagegrains.__cp_version__)"
python -m imagegrains --help
```

`--help` 会打印全部 CLI 参数，正常退出即通过。

## 数据/CLI smoke（无需下载）

仓库自带 `demo_data/`（FH、K1 等），可作为不动真模型的最小数据检查。注意：CLI 完整流水线需要预训练模型（默认从 `~/imagegrains/models/` 读取或 `python -m imagegrains --download_data True` 下载），**离线环境不要运行完整流水线**。

无模型也能验证的步骤：

- 用 `--skip_segmentation` 配合已有 `_mask.tif` 测粒径步骤（需要 demo_data/FH 中的 mask 对）。
- `data_loader.load_from_folders` / `read_grains` 等纯文件读取函数可以用 `demo_data/` 数据在 Python 里直接调用验证。

## 单元测试

新增或修改 `src/imagegrains/` 下函数时，先在 `tests/` 补针对性的 pytest 用例，再跑：

```bash
pytest tests/test_imagegrains.py -v
```

测试应使用合成的 numpy 图像/掩膜或 `demo_data/`，避免引入模型推理依赖。

## Notebook 改动

`notebooks/` 改动通常只需检查 JSON 结构和执行逻辑；涉及核心函数时按上面的单元测试路径验证，不要求逐格执行（需要模型/GPU 环境）。

## 何时跑哪种检查

- 纯文档/注释改动：`git diff` 目检，不需要 pytest。
- 函数逻辑改动：补测试 + `pytest tests/`。
- CLI/入口改动：`python -m imagegrains --help` + 相关函数测试。
- 打包/import 改动：`pip install -e .[test]` + import 自检。
- 分割/测量效果类改动：需要模型与 GPU 时，说明资源要求，得到确认后再跑。

## 昂贵命令

以下命令非明确要求或必要时不运行：

```bash
python -m imagegrains --download_data True          # 下载模型与示例数据（大）
python -m imagegrains --img_dir <路径>               # 完整流水线（模型推理）
notebooks/4_train_cellposeSAM_model.ipynb 的训练流程   # 模型微调
```

## 已知注意事项

- 本地可能没有 `imagegrains` conda 环境或 GPU；先确认环境再决定跑不跑推理。
- 默认模型路径是 `~/imagegrains/models/`；没有下载模型时分割步骤会直接退出。
- `demo_data/` 属于演示数据，不要改动；测试只在只读方式下使用。
- Cellpose-SAM 首次推理会下载权重或加载本地模型，耗时且依赖网络；把这类验证显式声明为 smoke。
