# Security Policy

## Supported versions

Security fixes are prioritized for the latest version on the `main` branch.

| Version | Support |
| --- | --- |
| Latest `main` | ✅ Active |
| Older revisions | ❌ Best effort only |

## Reporting a vulnerability

Please **do not open a public GitHub issue** for a security vulnerability.

Use GitHub's private vulnerability reporting for this repository when available. If private reporting is unavailable, contact the repository maintainer privately through GitHub.

Please include:

- A clear description of the vulnerability and impact
- Affected component, endpoint, or file
- Reproduction steps or proof of concept
- Affected version/commit
- Suggested mitigation, if known

Do not include API keys, passwords, private documents, personal data, or other secrets in a report.

## Disclosure

Please allow reasonable time for investigation and remediation before publicly disclosing a vulnerability. We will coordinate disclosure with the reporter when appropriate.

## Deployment security

Operators should:

- Never commit `.env` files, API keys, tokens, or credentials.
- Use strong, unique application secrets in production.
- Keep externally exposed services behind appropriate authentication and network controls.
- Enable rate limiting where appropriate.
- Review model-provider and tool permissions before deploying agents with access to private data or external systems.
- Treat retrieved documents and tool outputs as untrusted input and defend against prompt injection.
- Keep dependencies and container images updated.
