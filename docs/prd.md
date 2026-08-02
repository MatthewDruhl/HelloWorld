# PRD: HelloWorld — pipeline-deck test target

## Problem Statement

pipeline-deck needs a disposable repo to exercise its full launch flow (repo
pick → issue list → routed launch → live session → answered gate) without
firing real pipeline work at a production client repo.

## Solution

A minimal Python package with pytest wired, so every pipeline skill has a real
codebase to act on and a real test gate to satisfy. Seed issues drive the deck
picker's routing.

## End Goal

Any pipeline-deck change can be smoke-tested end to end against HelloWorld: a
launch reaches a real session, the session does real work, its PR passes the
test gate, and `/merged` cleans up — with zero risk to client repos. The repo
grows a second language codebase once the Python flow is solid.

## User Stories

### US-1: Greeting function — [M1]

**As a** deck operator, **I want** a trivial `greet(name)` function with a
passing test, **so that** the pipeline has real code + a real gate to run
against.

**Acceptance criteria:**
- [x] `hello.greet(name)` returns `"Hello, {name}!"`
- [x] `uv run pytest` passes

## Milestones

**M1: Walking skeleton — "the repo builds and its test gate is green"**
Covers US-1.

**Milestone log:**
- 2026-08-02: **M1 COMPLETE.** `hello.greet` + passing test; pytest green.
  Repo registered in pipeline-deck (`repos.local.json`) and the marvin project
  registry. Seed issues filed to drive the deck picker.

## Out of Scope

- Anything non-trivial: HelloWorld exists to exercise the deck, not to be a
  real product. Real features are just vehicles for testing the flow.

## Open Questions

None.
