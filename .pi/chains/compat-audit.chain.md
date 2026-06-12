---
name: compat-audit
description: Parallel investigation: scout local codebase + researcher external evidence → parent discusses findings
---

## parallel
phase: Investigation
label: Gather evidence
parallel:
  - agent: scout
    label: Local audit
    model: deepseek-v4-flash:off
    as: localFindings
    output: findings/local.md

    {task}

    Focus on:
    - Files that are relevant to the compatibility question
    - Configuration discrepancies between different deployment methods
    - Hardcoded values, env vars, paths that may have diverged
    - Documentation that may be stale
    - Any code paths that are dead or broken under one deployment method

    Include file:line references for every finding.
    Skip `.pi/plans/` and `.pi/` (except agents/settings) — orchestration artifacts.

  - agent: researcher
    label: External research
    model: deepseek-v4-pro:high
    as: externalFindings
    output: findings/external.md

    Research best practices, common issues, tools, and migration patterns relevant to: {task}

    Include:
    - Common pitfalls and breakage points
    - Recommended validation approaches
    - Tools or commands that can verify the current state
    - Source links for key references

    Focus on actionable, evidence-backed information.
    Do not include general overviews or marketing content.
concurrency: 2
