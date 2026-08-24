---
name: tdd
description: |
  Test-driven development discipline: red-green-refactor in vertical tracer-bullet
  slices. Use when building a feature or fixing a bug test-first, or when someone
  mentions TDD or red-green-refactor. Also the inner-loop philosophy every
  /spec-dev implementer follows. NOT for backfilling tests onto existing code
  ("add integration tests for X" is a test-writing task, not TDD).
license: MIT
metadata:
  user-invocable: true
  slash-command: null
  model: default
  proactive: false
---

# Test-Driven Development

The inner loop of this repo's build pipeline. `/spec-dev` owns the outer loop
(contract, plan, review, PR); this skill owns what happens between "the
acceptance test is PENDING" and "the acceptance test is green". Routing for the
whole pipeline is in `AGENTS.md`.

## Philosophy

**Core principle:** tests verify behavior through public interfaces, not
implementation details. Code can change entirely; tests should not. A good test
reads like a specification ("user can checkout with a valid cart") and survives
refactors because it exercises public APIs, not internal structure. The warning
sign of a bad test: it breaks when you rename an internal function without
changing behavior.

See [tests.md](tests.md) for good and bad examples, [mocking.md](mocking.md) for
mocking guidelines, [deep-modules.md](deep-modules.md) and
[interface-design.md](interface-design.md) for shaping the interface you are
about to test, and [refactoring.md](refactoring.md) for the refactor step.

## Anti-Pattern: Horizontal Slices

**DO NOT write all tests first, then all implementation.** That is horizontal
slicing: treating RED as "write all tests" and GREEN as "write all code".

It produces bad tests:

- Tests written in bulk test *imagined* behavior, not *actual* behavior.
- You end up testing the *shape* of things (data structures, signatures) rather than caller-facing behavior.
- Tests become insensitive to real changes: they pass when behavior breaks and fail when behavior is fine.
- You outrun your headlights, committing to test structure before understanding the implementation.

**Correct approach:** vertical slices via tracer bullets. One test, one
implementation, repeat. Each test responds to what the previous cycle taught you.
Because you just wrote the code, you know exactly what behavior matters and how
to verify it.

```
WRONG (horizontal):
  RED:   test1, test2, test3, test4, test5
  GREEN: impl1, impl2, impl3, impl4, impl5

RIGHT (vertical):
  RED->GREEN: test1->impl1
  RED->GREEN: test2->impl2
  RED->GREEN: test3->impl3
```

## The Acceptance Test Is Not Yours to Change

Inside a `/spec-dev` build, the committed acceptance test is the contract,
authored upstream and approved by the owner. You may add unit tests freely. You
MUST NOT modify, delete, weaken, or skip an acceptance test. If a targeted
acceptance test looks wrong, STOP and report it as a possible spec change rather
than editing it green. The deterministic weaken-check will catch you anyway. It
compares two FILES, so snapshot the committed side out of the default branch
first — without that step the `--old` path does not exist:

```bash
git -C <repo-abs-path> show main:tests/test_slice.py > /tmp/suite-ref-slice.py
```

```bash
forge check acceptance-integrity --old /tmp/suite-ref-slice.py --new tests/test_slice.py
```

The only legitimate edit is removing the PENDING marker once the behavior is
really green. In this pytest repo the marker convention is checked by:

```bash
forge validate pending-markers tests/test_slice.py
```

## Workflow

### 1. Planning

Before writing any code:

- [ ] Confirm what interface changes are needed.
- [ ] Confirm which behaviors to test, in priority order.
- [ ] Identify opportunities for [deep modules](deep-modules.md): small interface, deep implementation.
- [ ] Design interfaces for [testability](interface-design.md).
- [ ] List the behaviors to test, not the implementation steps.
- [ ] Get approval on the plan.

Ask: "What should the public interface look like? Which behaviors matter most?"

**You cannot test everything.** Confirm exactly which behaviors matter. Focus
effort on critical paths and complex logic, not every conceivable edge case.

### 2. Tracer Bullet

Write ONE test that confirms ONE thing about the system:

```
RED:   write a test for the first behavior -> it fails
GREEN: write minimal code to pass -> it passes
```

That is the tracer bullet. It proves the path works end to end.

### 3. Incremental Loop

For each remaining behavior:

```
RED:   write the next test -> it fails
GREEN: minimal code to pass -> it passes
```

Rules:

- One test at a time.
- Only enough code to pass the current test.
- Do not anticipate future tests.
- Keep tests on observable behavior.

**Run only what you are driving.** In the loop, run the single test (or the one
targeted file) you are turning green, with fail-fast on, so each cycle reads one
failure rather than a wall of output:

```bash
uv run pytest tests/test_slice.py -x -q
```

Do NOT run the full suite every cycle. That is the full-suite gate's job, once,
at the end (see `/spec-dev` step 5). The concept is framework-neutral; the
fail-fast idiom is per stack (pytest `-x`, vitest and jest `--bail`,
`go test -failfast`).

### 4. Refactor

After the tests pass, look for [refactor candidates](refactoring.md):

- [ ] Extract duplication.
- [ ] Deepen modules: move complexity behind simple interfaces.
- [ ] Apply SOLID principles where they fall out naturally.
- [ ] Consider what the new code reveals about the existing code.
- [ ] Run the tests after each refactor step.

**Never refactor while RED.** Get to GREEN first.

## Checklist Per Cycle

```
[ ] Test describes behavior, not implementation
[ ] Test uses the public interface only
[ ] Test would survive an internal refactor
[ ] Code is minimal for this test
[ ] No speculative features added
```
