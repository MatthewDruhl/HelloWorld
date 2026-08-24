---
name: spec-dev
description: |
  Build-pipeline execution stage for this repo: implement a GitHub issue that
  already names committed PENDING acceptance tests, via an approved plan and a
  background TDD implementer. Use when the owner types /spec-dev <issue>. NOT for
  issues without committed acceptance tests (route /spec-up first) and NOT for
  quick direct fixes nobody routed through the pipeline.
license: MIT
metadata:
  user-invocable: true
  slash-command: /spec-dev
  model: default
  proactive: false
---

# Spec-Driven Development

The execution stage of this repo's build pipeline. It is forge-native: every
deterministic gate below is a `forge` subcommand shipped in this repo, and the
agent contract lives in-repo at `src/forge/pipeline/agent_contract.md`. Routing
across the whole pipeline is in `AGENTS.md`.

## When to Use

- The owner types `/spec-dev <issue-number>`.
- A contract-ready issue needs implementing through the pipeline.

## Requirements

- A GitHub issue describing one vertical slice, contracted via `/spec-up`.
- The issue MUST name the acceptance test(s) it targets.
- Those tests MUST already be committed PENDING and owner-approved **on `main`**.
  This pipeline does not stack: the suite PR merges to `main` FIRST, and the
  build branch forks from `main` afterwards. A build is never dispatched against
  a suite that lives on an unmerged branch. That rule is what makes every
  `git show main:<suite-file>` in this skill unconditionally correct, and it
  removes the failure where a merged suite PR strands a build branch based on it.
- If no committed, approved suite exists on `main`, refuse: "This slice has no
  committed acceptance tests to drive. Run `/spec-up` to author and approve them
  first."
- The issue MUST have acceptance criteria for any behavior no committed test
  covers. If missing or vague, stop and ask.

## Process

### Phase 1: Interactive (requires the owner)

#### Step 1: Read the Spec

1. Look up the project in `state/projects.md` for the repo and path.
2. Fetch the issue: `gh issue view <number> --repo <owner/repo> --comments`.
3. Read the full body and every comment. Verify acceptance criteria exist; if
   missing or vague, stop: "This issue needs acceptance criteria before I can
   build it."
4. Read the targeted acceptance tests **on `main`**. These are the contract.
   Confirm each exists and is currently PENDING, and note the marker convention
   — you will flip exactly these.
5. **Deterministic entry gate.** For each targeted test, run the
   acceptance-integrity guard in entry mode against the file AS COMMITTED ON
   `main` — materialize that snapshot first; a relative path would read the
   working tree, which is not the contract when the checkout is on a branch or
   the local `main` is stale:

   ```bash
   git -C <repo-abs-path> show main:tests/test_<slice>.py > /tmp/suite-entry-<slice>.py
   ```

   ```bash
   forge check acceptance-integrity --entry --base /tmp/suite-entry-<slice>.py --test test_<name>
   ```

   Exit 0 means the named test exists and is PENDING. A non-zero exit ("not
   found" = absent, "not pending" = present but unmarked) is a hard refusal, not
   a warning: stop and report. This check is model-free and runs ALWAYS.

#### Step 2: Explore the Codebase

1. Work from the project path in `state/projects.md`.
2. Read the repo's conventions and the modules the issue targets.
3. Identify the real footprint — the files that will actually be written — and
   the existing test patterns around them.
4. Understand the current architecture before proposing changes.

#### Step 3: Plan

Present the plan:

```
**Issue:** #<number> - <title>
**Repo:** <owner/repo>
**Branch:** <type>/<short-description>

**Acceptance Criteria:**
- [ ] <criterion>

**Approach:**
1. <what will be changed and why>

**Verification plan:**
1. <criterion> -> <test name, or command + expected output, or external signal>

**Files affected:**
- <file>: <what changes>

Approve this plan?
```

Rules for the plan:

- The verification plan anchors to the COMMITTED acceptance tests this slice flips from PENDING to required. List them by name.
- If building reveals behavior no committed test covers, note the new test(s) needed. New acceptance tests are authored and approved through `/spec-up`, with a logged reason — never invented inside a build.
- Name the unit-level checks the inner TDD loop will add. These are emergent, not exhaustive up front.
- **Verify external-runtime semantics against docs BEFORE building.** If the slice integrates external semantics (harness hook events, a protocol, a third-party API), the plan names a docs-verification step that confirms them before implementation. Guessed runtime semantics cost two live-failure rounds the last time they were guessed.
- If a targeted acceptance test looks wrong, stop and flag it as a spec change. Do not plan around editing it.

**Wait for explicit approval before proceeding.**

#### Step 4: Save the Plan

Save the approved plan to `.plans/plan-issue-<number>.md`. This is the audit
trail: if the build drifts, compare the PR against this file.

### Phase 2: Background (no owner needed)

Spawn ONE implementer agent. The acceptance tests were authored independently
upstream and approved by the owner, so they are the external check on this
agent. The agent makes them pass; it does not get to redefine them. That
independence is already won across pipeline stages, which is why one implementer
is enough.

#### Agent Instructions

Prepend the full text of `src/forge/pipeline/agent_contract.md` to the agent
prompt. It defines isolation, git, write-scope, verification, and report-back
rules. The instructions below extend that contract; they never weaken it.

##### Handoff-Prompt Contract (required sections)

Every delegated build prompt MUST state all seven sections. A prompt missing any
section is under-specified: fill it in before spawning.

1. **Goal** — the issue's outcome, in one clear statement of work.
2. **Exact repo + target paths** — the concrete repo and the target file paths from the Step 2 footprint recon, not a vague area of the codebase.
3. **Constraints** — the file-disjoint footprint boundaries. State the exact set the agent may write.
4. **Non-goals** — explicit "do not touch / do not refactor X".
5. **Exact proof command** — the literal committed acceptance-suite invocation for this issue, copied verbatim, not paraphrased. This is the same command the reviewer runs.
6. **Output shape** — the exact report shape expected back.
7. **Recon delta** — either the literal word "none" or a short list of what pre-dispatch recon established that the issue body does not say: forced footprint, traps already identified, verified-safe conclusions the agent must not re-litigate, consciously deferred items with issue numbers. Any finding that changes the contract is written into the issue body BEFORE dispatch; the prompt section only attests the delta.

Lint the assembled prompt before spawning; it must exit 0:

```bash
forge validate handoff-prompt /tmp/handoff-<issue>.md
```

Exit 0 prints the handoff-ready line; non-zero lists the missing or malformed
sections. Fix before spawning, never dispatch under-specified. The validator
wants canonical ATX headers (`## Goal`, unnumbered) and a proof command wrapped
in backticks or a fence.

**Three nested retry caps (do not conflate).** (a) **3 in-agent attempts** per
failing test — the contract's own inner loop; (b) **2 reviewer fix-rounds** per
slice, then escalate rather than looping; (c) **2 fresh-agent re-dispatches** per
slice. Each outer cap contains many of the inner: one re-dispatch runs a fresh
agent that itself gets 3 in-agent attempts and can be sent through 2 reviewer
rounds.

**Build recovery.** When a build fails (the implementer dies, the committed suite
is still red after the agent reports done, or the build gate rejects), capture a
compact error trace (failing-test id + assertion diff + any stricter
instruction) OUTSIDE the worktree, bump the persisted recovery counter, and
decide: on retry, hard-reset the worktree to the branch base, clear untracked
files, and re-dispatch a FRESH agent carrying the frozen contract + the trace but
NEVER the prior transcript (context rot). On cap exhaustion, record the run
`needs-review` with the accumulated notes and hand to the owner.

Pass the following to the background agent:

1. **Setup** — the slice number and repo; the branch to create; the committed,
   currently-PENDING acceptance tests it targets, by name and path, and that
   they are the contract; the approved plan; the full issue body; and the
   instruction to read the repo's conventions and the targeted tests before
   writing any code.
2. **Inner TDD loop** (follow the `/tdd` skill) — drive the targeted tests from
   PENDING to green ONE vertical slice at a time: one unit test, minimal
   implementation, green, repeat. Each unit test verifies behavior through
   public interfaces. Never write all unit tests first. The agent MAY add unit
   tests; it MUST NOT modify, delete, weaken, or skip any acceptance test. If a
   targeted test looks wrong, STOP and report it as a possible spec change.
3. **Implement** — minimal code per test, following existing patterns. No
   speculative features.
4. **Flip PENDING to required** — as each targeted test passes, remove its
   marker so it becomes a required gate.
5. **Verify against spec and suite** — re-read the issue and the targeted tests
   (fetch again, do not rely on memory); confirm each is green and required; run
   the FULL suite once — it MUST stay green, this slice may not regress any
   previously-passing test. **Test-run economy:** if the full run regresses,
   iterate on just the failing tests, then do a single confirming full run.
   Never loop on the full suite; a failing full run dumps output the agent
   re-reads every cycle, which is where test tokens actually burn. Do not claim
   a criterion is met without pasting real output.
6. **Commit and PR** — clear messages following repo conventions, push the
   branch, open a PR:

   ```
   ## Summary
   <what was built and why>

   ## Spec
   Closes #<issue-number>

   ## Acceptance Tests Flipped
   - <test name>: PENDING -> required (verified by <unit test/output>)

   ## Full Suite
   - <N passed, 0 failed>: no regressions

   ## Test Plan
   - [x] Full acceptance suite green locally
   - [x] Verified against the original issue

   🤖 Generated with [Claude Code](https://claude.com/claude-code)
   ```

   This extends the contract's PR format with the Acceptance Tests Flipped and
   Full Suite sections. Merge and close prohibitions are in the contract.

   Verify the PR's base is the default branch. Read the base the PR ACTUALLY
   has, then check that observed value. Passing a hardcoded `main` compares
   `main` against the default branch and passes no matter what the PR is based
   on — a false green that never reads the PR at all:

   ```bash
   BASE=$(gh pr view <build-pr> --json baseRefName -q .baseRefName)
   ```

   ```bash
   forge check build-pr-base --base "$BASE"
   ```

   **Gate on the push landing at origin, not the agent's word.** After pushing:

   ```bash
   forge check push-landed --repo <worktree-abs-path> --remote origin --branch <build-branch> --sha "$(git -C <worktree-abs-path> rev-parse HEAD)"
   ```

   Exit 0 means the reported sha is on the remote branch. Non-zero means the
   push did not reach origin: recover from the worktree and re-push before
   reporting done. Then check the PR (`gh pr checks <build-pr>`); this repo has
   no CI, so "no checks" is the expected answer — state it, do not wait on it.
7. **Report back** — PR URL, PR status, which acceptance tests flipped,
   full-suite numbers, decisions made, concerns. **The report goes out BEFORE
   the agent idles.** An idle notification is not a report.

#### Spawning the Agent

The implementer always works in its OWN linked worktree inside the target repo,
per the agent contract's cross-repo worktree pattern, so parallel builds never
collide on one checkout:

```
Agent(
  description: "spec-dev: <repo>#<issue-number>",
  run_in_background: true,
  prompt: <the handoff prompt above, with the agent contract prepended>
)
```

The global no-main-commit hook cannot expand shell variables, so the worktree
path is written LITERALLY in every `git -C <abs> commit` the agent runs.

#### Log the Run

Immediately after spawning, log the run, then update it when the agent reports.
Three flag traps, all of which fail the command outright: `--logs-dir` is a
TOP-LEVEL flag and goes BEFORE the subcommand; append mode requires `--date`,
`--project`, `--skill` and `--task`; and `--remote` takes a git remote URL or an
`owner/repo` slug, never a remote NAME — a bare `origin` has no owner segment and
raises. Resolve the real URL from the repo:

```bash
REMOTE=$(git -C <repo-abs-path> remote get-url origin)
```

```bash
forge --logs-dir ~/Projects/agentLogs log-run --remote "$REMOTE" --date "$(date +%F)" --project pipeline-forge --skill spec-dev --task "#<issue>" --branch <branch>
```

`--date` drives the run id, so it must be TODAY's date, computed at run time. A
hardcoded date silently files the run under the wrong day and collides with that
day's id sequence.

The append prints the new run id. When the agent reports back, update the record
with what it delivered:

```bash
forge --logs-dir ~/Projects/agentLogs log-run --remote "$REMOTE" --update <run-id> --status needs-review --output "<PR URL + suite numbers>" --notes "<decisions, concerns>"
```

**Do NOT write `--cross-review` here.** At report-back time the Cross-Review Gate
has not run, so any verdict written now is invented. The verdict is a separate,
later write, made once an actual review exists — see the Cross-Review Gate
section below.

#### Resuming a Mid-Flight Ruling

A background implementer may STOP with a legitimate spec question, get a ruling
back, then go idle without executing — clean worktree, zero commits, no PR. Soft
prose ("proceed to completion") is not a reliable continuation trigger. Use both
mechanisms:

1. **Imperative-checklist ruling reply.** End every ruling reply with an explicit
   execution checklist, not a soft "proceed": resume the approved plan ->
   implement -> flip the targeted tests -> run the full suite -> commit, push,
   open the PR -> report back with the PR URL and suite result.
2. **Ground-truth follow-up.** After sending a ruling, check the branch for new
   commits or a PR rather than waiting for the next idle notification. If the
   tree is still clean, send the resume nudge immediately.

Surface the agent's question to the owner as a decision gate (purpose,
why-forced-now, what-changes, cost-of-no) before any file path, not as raw
file-talk.

#### Deterministic Acceptance-Integrity Guard (always-on, model-free)

Before the second-model review, run the weaken-check on every targeted
acceptance file in the diff, comparing the committed version on `main` against
the branch. The guard takes two FILES, not two refs, so materialize the `main`
side first — nothing else in this skill creates that snapshot, and skipping this
step is a `FileNotFoundError`, not a clean run — and `--new` must be the
suite file inside the BUILD WORKTREE (absolute path): a relative path resolves
in the orchestrator's checkout, whose unchanged copy would compare clean and
miss a weakening on the build branch:

```bash
git -C <repo-abs-path> show main:tests/test_<slice>.py > /tmp/suite-ref-<slice>.py
```

```bash
forge check acceptance-integrity --old /tmp/suite-ref-<slice>.py --new <build-worktree-abs-path>/tests/test_<slice>.py
```

Exit 0 means the only change is marker removal (the legitimate Step 4
activation) or a comment/whitespace edit. A non-zero exit is a WEAKENING and
names the offending test: an assertion, expected value, or comparison-operator
change; an `or True` short-circuit; an assert no-op'd; a whole-test deletion; a
rename-with-same-body; a marker downgrade (`xfail`->`skip`, `strict=True`->
`strict=False`); or a change to a module-level constant an assertion reads.
Non-zero is blocking; fix it on the branch before the merge decision.

This runs ALWAYS, not just when the second reviewer is up. It is the
deterministic layer UNDER the semantic review below, closing the gap where a
recorded `skipped:<reason>` would otherwise leave the do-not-weaken invariant
unenforced. It does not replace the reviewer, which still catches semantic
weakenings an AST check cannot.

A deliberate STRENGTHENING (a build-time spec correction the owner approved) also
trips this guard. Do not silence it: record the approval and have the second
reviewer confirm the direction of the change.

#### Cross-Review Gate (second-model critic)

Once the agent reports back and the run is `needs-review`, run an independent
second-model review of the PR diff, in parallel with the owner's own review
rather than gating it. Claude wrote the code; a different model grading it
catches the blind spots a single model shares with itself. The reviewer ladder,
the never-poll rule, and the failure classes are defined once in `AGENTS.md` —
follow them there.

> **Before diffing the feature branch against the default branch.** Any
> file-scope check that runs `git diff main <branch>` must first fetch and
> fast-forward the local `main` ref. A local default left behind origin makes
> already-merged changes show up as phantom out-of-scope edits.

- **Batched review contract.** ONE exhaustive pass: the reviewer enumerates ALL
  findings (concrete failure scenarios, weakened tests, tautologies) and does not
  stop at the first. Fix everything blocking in one batch, then run ONE
  confirmation round on the updated diff. Reopen only if the confirmation round
  itself finds a NEW blocking issue.

  > Structural check, reported as an ordinary finding: did this change grow any
  > module past the size limit, add an in-function internal import, or add a
  > second responsibility to an existing module?

- **Two-bucket triage.** A concrete failure scenario alone does NOT make a
  finding blocking — an adversarial reviewer can always construct one. Every
  finding lands in exactly one bucket; there is no third:
  - **Blocking, fix on the branch before the merge decision:** happy-path correctness of the contracted behavior, a fake or unearned green, data loss or corruption, or security.
  - **Deferred, file but do not schedule:** robustness (crash recovery, concurrency edges, adversarial inputs, portability). File it with the deferred-hardening label and record it in the run entry. Deferral is explicit and labeled, never silent, and it never drops, narrows, or defers the slice's own acceptance criteria.

  Ask the reviewer to tag each finding `correctness` or `robustness`. Note
  dismissed findings with a one-line reason.
- The reviewer also confirms NO acceptance test was modified, weakened, or
  skipped in the diff, and that new unit tests assert real behavior rather than
  tautologies.
- Record the verdict in the run's `cross_review` field so it is an auditable
  fact at terminal status. This write happens HERE, once a real review has
  returned — never back at report-back time, where there is nothing to record
  yet and a written `done` would be a fabricated pass:

  ```bash
  forge --logs-dir ~/Projects/agentLogs log-run --remote "$REMOTE" --update <run-id> --cross-review done
  ```

  The value is the outcome that actually happened: `done` for a clean review,
  `blocking:<n>` while findings are open, or `skipped:<reason>` when no reviewer
  could run. A skip must carry an explicit one-line reason.

### The Acceptance Suite Is the Regression Set

The acceptance tests this pipeline commits are cumulative. Every subsequent slice
keeps the entire suite green. "Done" for the whole project is the PENDING count
reaching zero with the full suite required and green.

## Error Handling

- **Tests will not pass / ambiguous spec:** contract verification rules apply — 3 distinct attempts, then stop and report. Never guess on ambiguity.
- **Missing dependencies:** the agent stops and reports what is needed rather than installing packages without context.

## What This Skill Does NOT Do

- Create issues, or author acceptance tests (that is `/spec-up`).
- Merge PRs or close issues — PR linkage closes them on merge.
- Skip the plan-approval checkpoint.

## Background Launch Contract

Every background launch whose output is captured to a file, not the session
transcript, MUST run guarded:

```bash
perl -e 'alarm shift; exec @ARGV' 600 codex exec --skip-git-repo-check "$PROMPT" </dev/null > run.log 2>&1
```

`timeout` is GNU coreutils and is NOT on a stock macOS box: the command exits 127
without ever launching the review, which then reads as an empty result. The perl
form is the portable one and is what this pipeline uses. If coreutils is
installed, `gtimeout 600 ...` works too, but do not write bare `timeout`.

- **stdin-close** — close stdin so the launch never blocks on a missing TTY.
- **stderr-capture** — fold stderr into the log with `2>&1`; never send stderr to `/dev/null`.
- **persistent-log** — persist the full output to a file, so the empty-output check has something to read.
- **timeout** — bound the run with an explicit wall clock.
- **empty-output-retry** — treat empty output as FAILED and allow one retry before escalating.
- **nonzero-exit-FAILED** — treat a non-zero exit as FAILED, never a clean pass.

Preserve the launch's own exit status: a `tee` pipeline reports the tail's status
and hides a failed launch, so use `set -o pipefail` or read `${PIPESTATUS[0]}` if
you must tee. A background launch may NOT filter stderr; a foreground launch
lands in the transcript and MAY, because the output is visible there. This is the
canonical contract the other build-pipeline skills reference.
