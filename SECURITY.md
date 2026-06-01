# Security Policy

## Scope

CaseForge Studio is currently a local-first, single-tenant application. It is designed for local validation, product iteration, and reviewer walkthroughs, not for untrusted multi-tenant deployment in its current form.

## Supported Surface

- Local CLI usage
- Local HTTP server started with `python -m caseforge serve`
- Optional OpenAI overlay through explicit environment variables

## Security Expectations

- Do not commit API keys, tokens, or `.env` files.
- Treat persisted blueprint content as local project data unless you intentionally sanitize it for sharing.
- Use the deterministic provider path by default when capturing walkthroughs or testing on untrusted environments.
- Do not expose the local server directly to the public internet without adding authentication, reverse-proxy controls, and deployment hardening.
- If you run the Docker image locally, publish the port to loopback only, for example `-p 127.0.0.1:8127:8127`.

## Reporting

Do not open public issues with secrets, exploit details, or sensitive sample data. Use a private disclosure path through the hosting platform or contact the maintainer directly.

## Known Limits

- No built-in authentication or authorization
- No tenant isolation
- No rate limiting
- Local stdlib HTTP server, not hardened production hosting
- Optional live-provider path depends on external API credentials
