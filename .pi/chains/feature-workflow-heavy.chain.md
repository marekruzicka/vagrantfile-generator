---
name: feature-workflow-heavy
description: Heavy feature implementation: scout → context-builder → planner → worker → 3 parallel reviewers → 2 parallel validators
---

## scout
phase: Context
label: Quick map
model: deepseek-v4-flash:off
as: scoutContext
output: context-build/00-scout-map.md

{task}

Skip `.pi/plans/` and `.pi/` (except agents/settings) — orchestration artifacts, not source code.
This is a quick initial map. Focus on entry points, key files, and architecture. The context-builder will do the deep analysis.

## context-builder
phase: Context
label: Deep analysis
model: deepseek-v4-pro:high
output: context-build/01-deep-context.md

Analyze the task against the codebase using the scout map at context-build/00-scout-map.md.
Read every relevant file fully — follow imports, callers, tests, config, docs, and adjacent patterns.
Conduct web research if external APIs, libraries, or best practices matter.

Write two files in the chain directory:

`context-build/01-deep-context.md`
- Relevant files with line numbers and key snippets
- Important patterns already used in the codebase
- Dependencies, constraints, and implementation risks
- Resolved questions and remaining gaps

`context-build/meta-prompt.md`
- Goal: concrete outcome for the implementing agent
- Context/evidence: files, diffs, decisions, constraints
- Success criteria: what must be true before done
- Hard constraints: true invariants (no edits for review-only, single writer, etc.)
- Suggested approach: concise direction
- Validation: targeted checks to run
- Stop/escalation rules

Skip `.pi/plans/` and `.pi/` (except agents/settings).

## planner
phase: Planning
label: Create plan
model: gpt-5.5:high
as: plan
output: plan.md
reads: context-build/01-deep-context.md, context-build/meta-prompt.md

Create a concrete implementation plan using the deep context and meta-prompt above. Do NOT edit code.

Skip `.pi/plans/` — orchestration artifacts, not source.

## worker
phase: Implementation
label: Implement + test
model: deepseek-v4-pro:high
reads: plan.md
skill: playwright-browser
progress: true
output: implementation.md
acceptance:
  criteria:
    - "Implementation follows the approved plan"
    - "Playwright e2e tests cover the new/changed behavior"
    - "New feature tests pass"
    - "No unrelated files modified"
    - "Meta-prompt success criteria are met"
  evidence: ["changed-files", "commands-run", "validation-output", "residual-risks"]
  verify:
    - id: "feature-tests"
      command: "cd frontend && npx playwright test --grep {task}"
  stopRules:
    - "Do not edit files outside the scope of the plan"
    - "Stop and report if an unapproved decision is needed"
  maxFinalizationTurns: 3

Implement the approved plan at plan.md. Write Playwright e2e tests.
After implementing, run your new tests directly — target only the test file you created.

When scouting, skip `.pi/plans/` and `.pi/` (except agents/settings).

## parallel
phase: Review
label: Parallel review
parallel:
  - agent: reviewer
    label: Correctness
    model: gpt-5.5:high
    context: fresh
    reads: plan.md, implementation.md, context-build/meta-prompt.md
    task: Review the implementation diff for correctness, regressions, and edge cases.
      Check against the meta-prompt success criteria. Inspect the actual diff directly.
      Do not modify files.
    
  - agent: reviewer
    label: Test quality
    model: deepseek-v4-pro:high
    context: fresh
    reads: plan.md, implementation.md
    task: Review the tests. Do they cover key scenarios, error states, edge cases,
      and the acceptance criteria? Are assertions actually verifying the right behavior?
      Do not modify files.
    
  - agent: reviewer
    label: Simplicity + security
    model: deepseek-v4-flash:off
    context: fresh
    reads: plan.md, implementation.md
    task: Review for unnecessary complexity, duplication, verbosity, inconsistent patterns,
      and any security concerns (XSS, injection, exposed data). Do not modify files.
concurrency: 3

## parallel
phase: Validation
label: Behavior validation
parallel:
  - agent: reviewer
    label: Behavior check
    model: deepseek-v4-pro:high
    context: fresh
    reads: plan.md, implementation.md
    skill: playwright-browser
    task: Validate that the implementation actually works. Use Playwright or bash to
      interact with the running app and verify the feature behaves correctly.
      Check the happy path, error states, and edge cases. Report pass/fail with evidence.
      Do not modify project source files.
    
  - agent: reviewer
    label: Regression check
    model: deepseek-v4-flash:off
    context: fresh
    reads: plan.md, implementation.md
    task: Run the existing test suite and verify no regressions:
      `cd frontend && npm run test:e2e`
      Report which tests passed and which failed. Do not modify project source files.
concurrency: 2
