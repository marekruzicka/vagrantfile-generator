---
name: feature-workflow-light
description: Lightweight feature implementation: scout → plan → worker → single reviewer
---

## scout
phase: Context
label: Gather context
model: deepseek-v4-flash:off
as: context
output: context.md

{task}

Skip `.pi/plans/` and `.pi/` (except agents/settings) — orchestration artifacts, not source code.

## planner
phase: Planning
label: Create plan
model: gpt-5.5:high
reads: context.md
as: plan
output: plan.md

Create a concrete implementation plan from the scout context. Do NOT edit code.

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

## reviewer
phase: Review
label: Review
model: gpt-5.5:high
context: fresh
reads: plan.md, implementation.md

Review the implementation diff for correctness, edge cases, test coverage, and project
pattern adherence. Inspect the actual diff directly. Do not modify files.
