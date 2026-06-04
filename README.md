# CaseForge Studio

CaseForge Studio turns a rough operational software brief into an implementation blueprint that a reviewer can inspect before any build work starts. It ships with a local web app, CLI, HTTP API, persisted run history, export manifests, comparison flow, and an optional OpenAI overlay that refines the final blueprint without becoming the only path through the product.

The core thesis is simple: a useful idea should become scoped, explainable, comparable, and ready for a delivery conversation. CaseForge turns vague prompts into reviewable artifacts instead of treating the generated text as the final answer.

## Useful In Practice For

- Turning a rough implementation brief into a structured planning dossier that can be reviewed before coding starts.
- Comparing two alternate delivery framings when the first generated plan is not strong enough.
- Producing Markdown, JSON, summary, and export-manifest artifacts that make a planning run easy to hand off or revisit later.
- Demonstrating how an optional AI provider can sit behind a deterministic product path instead of becoming the whole product.

## What This Project Proves

- Deterministic by default, so the product remains usable without external services.
- Optional live-provider overlay for stronger AI-assisted refinement when credentials are available.
- Multiple surfaces from one shared service layer: CLI, browser UI, and HTTP API.
- Saved runs and comparison views make iteration concrete instead of relying on a single generated answer.
- Fast to evaluate in a handoff: brief in, blueprint out, compare runs, choose the strongest implementation path.

## Reviewer Proof

- **Problem:** rough implementation ideas are often too vague to estimate, review, or hand off cleanly.
- **First command:** `powershell -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1`
- **Proof artifact:** a persisted dossier bundle under `outputs/<slug>/` with Markdown, JSON, summary, and export-manifest files.
- **Visual proof:** `docs/screenshots/web-app.png` and `docs/screenshots/web-app-mobile.png` show the local planning workspace.
- **Validation:** unittest coverage for deterministic generation, saved runs, export manifests, comparison, API behavior, and fallback paths.
- **Current limitation:** the OpenAI refinement layer is optional; the public demo is intentionally deterministic and local-first.

## Product Surface

- Planner, architect, evaluator, and delivery-path stages
- Markdown, JSON, and summary export under `outputs/` for persisted local runs
- Export manifest that tells reviewers which artifact to open first and why
- Local web app with readiness feedback, blueprint preview, saved-run browsing, export bundle, and comparison
- Local HTTP API for generation, preview, retrieval, and compare flows
- Optional OpenAI Responses API overlay with deterministic fallback
- Standard-library-only backend runtime
- CI workflow plus tag-based release workflow

## Architecture Snapshot

```text
Brief
  -> normalization
  -> planner
  -> architect
  -> evaluator
  -> delivery path
  -> blueprint export
  -> optional OpenAI public-facing overlay
```

The deterministic path is the primary product path. The live provider is an enhancement layer, not a dependency for the base workflow.

## Local Product Walkthrough

The fastest way to evaluate the project is through the local web app:

1. Start the server with `python -m caseforge serve --host 127.0.0.1 --port 8127`.
2. Open `http://127.0.0.1:8127`.
3. Load one preset brief and use **Preview only** to inspect the deterministic output without writing files.
4. Use **Forge blueprint** to create a persisted run under `outputs/<slug>/`.
5. Review the export bundle: Markdown, JSON, and summary paths should appear together.
6. Open the recent-run panel, select two saved runs, and compare score, preset, provider path, strengths, and risks.

The demo is designed to show product behavior, not just a CLI command: input readiness feedback, recovery messaging, backend status, saved-run history, comparison, export paths, and fallback behavior are visible in one screen.

## Reviewer Demo Command

For a repeatable local review, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
```

The script installs the package, runs the unittest suite, previews a deterministic blueprint from a committed intralogistics readiness brief, persists two saved runs, compares them, and prints the recent-run list. After that, start the web app and inspect the same saved-run comparison visually:

```powershell
python -m caseforge serve --host 127.0.0.1 --port 8127
```

This path gives a reviewer one clear chain: rough brief -> deterministic dossier -> saved artifact bundle -> export manifest -> comparison decision.

## Demo Screenshot

![CaseForge Studio local web app](docs/screenshots/web-app.png)

## Quickstart

From the `caseforge-studio` project root:

```powershell
python -m pip install -e .
```

Generate a saved intralogistics blueprint:

```powershell
python -m caseforge create --brief-file examples/briefs/intralogistics-commissioning-planner.md --preset product
```

Write artifacts to a separate review folder when running demos, tests, or shared machines:

```powershell
$env:CASEFORGE_OUTPUT_ROOT="$PWD\.caseforge-review-output"
python -m caseforge create --brief-file examples/briefs/intralogistics-commissioning-planner.md --preset product
```

Preview a blueprint without persistence:

```powershell
python -m caseforge create "Build a release readiness planner for engineering leads." --preset full-stack --preview --json
```

Run the local web app:

```powershell
python -m caseforge serve --host 127.0.0.1 --port 8127
```

Then open `http://127.0.0.1:8127`.

Run tests:

```powershell
python -m unittest discover -s tests -v
```

Build distributable artifacts:

```powershell
python -m pip install --upgrade build
python -m build
```

## Optional OpenAI Overlay

The live provider path is optional. Without credentials, the app falls back to the deterministic path and explains why.

```powershell
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_MODEL="gpt-5-mini"
python -m caseforge create "Build an AI operations copilot." --preset ml --provider openai --preview --json
```

Supported environment variables:

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_RESPONSES_ENDPOINT`
- `OPENAI_BASE_URL` remains supported as a legacy alias and must point to the full Responses API endpoint.
- `CASEFORGE_OUTPUT_ROOT` controls where saved Markdown, JSON, summary, and export-manifest artifacts are written.

See [.env.example](.env.example) for the default shape.

## CLI Commands

Create from inline text:

```powershell
python -m caseforge create "Design an operations copilot that summarizes incidents and proposes follow-up work."
```

Create from a file:

```powershell
python -m caseforge create --brief-file examples/briefs/ai-ops-copilot.md --mode "AI workflow product" --goal "Emphasize shipping discipline" --preset full-stack
```

List recent blueprints:

```powershell
python -m caseforge list
```

Compare two persisted blueprints:

```powershell
python -m caseforge compare <slug-a> <slug-b> --markdown
```

Open a persisted record:

```powershell
python -m caseforge show <slug>
```

## HTTP API

- `GET /health`
- `POST /api/dossiers`
- `POST /api/dossiers/preview`
- `GET /api/dossiers`
- `GET /api/dossiers/compare?slug=<slug>&slug=<slug>`
- `GET /api/dossiers/<slug>`
- `GET /`

Example request:

```json
{
  "brief": "Build an AI operations copilot that turns incident notes, service metrics, and follow-up tasks into a release-ready action plan.",
  "audience": "Technical stakeholders",
  "mode": "AI assistant",
  "goal": "Emphasize AI decisioning",
  "preset": "ml",
  "provider": "openai",
  "provider_model": "gpt-5-mini"
}
```

## Review Walkthrough

1. Start the web app and paste a rough project idea into the brief box.
2. Preview the blueprint first and check the score, recommendation, architecture section, and delivery path.
3. Persist a run only when the preview is worth keeping.
4. Open the committed sample blueprint at `examples/sample-blueprint.md` or a locally generated artifact under `outputs/<slug>/dossier.md`.
5. Compare two runs to review score movement, provider path, and recommendation changes.
6. Explain why the deterministic path is the default and when the live provider is worth using.
7. Close with the test suite and release checklist.

## Verification

- `python -m unittest discover -s tests -v`
- `python -m build`
- smoke-test `GET /health`
- smoke-test `GET /`
- generate one blueprint through the CLI
- generate one blueprint through the web UI

## Project Layout

```text
caseforge-studio/
|-- .github/
|-- caseforge/
|-- docs/
|-- examples/
|   |-- sample-blueprint.md
|   `-- briefs/
|-- tests/
|-- CHANGELOG.md
|-- RELEASE_CHECKLIST.md
`-- README.md
```

`outputs/` is generated locally at runtime and is intentionally kept out of version control. The committed public sample blueprint lives at `examples/sample-blueprint.md`.

## Release And Security

- Release gating lives in [.github/workflows/ci.yml](.github/workflows/ci.yml) and [.github/workflows/release.yml](.github/workflows/release.yml).
- Release readiness is tracked in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).
- Project history is tracked in [CHANGELOG.md](CHANGELOG.md).
- Security expectations and disclosure guidance live in [SECURITY.md](SECURITY.md).

## Current Limits

- The server is local-first and single-tenant.
- There is no built-in authentication or multi-user access control.
- The OpenAI overlay path should be used only with deliberate credential handling.
- The default runtime is still a local stdlib HTTP server, not a multi-tenant hosted deployment stack.

## Roadmap

- Add a clean deployment wrapper around the local server path
- Capture one intentional live-provider blueprint artifact
- Add stronger browser-level regression coverage
- Promote the best saved blueprint flow into a tighter public release
