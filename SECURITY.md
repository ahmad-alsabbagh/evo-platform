# Security Policy

## Reporting

Do not report vulnerabilities in public issues. Use a private security channel maintained by the repository owners.

## Baseline

- Never commit secrets, credentials, or production data.
- Validate all external input at the API boundary.
- Keep dependencies locked and patched.
- Treat model output and tool arguments as untrusted input.
- Require explicit authorization for side-effecting tools.
