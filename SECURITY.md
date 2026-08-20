# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | ✅ Active support  |
| < 1.0   | ❌ No longer supported |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

### Preferred: GitHub Private Advisory
Use [GitHub's private vulnerability reporting](https://github.com/your-org/AdaptiveAgent/security/advisories/new)
to submit a report. We will acknowledge within **48 hours** and aim to provide a
fix or mitigation within **14 days** for critical issues.

### Alternative: Email
Send details to **security@your-org.example.com**
(replace with your real security contact before publishing).

Please include:
- A description of the vulnerability and its potential impact
- Steps to reproduce or a proof-of-concept
- The version of AdaptiveAgent affected
- Any suggested mitigations

## Disclosure Policy

We follow coordinated disclosure. We ask that you:
- Give us reasonable time to fix the issue before public disclosure
- Not exploit the vulnerability beyond what is needed to demonstrate it

## Security Considerations for Operators

- Set `ENVIRONMENT=production` to enable startup security checks
- Generate strong secrets: `openssl rand -hex 32`
- Never commit `.env` files to source control
- Bind service ports to loopback (`127.0.0.1`) behind a reverse proxy in production
- Enable rate limiting (`RATE_LIMIT_ENABLED=true`)
- Install `sunglasses` for semantic prompt-injection detection
