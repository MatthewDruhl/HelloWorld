---
name: merged
description: |
  Post-merge protocol for this repo, invoked after Matt has merged PR(s) in the
  browser: fast-forward the local default branch, then run forge's deterministic
  cleanup runner (verify, test gate, delete branches, clean worktrees, close
  issues, flip the run record) and report what's next. Use when the user types
  /merged or says they merged PR(s). NOT for merging itself: this skill never
  merges, approves, or closes a PR.
license: MIT
metadata:
  user-invocable: true
  slash-command: /merged
  model: default
  proactive: false
---

# Merged

Post-merge protocol. Merging is deliberately Matt's job; he merges in the browser
and then invokes `/merged`. This skill is repo-local and forge-native: the whole
cleanup ritual is owned by the `merged-run` runner shipped in this repo
(`src/forge/pipeline/merged/`), driven by the committed registry
`state/projects.md`. Nothing here depends on an external pipeline checkout.

The steps below are ORDERED. Step 1 runs before Step 2 every time.

## Step 1 — fast-forward the local default branch FIRST

Before invoking the runner, fast-forward this repo's local default branch to the
remote. `pull` only updates the branch that is CHECKED OUT, so pick the line that
matches where HEAD is — from a feature branch, the fetch form updates the `main`
ref directly without touching the working tree (and refuses a non-fast-forward):

```bash
# HEAD on main:
git -C ~/Projects/pipeline-forge pull --ff-only origin main
# HEAD on any other branch:
git -C ~/Projects/pipeline-forge fetch origin main:main
```

This is a pre-run step, not a cleanup step, and it exists for two reasons:

1. **The runner you are about to execute is code in this repo.** A merged PR that
   changed the runner is only in the tree after this fast-forward, so a stale
   local default branch runs the PRE-merge runner against a POST-merge world.
2. **A stale default branch makes the next reviewer's diff lie.** Already-merged
   changes show up as phantom out-of-scope edits in `git diff main <branch>`.

Fast-forward only, never force. A non-fast-forwardable local default branch means
the local branch has diverged: STOP and surface it to Matt rather than resolving
it. The runner's own post-cleanup `main_sync` does not replace this step — it runs
after the cleanup, far too late to refresh the code being executed.

## Step 2 — run the cleanup runner

Run once per invocation from the repo root (the registry path is repo-relative),
passing every merged PR number:

```bash
forge --registry state/projects.md --logs-dir ~/Projects/agentLogs \
  merged-run --project pipeline-forge --remote origin --pr <number> [--pr <number> ...]
```

- `--project` is the registry key in `state/projects.md`; `--remote` is required
  so a live run is never left guessing the remote name.
- `--pr` is repeatable, one flag per merged PR number.
- `--logs-dir` points at the central agent-run store. Without it the run-record
  flip is a silent no-op, so pass it.
- The runner prints ONE JSON envelope to stdout and exits non-zero when anything
  needs human judgment. Do NOT re-run it to "retry" an anomaly — read the JSON.

### Consume the envelope

Top-level keys: `runner_version`, `prs`, `report_data`, `main_sync`, `anomalies`.

Each entry in `prs` carries an `action`:

- `skip` — the PR was not actually MERGED. Zero mutations ran for it.
- `noop` — already cleaned up (local branch, remote branch, and worktree all gone).
- `clean` — verified merged and the cleanup RAN. Not proof it all succeeded: read
  the sub-records before you report the PR cleaned. `test_gate`, `branch`,
  `worktree`, `closeout` (including `run_record_flipped`), and `route`. Confirm
  `branch.local` and `branch.remote` are both true, and relay any
  `closeout.close_failed` / `comment_failed` issue numbers as work left for a
  retry — those keys appear only when a delete or an issue write failed, and
  neither downgrades the `action` or raises an anomaly.
- `halt` — cleanup stopped for that PR; the record names the `anomaly`.

`report_data.open_prs` plus the per-PR records are the raw facts for the "what's
next" report you compose: remaining open PRs in stack order, issues the merge
unblocked, and PENDING acceptance suites now ready for `/spec-dev`. The runner
deliberately does not write that prose.

### Halt on anomaly — surface, never auto-resolve

A non-empty `anomalies` list, or any PR record whose `action` is `halt`, is a
full stop for that PR. Relay the anomaly name and its evidence to Matt and take
no corrective action: the runner already refused to act because the case needs
human judgment. The same holds for an item-level `"action": "flag"` on a `branch`
or `worktree` record (dirty worktree, content not on the default branch, retarget
unverified) even when it is not lifted to the top-level list.

Anomaly names the runner emits: `verification-failed`, `missing-head-ref`,
`missing-remote`, `stranded-squash`, `retarget-discovery-failed`,
`stacked-pr-appeared`, `worktree-lookup-failed`, `worktree-status-failed`,
`worktree-prune-failed`, `diff-read-failed`, `sync-failed`, `env-sync-failed`,
`no-test-command`, `red-main`, `empty-suite`, `collection-error`, and the
top-level `project-not-found` (a `--project` key that is not in the registry).

## Hard boundaries

- **Never merges, approves, or closes a PR.** The runner has no such call.
- **Never force-deletes a branch with unmerged commits.** Content not proven on
  the default branch is flagged, never deleted.
- **Never watches or polls for merges.** Matt invokes it; there is no loop.
- **Verify before acting.** Merge state comes from the runner's own `gh pr view`
  read, never from the invocation wording.

## Out of scope

- Merge-order dashboards beyond the "what's next" report.
- Closing issues unrelated to the merged PRs.
- Making the runner emit the human-facing report (it stays model-driven).
