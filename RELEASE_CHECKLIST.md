# Release Checklist

Use this before calling a CaseForge Studio version ready to demo or share.

## Product

- The web app loads without console-breaking behavior.
- `POST /api/dossiers` works and persists a dossier.
- `POST /api/dossiers/preview` works without persistence.
- `GET /api/dossiers` returns recent saved runs.
- `GET /api/dossiers/compare` compares two saved runs.
- `GET /api/dossiers/<slug>` returns a loadable dossier payload.
- If `provider=openai` is requested without credentials, the app falls back cleanly.
- If OpenAI credentials are configured, the live overlay path is explicitly tested.
- If a public sample dossier is included, `examples/sample-dossier.md` is current and readable.

## Verification

- Run `python -m unittest discover -s tests -v`
- Smoke-test `GET /health`
- Smoke-test `GET /`
- Generate one dossier from the CLI
- Generate one dossier from the UI

## Documentation

- `README.md` reflects the current commands and endpoints.
- `CHANGELOG.md` reflects completed unreleased work.
- If a curated sample dossier is included for public demo, it is current and sanitized.
- Any new behavior is described briefly and concretely.

## Interview Readiness

- The deterministic fallback story is still true.
- The live product path is easy to explain in under two minutes.
- The strongest tradeoff is explicit.
- The sample prompt and sample output both feel intentional.

## Cleanup

- Remove throwaway outputs that do not support the demo story.
- Keep one strong sample dossier.
- Do not leave stale claims about endpoints or features in docs or generated artifacts.
- Confirm `.github/workflows/ci.yml` and `.github/workflows/release.yml` still match the packaging story.
