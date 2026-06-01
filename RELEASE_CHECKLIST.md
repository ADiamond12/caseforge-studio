# Release Checklist

Use this before calling a CaseForge Studio version ready to use or share.

## Product

- The web app loads without console-breaking behavior.
- `POST /api/dossiers` works and persists a blueprint artifact.
- `POST /api/dossiers/preview` works without persistence.
- `GET /api/dossiers` returns recent saved runs.
- `GET /api/dossiers/compare` compares two saved runs.
- `GET /api/dossiers/<slug>` returns a loadable blueprint payload.
- If `provider=openai` is requested without credentials, the app falls back cleanly.
- If OpenAI credentials are configured, the live overlay path is explicitly tested.
- If a public sample blueprint is included, `examples/sample-blueprint.md` is current and readable.

## Verification

- Run `python -m unittest discover -s tests -v`
- Smoke-test `GET /health`
- Smoke-test `GET /`
- Generate one blueprint from the CLI
- Generate one blueprint from the UI
- Run a high-risk secret scan for API keys, bearer tokens, private keys, seed phrases, credentials, and local absolute paths.
- Run `git diff --check` before committing.
- Inspect the built sdist/wheel file list before publishing packages.
- Review Docker context with `docker build` or `.dockerignore` inspection before sharing the image.

## Documentation

- `README.md` reflects the current commands and endpoints.
- `CHANGELOG.md` reflects completed unreleased work.
- If a curated sample blueprint is included for public sharing, it is current and sanitized.
- Any new behavior is described briefly and concretely.
- Screenshot files open correctly and do not show local paths, credentials, browser profile data, or private customer material.

## Industry Readiness

- The deterministic fallback and local-first story are still true.
- The live product path is easy to explain in a quick handoff.
- The strongest tradeoff is explicit.
- The sample prompt and sample output both feel intentional.
- Path traversal checks for saved-run loading and static output serving are covered by tests.
- Browser console output is checked during the web app smoke test.

## Cleanup

- Remove throwaway outputs that do not support the current release story.
- Keep one strong sample blueprint.
- Do not leave stale claims about endpoints or features in docs or generated artifacts.
- Confirm `.github/workflows/ci.yml` and `.github/workflows/release.yml` still match the packaging story.
