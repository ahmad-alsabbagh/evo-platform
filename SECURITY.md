# Security Policy

## Reporting

Do not report vulnerabilities in public issues. Use a private security channel maintained by the repository owners.

## CI security gates

Every change should pass secret scanning, dependency auditing, static security analysis, linting, type checking, and tests.

## Secret handling

- Never commit secrets, credentials, or production data.
- Provide database URLs and credentials through environment variables or a managed secret store.
- Rotate credentials immediately after suspected exposure.
- Do not place real tokens in fixtures, documentation, or test logs.

## Runtime baseline

- Validate external input at the API boundary.
- Treat model output and tool arguments as untrusted input.
- Require explicit authorization for side-effecting tools.
- Run application containers as non-root.
- Keep dependencies patched and review migration changes.

## Incident response

1. Disable or rotate the affected credential.
2. Preserve relevant logs and commit identifiers.
3. Assess blast radius and affected artifacts.
4. Patch, test, and deploy the fix.
5. Document the incident and prevention actions.
