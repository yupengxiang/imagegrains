"""aggregate_screening: 竞赛工程层。

在 ImageGrains 2.0 的上游工作流之上，提供自然堆积赛道所需的
筛分等效粒径、质量加权分布、形貌分类与异常检测能力。

模块：
- sieve_equivalent: 视觉几何 -> 筛分等效粒径 -> 质量加权分布 -> D10/D50/D90
- morphology:      形貌分类（针片状/圆形/棱角状，规则法）
- anomaly:         异常检测（>50mm 异物、泥团/非骨料、噪声过滤）
- report:          场景级汇总报告与消融对照
- app:             一键 CLI 入口
"""

from . import sieve_equivalent, morphology, anomaly, report

__all__ = ["sieve_equivalent", "morphology", "anomaly", "report"]
