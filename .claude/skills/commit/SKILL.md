---
name: commit
description: |
  Commit the working changes as clean, well-structured git commits, push the
  branch, and confirm before opening a PR. Use when the owner types /commit, asks
  to commit or save changes to git, or after finishing a piece of work.
license: MIT
metadata:
  user-invocable: true
  slash-command: /commit
  model: default
  proactive: false
---

# Commit

Turn a dirty working tree into a clean, reviewable branch. This skill never
merges and never closes an issue — PR linkage closes issues on merge, and
merging is the owner's job.

## Process

### Step 0: Branch check

```bash
git branch --show-current
```

Never commit on `main`. If HEAD is on `main`, propose a branch name from the
changes (`fix/gui-escaping`, `feat/skill-pack`) and create it before committing:

```bash
git checkout -b <type>/<short-description>
```

When you are working in a linked worktree, write the worktree path LITERALLY in
every `git -C <abs> ...` invocation. The no-main-commit hook cannot expand shell
variables, so a `$VAR` path reads to it as an unknown tree and the commit is
refused.

### Step 1: Survey the changes

```bash
git status --short
git diff
git log --oneline -5
```

Read the FULL diff so every change lands in the right commit, and match the
repo's commit style from the recent log.

Watch for a trap that has bitten this repo: a **staged new file follows a branch
switch**. If you staged a file and then moved to a sibling branch, run
`git restore --staged <file>` before committing, or the file leaks into the wrong
PR.

### Step 2: Group into logical commits

Group related files by type; one commit per group.

| Category | Commit type |
|----------|-------------|
| New functionality | `feat:` |
| Bug fixes | `fix:` |
| Docs (`*.md`) | `docs:` |
| Tests / acceptance suites | `test:` |
| Config / maintenance | `chore:` |

When the work traces to an issue, scope the commit to it: `feat(#237): ...`.

Stage each group and commit, ending the message with the environment's required
commit footer:

```bash
git add <specific files>
git commit -m "$(cat <<'EOF'
<type>(#<issue>): <short description>

<optional body>

Claude-Session: <session-url>
EOF
)"
```

Done when every file from `git status --short` is staged into exactly one commit
and `git status` is clean. Expect the repo's pre-commit hooks (ruff) to gate the
commit: fix the lint at the offending line and re-commit rather than bypassing
the hook, and never widen repo-global config to satisfy a hook.

### Step 3: Push, then verify the push actually landed

```bash
git push -u origin <branch-name>
```

A "pushed" line in your own output is not evidence. Verify against the remote:

```bash
forge check push-landed --repo <repo-abs-path> --remote origin --branch <branch-name> --sha "$(git -C <repo-abs-path> rev-parse HEAD)"
```

Exit 0 means the sha is on `origin/<branch>`. Non-zero means the push did not
reach the remote: recover and re-push before reporting done.

### Step 4: Confirm the PR before opening it

Creating a PR is a mutation, so confirm before opening one. Never auto-open it,
and never auto-merge it. On approval:

```bash
gh pr create --base main --title "<type>(#<issue>): <short description>" --body "$(cat <<'EOF'
## Summary
<1-3 bullets>

## Spec
Closes #<issue-number>

## Test Plan
- [x] <what was run and the result>

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

A **suite** PR (one that only commits PENDING acceptance tests) must say
`References #<n>` instead of a closing keyword — a closing keyword closes the
build issue the moment the suite merges, before anything is built.

Confirm the base is the default branch. Read the base the PR actually got, then
check that value — a hardcoded `main` here just compares `main` to the default
branch and always passes without reading the PR:

```bash
BASE=$(gh pr view <pr-number> --json baseRefName -q .baseRefName)
```

```bash
forge check build-pr-base --base "$BASE"
```

## Output Format

```
**Commits created:**
1. `<type>(#<issue>): <message>`

{Pushed to origin/<branch> | PR: <url>}
```

## What This Skill Does NOT Do

- Merge or approve a PR, or close an issue directly.
- Commit on `main`.
- Bypass a failing pre-commit hook.
