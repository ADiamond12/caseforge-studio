# Screenshots

This folder stores public-safe screenshots used by the GitHub README and portfolio site.

Current capture:

- `web-app.png`: local CaseForge Studio web app with the default sample brief and generated blueprint preview.
- `web-app-mobile.png`: narrow viewport check for the same reviewer flow.

Refresh flow:

```powershell
python -m caseforge serve --host 127.0.0.1 --port 8127
```

Open `http://127.0.0.1:8127`, wait for the sample blueprint to render, and capture the workspace without local file paths or generated output directories visible.
