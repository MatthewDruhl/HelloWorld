# Project Registry

The forge-format project registry for this repo, read by every registry-driven
runner via `forge --registry state/projects.md ...`. Grammar: `## Project: <key>`
followed by `- **Field:** <value>` bullets (see `src/forge/registry.py`).
`Language` is required; `~` paths are expanded at parse time, so this file stays
host-agnostic and carries no absolute home directory.

## Project: HelloWorld

The standing TESTING AND DEMO project (owner decision, 2026-08-24): every
pipeline demo, dry run, and experiment targets HelloWorld. `pipeline-forge`
becomes a target only after a production release.

- **Path:** ~/Projects/HelloWorld
- **Repo:** MatthewDruhl/HelloWorld
- **Language:** python
- **Default branch:** main
- **Test Command:** uv run pytest -q
- **Remote:** origin
- **Worktree root:** ~/Projects/HelloWorld-worktrees

## Project: pipeline-forge

- **Path:** ~/Projects/pipeline-forge
- **Repo:** MatthewDruhl/pipeline-forge
- **Language:** python
- **Default branch:** main
- **Test Command:** uv run pytest -q
- **Remote:** origin
- **Worktree root:** ~/Projects/pipeline-forge-worktrees
