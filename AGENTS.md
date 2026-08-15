# Agent Instructions


## Repository scope

This repository is the ImageGrains 2.0 codebase, forked for the "混凝土骨料颗粒智能筛分比拼" competition (natural stacking track, see `docs/task.md`). It segments and measures aggregate/grain particles in images using Cellpose-SAM.

This is a real Python package (see `pyproject.toml`, installable via `pip install -e .[test]`). The upstream project is <https://github.com/dmair1989/imagegrains>.

Do not edit generated files, cache files, model weights, demo data, or large binary artifacts unless explicitly requested.


## Persistent AI Context

The `docs/ai/` directory stores persistent context for multi-agent and multi-model workflows.

Use these files as follows:

- `docs/ai/project-overview.md`
  Project background, repository structure, competition requirements, model/data assumptions, and high-level goals.

- `docs/ai/coding-style.md`
  Coding conventions, naming rules, typing expectations, module organization, and interface style.

- `docs/ai/testing.md`
  Validation commands, test commands, smoke tests, and expected verification workflow.

- `docs/ai/workflow.md`
  Multi-model workflow, planner/executor/reviewer roles, and handoff behavior.

- `docs/ai/PLAN.md`
  Current task plan. Read this before implementing a planned change. If it conflicts with the actual code, stop and report the inconsistency.

- `docs/ai/HANDOFF.md`
  Current handoff state. Read this when continuing previous work or when another agent/model worked on the task before.

- `docs/ai/DECISIONS.md`
  Persistent technical decisions. Read this before making architecture-level, interface-level, or configuration-schema decisions.

- `docs/ai/TODO.md`
  Follow-up tasks. TODO items are not automatic permission to make broad changes.

- `docs/task.md`
  The competition task text (the requirements this repository serves). Read it when any change touches competition-relevant behavior.

- `docs/insight/`
  Local, gitignored research notes: GPT-suggested datasets, papers, and the competition technical plan. Reference material only, not an executable spec.

- `docs/data-flow.md` and `docs/architecture.md`
  Current image-processing data flow and module architecture. Read these before changing pipeline behavior.


## Task Routing

When continuing previous work:

1. Read `docs/ai/HANDOFF.md`.
2. Read `docs/ai/PLAN.md`.
3. Inspect `git status` and `git diff`.
4. Continue from the documented state instead of restarting the task.

When implementing a planned change:

1. Read `docs/ai/PLAN.md`.
2. Read `docs/ai/coding-style.md`.
3. Read `docs/ai/testing.md`.
4. Implement only the current planned step.

When designing or reviewing an approach:

1. Read `docs/ai/project-overview.md`.
2. Read `docs/ai/DECISIONS.md`.
3. Produce analysis or a plan first.
4. Do not modify code unless implementation is requested.

When fixing a bug:

1. Localize or reproduce the issue when possible.
2. Inspect the smallest relevant code path.
3. Make the minimal fix.
4. Run the smallest relevant validation command.
5. Update `docs/ai/HANDOFF.md` if the task remains unfinished.


## Project-Specific Constraints

Do not change public interfaces, CLI options, module function signatures, or output formats without explaining the compatibility impact.

Do not introduce new heavy dependencies unless explicitly confirmed.

Do not rename files, modules, classes, or public functions unless the task explicitly requires it.

Preserve existing behavior unless the task asks for a behavior change.

For research-code changes, prefer correctness, traceability, and reproducibility over clever abstractions.

Competition-specific constraints:

- Our track is the natural stacking (自然堆积) scene; do not design for the conveyor belt (传送带) scene unless explicitly asked.
- The scoring baseline is standard sieve analysis; mass-weighted size distribution matters more than raw per-particle counts.
- Plan for a ≤30 minute on-site capture/setup window and a one-click local application, not a jupyter-heavy demo.


## Validation Protocol

Before reporting completion, run the smallest relevant validation command from `docs/ai/testing.md`.

If validation cannot be run, report:

- the command that should have been run;
- why it was not run;
- what risk remains.


## Handoff Protocol

Before switching agents, ending a substantial task, or leaving work unfinished, update `docs/ai/HANDOFF.md` with:

- current task goal;
- completed steps;
- files changed;
- important decisions;
- validation commands run;
- known issues;
- next recommended step.

Keep `docs/ai/PLAN.md` aligned with the actual implementation state.


## Rules

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
