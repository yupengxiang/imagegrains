---
name: aggregate-competition-report-editor
description: Revise the Chinese technical report for the concrete aggregate intelligent sieving competition. Reduce formulaic AI-style prose, strengthen argument flow, preserve evidence and LaTeX structure, and write for technical judges rather than for a generic academic audience.
---

# Aggregate Competition Report Editor

## 1. Purpose

Use this skill whenever editing `docs/paper/main.tex` or files under `docs/paper/reviewer/`.

The target is a concise, credible Chinese technical report for competition judges. The report should read as the work of an engineering team that understands the problem, made explicit design choices, implemented a complete system, and knows exactly what its current evidence does and does not support.

This skill improves writing quality and authorial voice. It is not a detector-evasion workflow.

## 2. Reader and narrative

Primary reader: technical judges who may not know the repository or the development history.

The report should answer, in order:

1. What makes natural-pile visual sieving difficult?
2. Why was this technical route chosen?
3. How does an image become particle-level physical measurements?
4. How are visual measurements converted into grading statistics?
5. What do the current real-image results actually show?
6. How is the system operated within the competition workflow?
7. What are the method's physical and evidential boundaries?

Do not write the paper as a reply to an invisible questioner. It must stand alone.

## 3. Evidence invariants

Never change or strengthen the following without new evidence in the repository:

- The current real-image evidence set contains three demonstration scenes: `agg_001`, `agg_005`, and `agg_029`.
- Current scene outputs are functional/behavioral evidence, not paired mechanical-sieving accuracy evidence.
- No paired mechanical-sieving ground truth is claimed in the final report.
- The current scale used by the demonstrations is about 0.208 mm/px.
- The current sieve-equivalent baseline uses `theta=(1,0,0)`, i.e. the short-axis baseline.
- The current mass proxy uses `w=d^gamma` with `gamma=3` as a geometric prior, not direct weighing.
- `D10/D50/D90` reported from the current pipeline are visual mass-proxy grading statistics.
- Projected-shape rules describe 2D projection morphology; they are not a 3D specification-grade needle/flaky test.
- Mud detection is a geometric candidate rule, not a validated material classifier.
- The contest-layer synthetic test suite currently contains 27 passing tests; this supports implementation consistency, not empirical field accuracy.
- Existing runtime records are component/prototype timing, not a completed independent proof of the whole 30 min field procedure.

Preserve all numerical values, equations, BibTeX keys, labels, cross-references, filenames, model names, and units unless the source data or code supports a change.

## 4. Contribution boundary

Keep reused capability and project contribution distinct.

Reused foundation:

- ImageGrains 2.0 / Cellpose-SAM pretrained instance segmentation.

Project contribution:

- aggregate-domain image-to-physical-measurement chain;
- explicit and interpretable visual-size to grading-statistics mapping;
- mass-proxy statistics aligned with mass-based sieving semantics;
- integrated sizing, projected morphology, anomaly screening, reporting, and deployment workflow.

Do not imply that Cellpose-SAM or ImageGrains 2.0 was developed by this project.

## 5. Terminology lock

Prefer these terms consistently:

- `实例分割` for the concrete segmentation operation; `实例感知` only when referring to the broader perception stage.
- `毫米级几何量` for calibrated particle geometry.
- `筛分等效粒径` for the mapped particle size variable `d`.
- `质量代理` and `质量代理级配` for statistics based on `w=d^gamma`.
- `数量分布` for unweighted particle-count statistics.
- `投影形貌` for 2D shape categories.
- `异常候选` for rule-triggered oversized, undersized, or mud-like targets.
- `当前证据` or `本文证据` instead of `真值不足` repeated throughout the paper.

Do not rotate synonyms merely for stylistic variety when they denote the same technical object.

## 6. Natural Chinese academic style

### 6.1 Write statements, not service language

Delete or rewrite phrases that sound like an assistant explaining itself:

- `这里需要强调的是`
- `值得注意的是`
- `需要指出的是`
- `可以看到`
- `不难发现`
- `换句话说`
- `为了让评委理解`
- `下面将介绍`
- `本文接下来`

State the fact or inference directly.

### 6.2 Remove defensive prose

Avoid repeated structures such as:

- `并不是……而是……`
- `不等于……`
- `并非本文声称……`
- `不能说明……`
- `这里并不意味着……`

When a boundary matters, state the positive scope once:

Bad: `这并不能说明系统已经达到机械筛分精度。`

Better: `本文据此评价系统的端到端可运行性和统计行为；机械筛分绝对误差不在当前证据范围内。`

Do not repeat the same evidence disclaimer in every section.

### 6.3 Prefer concrete subjects and ordinary verbs

Prefer:

- `系统输出……`
- `三组样本显示……`
- `质量代理使粗颗粒获得更高权重……`
- `尺度误差会整体平移粒径分布……`

Avoid inflated wrappers such as:

- `充分体现了`
- `有力证明了`
- `进一步彰显了`
- `实现了对……的有效赋能`
- `构建了完整闭环`
- `具有重要意义`
- `显著提升` without a measured comparison.

Use `是、有、用、由、导致、取决于、显示、得到、增加、减少` when they are sufficient.

### 6.4 Keep paragraph rhythm human

Do not make every paragraph the same length or every sentence the same cadence.

- One paragraph should carry one argument, not one sentence.
- Keep some long technical sentences where relations belong together.
- Use short sentences only when they sharpen a conclusion.
- Avoid a sequence of identical sentence openings such as `首先/其次/此外/最后`.
- Use transitions only when the logical relation is not already obvious.

### 6.5 Avoid outline-shaped prose

Bullets and tables are useful for parameters, mappings, procedures, and comparisons. They should not replace argumentation.

A method paragraph should normally follow:

`motivation -> definition -> equation/operation -> parameter meaning -> consequence`.

A results paragraph should normally follow:

`observation -> numerical evidence -> mechanism/interpretation -> implication`.

A limitation paragraph should normally follow:

`condition -> source of error -> direction of impact -> practical boundary`.

## 7. Section-specific editing rules

### Abstract

Use one compact narrative:

`problem -> method -> current evidence -> principal finding -> evidence scope`.

Do not list contributions mechanically. Do not advertise the system. Do not mention repository implementation details unless essential to reproducibility.

### Problem definition / introduction

Focus on the competition task, the three semantic gaps, and the paper's contribution. Keep code, thresholds, CLI details, and calibration implementation out of this section.

### Framework

Compare routes only to justify the selected architecture. Avoid straw-man comparisons. The architecture diagram must depict what the final system actually executes, not experiments that were never performed.

### Visual measurement

Explain why the measurement is physically meaningful. Separate scale error, segmentation error, and projection limitations. Treat ImageGrains 2.0 / Cellpose-SAM as a reused foundation.

### Grading mapping

This is the technical core. Preserve the chain:

`2D geometry != sieve passage -> define sieve-equivalent size -> count != mass -> define mass proxy -> weighted CDF -> grading statistics`.

For `theta=(1,0,0)` and `gamma=3`, explain why they are transparent baseline assumptions. Do not present them as experimentally calibrated truth.

### Results

Report numbers before interpretation. Keep statements proportional to the evidence.

Especially preserve the count-vs-mass comparison because it demonstrates a real semantic effect using the existing data. Do not convert this result into a claim that `gamma=3` is mechanically accurate.

### Deployment

Prefer concrete operations, checks, thresholds, and recovery actions over generic engineering adjectives. The 30 min SOP is an operating plan; wording must distinguish target budget from measured component timing.

### Limitations / evidence boundary

Keep this concise. Group related limitations rather than repeating disclaimers from previous sections. The goal is to tell judges where the method works and where interpretation becomes uncertain.

### Conclusion

Restate the technical contribution and the strongest observed results. Do not add a future-work shopping list. Do not end with promotional claims.

## 8. Revision workflow

For a substantial paper revision:

1. Read the entire target section before editing.
2. Identify each paragraph's function in 3-8 words.
3. Remove duplicate paragraph functions.
4. Lock facts, numbers, equations, citations, labels, and terminology.
5. Rewrite for argument flow rather than sentence-by-sentence synonym replacement.
6. Remove assistant-like signposting, defensive language, inflated claims, and repeated evidence disclaimers.
7. Check that every quantitative interpretation points to an actual table, figure, or repository output.
8. Check transitions to the previous and next section.
9. Compile `docs/paper/main.tex` with XeLaTeX/BibTeX.
10. Reject the revision if it introduces unresolved references, citations, clipped figures, or material overfull boxes.

## 9. Final self-check

Before committing a revised section, answer yes to all of the following:

- Does the first paragraph start from the section's technical problem rather than generic background?
- Does every paragraph have a distinct argumentative job?
- Are claim strength and evidence strength aligned?
- Are reused work and project contribution clearly separated?
- Are technical terms stable across sections?
- Are numbers, units, citations, equations, and LaTeX references preserved?
- Have repeated `值得注意/需要指出/可以看到/此外/综上` patterns been removed?
- Have defensive `不是X而是Y` patterns been reduced to genuinely necessary distinctions?
- Does the prose contain specific mechanisms and observations rather than generic praise?
- Can the section be read without knowing the chat history?
- Does the ending create a reason for the next section rather than announce it mechanically?
