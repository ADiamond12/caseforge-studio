# Screenshots

This folder stores public-safe screenshots used by the GitHub README and portfolio site.

Current capture:

- `web-app.png`: local CaseForge Studio web app with the default sample brief and generated blueprint preview.
- `web-app-mobile.png`: narrow viewport check for the same reviewer flow.

Refresh flow:

```powershell
python -m caseforge serve --host 127.0.0.1 --port 8127
```

Open `http://127.0.0.1:8127`, load the AI ops copilot preset, generate one deterministic saved run, and capture the workspace without absolute local paths, credentials, browser profile data, or private material. Relative `outputs/<slug>/...` artifact paths are acceptable because they are part of the product workflow.
