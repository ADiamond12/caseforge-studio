# CaseForge Studio Demo Storyboard

Use this storyboard for a short public-safe walkthrough. The brief is synthetic and does not reference any workplace material.

## 60-Second Reviewer Flow

1. Open the local app at `http://127.0.0.1:8127`.
2. Load the operations-planning preset.
3. Show the input readiness panel: the app checks whether the brief has enough scope before saving anything.
4. Click **Preview only** and point out that deterministic planning works without external credentials.
5. Click **Forge blueprint** and show the export bundle paths for Markdown, JSON, and summary output.
6. Open recent runs and compare two saved dossiers.
7. Close with the proof chain: rough brief -> structured dossier -> saved artifact -> comparison decision.

## Screenshots To Capture

- `docs/screenshots/web-app.png`: generated dossier, export bundle, saved runs, and compare controls visible.
- `docs/screenshots/web-app-mobile.png`: same flow on a narrow viewport.

## Clean Output Folder

For a repeatable reviewer run that keeps generated artifacts out of the working tree, set:

```powershell
$env:CASEFORGE_OUTPUT_ROOT="$PWD\.caseforge-review-output"
python -m caseforge serve --host 127.0.0.1 --port 8127
```

## What To Say

CaseForge is not a chatbot wrapper. The value is the reviewable planning workflow: it turns a rough brief into a structured implementation dossier, persists the result, and lets a reviewer compare alternate runs before committing to a build path.
