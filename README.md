# HelloWorld

A throwaway target repo for exercising the [pipeline-deck](https://github.com/MatthewDruhl/pipeline-deck)
launch flow end to end: pick this repo in the deck, launch a session against a
seed issue, and watch a real pipeline skill (`/dispatch`, `/spec-up`,
`/spec-dev`, `freeform`) run against disposable code.

Python first; other language codebases get added as the deck hardens.

```bash
uv run pytest        # the pipeline test gate
```
