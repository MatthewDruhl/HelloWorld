---
name: spec-up
description: |
  Brownfield pipeline entry for this repo. Retrofit a build contract onto an
  EXISTING GitHub issue: derive testable acceptance criteria from it, author and
  commit the acceptance test(s) PENDING on main, then hand off to /spec-dev. Use
  when an existing issue should be built through the pipeline but has no
  committed acceptance tests yet.
license: MIT
metadata:
  user-invocable: true
  slash-command: /spec-up
  model: default
  proactive: false
---

# Spec-Up

Turn an existing GitHub issue into a `/spec-dev`-ready build contract, without
minting a PRD. This skill is repo-local and forge-native: every deterministic
gate below is a `forge` subcommand shipped in this repo, driven by the committed
registry `state/projects.md`. Nothing here depends on an external checkout.

## When to Use

- The owner types `/spec-up <issue>`, or an existing issue should be built through the pipeline.
- The issue describes a **single buildable unit** (a vertical slice or a self-contained fix), not an epic or a meta/triage issue.
- The issue has no committed PENDING acceptance tests yet.

**Route elsewhere when:**

- The issue is a **meta/epic** spanning multiple slices: scope a PRD to one epic first, then slice it. Spec-up is one issue, one contract.
- There is **no issue yet**: that is greenfield planning, not spec-up.
- The issue **already names committed PENDING acceptance tests**: skip straight to `/spec-dev`.
- The task is a refactor/research/migration with no testable behavior change: dispatch it directly.

## Requirements

- The project is registered in `state/projects.md` (repo + path).
- An existing GitHub issue describing one buildable unit.
- A pending-test convention that keeps a committed-red suite from BOTH failure
  modes: silently skipping (a false green that proves nothing) and reddening
  sibling PRs that do not implement it. In this pytest repo the canonical marker
  is the literal decorator, one per test function:

  ```python
  @pytest.mark.xfail(strict=True, reason="PENDING (#<n>)")
  ```

  It is enforced at authoring time, not by eye:

  ```bash
  forge validate pending-markers tests/test_<slice>.py
  ```

## Process

### Step 0: Readiness Gates (all inputs)

These gates run on **every** input, not just drafts you authored here. A shaped,
pre-existing issue is the normal input and must clear the same gates before
Step 4; a stray arrow or a bare "exit 0" slips through just as easily on an
organic issue as on a fresh draft.

- **Buildability triage**: apply Step 2.
- **Golden values**: confirm or elicit them per Step 3.
- **Lazily-satisfiable guard**: reject a criterion whose only proposed test is trivially passable (a bare "exit 0", an assertion an empty implementation would satisfy). Push for an observable a wrong implementation would fail.
- **Testability-seam pre-check**: ask whether the code under test is reachable in isolation. If not, name the seam or injectable surface as part of the work and write it into the issue, so neither this skill nor `/spec-dev` is surprised by it later.
- **Invariant lens**: if the issue asserts an ownership, uniqueness, or "must never happen twice" property, apply the Step 3 invariant lens now, so the issue carries a criterion the happy path cannot satisfy.
- **Dedup against open issues**: `gh issue list --repo <owner/repo> --search "<terms>"` before minting a duplicate.
- **Namespace-collision check**: before a CLI subcommand, flag, or module name lands in an issue body, grep for it — the subparser set (`grep -n "add_parser(" src/forge/cli.py`), the package's module names, existing flags. A hit is surfaced as a DECISION for the owner (rename options + what the existing name owns), never resolved by silently picking a different name mid-draft.
- **Lint gate**: run the readiness validator on the issue body and do not proceed to Step 4 until it exits 0 (all 8 canonical sections present, plus a golden-value arrow inside Acceptance Criteria with a real value on **both** sides; a one-sided or placeholder-only arrow does not count):

  ```bash
  forge validate spec-up-issue /tmp/issue-body.md
  forge validate spec-up-issue /tmp/issue-body.md --labels route:spec-up,demo-path --milestone M9
  ```

  Passing `--labels` enables the filing checks; `--milestone` requires `--labels`.

**Authoring from scratch (optional intake):** when there is a finding or need but
no well-formed issue yet, draft the issue body while running the gates above; the
drafted issue then becomes the "existing issue" the rest of the skill consumes.

### Step 1: Resolve the Project and Read the Issue

1. Resolve the project from `state/projects.md` (repo + path).
2. Fetch the issue with full context: `gh issue view <number> --repo <owner/repo> --comments`.
3. Read the repo's own conventions and the code the issue targets. Never assert what the code does without reading it.

### Step 2: Triage the Issue's Granularity

- **Single buildable unit** -> continue.
- **Epic / meta / triage issue** -> stop, and say which epic you would start with.
- **Not testable** (pure refactor, doc, research) -> stop and route out of the pipeline.

> Footprint rule: if this slice introduces a new concern, the expected footprint
> names a NEW module for it. Extending a module over 500 lines is not the
> default — it requires an explicit "extending oversized module `<name>` because
> `<reason>`" line in the plan presented for approval.

### Step 3: Derive Testable Acceptance Criteria

The criteria come **from the issue**, not invented:

1. If the issue states criteria, confirm each is **testable** and **behavioral**: observable behavior, not implementation. "Returns 409 on a second match", not "works correctly".
2. If a criterion is vague or missing, interview the owner to make it testable. Ask **one question at a time** and wait for each answer. Pull golden values (input -> expected output) into the open.
3. Where a documented invariant is touched, make the guard for that invariant one of the criteria. A committed test is how a prose rule becomes enforced.
4. **Invariant / non-functional lens.** When the issue asserts a "must never happen twice" property, deriving from prose alone yields only the *sequential* criterion, which a read-then-write guard satisfies while a concurrent race still violates the invariant. Derive criteria the happy path cannot satisfy: a constraint at the durable layer (unique / partial-unique / check), and a concurrency test with two interleaved requests. Where relevant add the sibling lenses: idempotency-under-retry (same request twice, one effect) and partial-failure/rollback (a mid-transaction failure leaves no half-state).

   **Pre-demo scoping.** Before the project's demo milestone, keep the sequential
   criterion and the durable-layer constraint (cheap, and it stops corruption at
   the root), but file the concurrency / retry / partial-failure tests as
   labeled post-demo acceptance work instead of folding them into this contract,
   unless the happy path itself can corrupt or lose data. After the demo
   milestone, apply the full lens.

If the criteria cannot be made testable, stop and say what is unclear. Do not guess.

### Step 4: Author the Acceptance Suite

1. Author `ACCEPT: <behavior>` bodies with golden values (one criterion may map
   to several tests). After drafting each body, validate its dual-layer format
   and do not proceed to the review batch until it exits 0:

   ```bash
   forge validate accept-body /tmp/accept-body.md
   ```

2. **Second-model validity + coverage review** as a single batch, under the
   degradation order and the never-poll rule in `AGENTS.md`. The contract: ONE
   exhaustive pass in which the reviewer enumerates ALL findings (tautologies,
   coverage gaps, weakening vectors, false-allows) and does not stop at the
   first. Triage per the two-bucket rule in `/spec-dev`: fix every blocking
   finding (a tautology, a weakening vector, a false-allow, a happy-path
   coverage gap), but a robustness finding raised before the demo milestone is
   FILED with the deferred-hardening label, not folded into this suite. Then run
   ONE confirmation round on the fixed suite. Reopen only if the confirmation
   round itself finds a NEW blocking issue.
3. **Owner approval as one batched review of the whole suite.** Present every
   test plain-English-first (the plain behavior summary, then its
   `technical (contract):` golden values) with its review annotation, and take
   approve / adjust / reject per test in that single pass. On approve, a
   test-author agent under `src/forge/pipeline/agent_contract.md` opens a PR
   adding the executable tests on a suite branch, marked PENDING. Before
   committing, run the gates this repo actually ships on the new suite file:
   `forge validate pending-markers <suite-file>` plus a full local test run
   (this repo has no separate format/lint tooling; do not invoke tools the
   checkout does not provide).

**Verbatim-example fixture rule:** if the issue body shows a concrete example of
the input/output under test, one committed fixture must reproduce it verbatim,
and the coverage check confirms the suite pins that canonical format.

**Presentation: plain-English-first (dual-layer).** Every acceptance test is
presented plain-English-first with the exact golden values preserved in a
labeled `technical (contract):` block underneath. This applies to the approval
prompt, the ACCEPT bodies, the committed docstrings, and the Step 6 handoff. The
human gate should judge "is this the behavior we want", not "is this the right
mock". Golden values are the identical byte-for-byte contract either way; plain
English is additive, never a substitute.

### Step 5: Stop at the Suite PR, Resume After the Owner Merges

Opening the suite PR is where this skill STOPS mutating: it never merges, and
the tests are not "committed on `main`" until the owner has merged that PR.
Only AFTER the merge (and its `/merged` cleanup) do the closing steps run:
update the **existing issue body** to name the now-on-`main` PENDING
acceptance test(s). After this the issue satisfies `/spec-dev`'s entry
requirement: it names committed, currently-PENDING acceptance tests on `main`.
A handoff issued while the suite PR is still open is premature — `/spec-dev`
must refuse it.

A suite PR body must say `References #<n>` for its build issue, never a closing
keyword — a closing keyword closes the build issue the moment the suite merges,
before anything is built.

### Step 6: Verify the Suite PR, then Handoff

Do not declare the issue contract-ready while the suite PR is red. Local
verification does not exercise gates that only run on the PR.

1. Run `gh pr checks <suite-pr>`. In a repo with no CI configured this reports
   "no checks" — state that and move on rather than waiting.
2. Re-run the local gates on the committed file:

   ```bash
   forge validate pending-markers tests/test_<slice>.py
   ```

3. Only then hand off, describing each committed test plain-English-first:
   "Acceptance tests committed PENDING on `main` (suite PR #<pr>); issue #<n>
   now names them. Run `/spec-dev <n>` to build."

## What This Skill Does NOT Do

- Write a PRD, or decompose an epic into slices.
- Implement the issue, or modify acceptance tests after authoring — that is `/spec-dev`, and acceptance tests are never weakened during a build.
- Skip the review or the owner gate in Step 4.
- Merge or close anything.

## Background Launch Contract

Any background launch this skill triggers follows the guarded-launch rules in
`/spec-dev`'s Background Launch Contract section: close stdin, never send stderr
to `/dev/null`, persist the full output to a log file, set an explicit timeout,
treat empty output or a non-zero exit as FAILED with one retry, and preserve the
launch's own exit status.
