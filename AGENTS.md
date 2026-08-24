# AGENTS.md — driver's manual for pipeline-forge

This repo runs its own build pipeline. Every deterministic gate is a `forge`
subcommand shipped in `src/forge/`, every skill is committed under
`.claude/skills/`, and the project registry is the in-repo `state/projects.md`.
A fresh session here needs nothing outside this checkout.

Read this file first. It is the routing table, the boundary list, and the
reviewer contract. The skills carry the procedures; this file says which one to
open and what never to do.

## Preflight

Before the first pipeline action of a session, confirm the toolchain and the
registry resolve:

```bash
forge --registry state/projects.md --logs-dir ~/Projects/agentLogs doctor
```

`--registry` and `--logs-dir` are TOP-LEVEL flags, required, and go BEFORE the
subcommand. A bare `forge doctor` exits 2 without running anything — that is an
unconfigured invocation, not a broken environment.

A non-zero exit means the environment is not ready. Fix it before dispatching
anything: a build launched against a broken preflight burns an agent round-trip
to discover what one command would have told you.

## Routing

| You want to | Command | What it owns |
|---|---|---|
| Give an existing issue a build contract | `/spec-up <issue>` | Derives testable criteria, authors the acceptance suite, commits it PENDING on `main`, names it on the issue. |
| Build a contract-ready issue | `/spec-dev <issue>` | Plan gate, background implementer in a linked worktree, flips PENDING to required, PR. |
| Write code test-first | `/tdd` | The inner red-green-refactor loop every implementer follows. Not a slash command on its own during a build. |
| Save and push work | `/commit` | Logical commits, push, verified landing, confirmed PR. |
| Clean up after a merge | `/merged` | Post-merge protocol: fast-forward, cleanup runner, closeout report. |

The pipeline is a line, not a menu: `/spec-up` -> `/spec-dev` -> owner merges ->
`/merged`. `/tdd` and `/commit` are used *inside* those stages. An issue with no
committed PENDING acceptance tests does not enter `/spec-dev`; route it through
`/spec-up` first, and refuse rather than improvising a contract mid-build.

## The deterministic gates

Every gate below is model-free and runs the same way every time. None of them is
optional because a model "already checked".

| Stage | Command |
|---|---|
| Issue is spec-up ready | `forge validate spec-up-issue <body-file>` |
| ACCEPT body is dual-layer | `forge validate accept-body <body-file>` |
| Suite uses the canonical PENDING marker | `forge validate pending-markers <suite-files>` |
| Handoff prompt has all seven sections | `forge validate handoff-prompt <prompt-file>` |
| Targeted test exists and is PENDING | `forge check acceptance-integrity --entry ...` |
| No acceptance test was weakened | `forge check acceptance-integrity --old ... --new ...` |
| Build PR bases on the default branch | `forge check build-pr-base --base <observed base from gh pr view>` |
| The push actually reached the remote | `forge check push-landed --repo ... --remote ... --branch ... --sha ...` |
| Milestone reconcile has no orphans | `forge check agile-reconcile --repo <owner/repo>` |
| The run is recorded | `forge --logs-dir <dir> log-run --remote <git remote URL> ...` |

Two flag traps in that table. `--base` takes the base the PR ACTUALLY has, read
from `gh pr view`; hardcoding `main` compares `main` to the default branch and
passes unconditionally, which is a false green, not a check. And `log-run`'s
`--remote` takes a git URL or an `owner/repo` slug, never a remote NAME like
`origin` — a bare name has no owner segment and raises.

## Hard boundaries

- **Never commit to `main`.** Branch, push, open a PR. Every change to `main` goes through a PR, including a one-line fix.
- **Never merge or approve a PR, and never close an issue by hand.** Merging is the owner's decision; PR linkage closes issues on merge.
- **Never modify, weaken, delete, or skip a committed acceptance test.** The only legitimate edit during a build is removing the PENDING marker of a test that is genuinely green. If a targeted test looks wrong, STOP and report it as a spec change.
- **Never widen repo-global config to satisfy a hook or a lint rule.** Fix the narrow cause; if the rule itself is wrong, stop and say so.
- **Never write outside the assigned footprint.** The handoff prompt names the exact file set an agent may write.
- **Never read or write `.env`, and never echo a secret** into output, a commit, or a PR body.
- **Report before idling.** A background agent's final report is the run record. An idle notification carries no results and forces a manual recovery round-trip.

## Second-reviewer contract

Claude writes the code, so a *different* model grades it. The reviewer ladder
degrades in a fixed order, and the fallback is always recorded, never silent:

1. **Codex** — the primary reviewer. Run it as one exhaustive adversarial pass over the branch diff.
2. **grok-4.6 in file-access mode** — the fallback when Codex is unavailable or its result is unusable. File access matters: a reviewer working from a pasted excerpt reconstructs hunks it cannot see and reports fabricated findings.
3. **A recorded skip** — when neither reviewer can run, record the literal form `skipped:<reason>` in the run's `cross_review` field. A skip must carry a real one-line reason; an unexplained blank is not a skip, it is an unrecorded gap.

**Never poll a running review.** A review turn takes minutes, and resuming,
polling, or messaging the reviewer mid-turn ABORTS the turn, so it never emits a
verdict — which then reads as a review that "hung". The review works; the poll
kills it. Launch it, leave it strictly alone, and wait for its own completion
notification.

An EMPTY review result is FAILED. Zero output is not a clean bill of health: it
is the exact signature of an aborted turn, a launch that blocked on a missing
TTY, or a reviewer that never started. Re-run it fresh and untouched, or degrade
one rung down the ladder and record the reason.

A VERDICT-LESS review is FAILED for the same reason. A review that produces prose
but never states a verdict, or whose run exits non-zero, has not graded anything;
treat "no verdict" as a failed gate, never as a pass. Only an explicit verdict on
the actual diff closes the cross-review gate.

Triage findings into exactly two buckets. **Blocking** (fix on the branch before
the merge decision): happy-path correctness of the contracted behavior, a fake or
unearned green, data loss or corruption, security. **Deferred** (file with the
deferred-hardening label, do not schedule): crash recovery, concurrency edges,
adversarial inputs, portability. Deferral is explicit and labeled, and it never
narrows the slice's own acceptance criteria.

## Known traps

These have each cost a real round-trip in this repo. They are not hypotheticals.

- **A stale local `main` makes the next diff lie.** `/merged` does not advance a session's local `main` ref. Fetch and fast-forward before any `git diff main <branch>`, or already-merged changes surface as phantom out-of-scope edits.
- **Never stack a build PR on a suite PR.** This pipeline is un-stacked by design: the suite PR merges to `main` first, and the build branch forks from `main` afterwards. Stacking strands the build off `main` the moment the suite merges, and it breaks every weaken-check that reads the committed suite out of `main`.
- **`timeout` is not on stock macOS.** A bare `timeout 600 ...` exits 127 without launching anything, and the empty log then reads as an empty result. Use `perl -e 'alarm shift; exec @ARGV' 600 ...`.
- **A verdict is only recorded after the review returns.** Never write `--cross-review done` at report-back time; there is nothing to record yet, and a pre-written pass is a fabricated one.
- **A suite PR must never carry a closing keyword** for its build issue. `Closes #<n>` on a suite PR closes the issue the moment the suite merges, before anything is built. Use `References #<n>`.
- **Shell variables do not survive the no-main-commit hook.** Write the worktree path LITERALLY in every `git -C <abs> commit`; the hook cannot expand `$VAR` and refuses the commit.
- **A staged new file follows a branch switch.** `git restore --staged <file>` before committing on a sibling branch, or it leaks into the wrong PR.
- **A PENDING suite for a module that does not exist yet must import that module INSIDE each test.** A top-level import is a collection failure, not an expected failure, and it reddens the whole file instead of pending one test.
- **This repo has no CI.** `gh pr checks` reports "no checks" — state that and move on. Do not wait on checks that will never appear, and do not report "CI green" when nothing ran.
- **Every claim is verified before it is stated.** Read the code before saying what it does, run the tests before saying they pass, and confirm a command exists before recommending it. A green suite that never executes the changed behavior is not verification.
