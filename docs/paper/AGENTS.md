# Paper Editing Instructions

These instructions apply to all work under `docs/paper/`.

Before editing the technical report:

1. Read `../ai/HANDOFF.md` for the current evidence set and submission state.
2. Read `../ai/DECISIONS.md` for fixed technical and evidence-boundary decisions.
3. Read `../ai/report-writing-skill/SKILL.md` and use it as the editing rubric.
4. Treat `main.tex` as the only canonical report entrypoint.

Do not recreate `main_submission.tex` or `main_v2.tex`.

The current report is a final-evidence competition technical report. Do not introduce placeholders for future mechanical-sieving experiments, manual instance annotations, or other data that the project has decided not to collect for this submission.

Preserve facts, numerical results, equations, BibTeX keys, labels, units, and the distinction between reused ImageGrains 2.0 / Cellpose-SAM capability and this project's contribution.

After substantive edits, compile `main.tex` and verify:

- no unresolved references or citations;
- no material Overfull boxes;
- cover, abstract, TOC, references, and appendix remain present;
- figures and tables are not clipped or overlapping;
- conclusions remain within the current evidence scope.
