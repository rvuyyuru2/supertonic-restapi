# Security Policy

## Supported Versions

The following versions of Supertonic TTS are currently supported with security updates:

| Version | Supported              |
| ------- | ---------------------- |
| 1.0.x   | ✅ Supported           |
| 0.9.x   | ⚠️ Security fixes only |
| < 0.9   | ❌ Not supported       |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. Email the maintainers directly at [security@supertonic.ai](mailto:security@supertonic.ai)
3. Include the following in your report:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact of the vulnerability
   - Any suggested fixes (optional)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Fix Timeline**: Depending on severity (see below)

| Severity | Fix Timeline |
| -------- | ------------ |
| Critical | 24-72 hours  |
| High     | 7 days       |
| Medium   | 30 days      |
| Low      | Next release |

## Security Best Practices

When deploying Supertonic TTS:

1. **API Keys**: Use strong API keys and rotate them regularly
2. **Network**: Run behind a reverse proxy with HTTPS
3. **Authentication**: Enable and enforce API key authentication in production
4. **Updates**: Keep your installation updated to the latest version
5. **Logging**: Monitor logs for suspicious activity
6. **Rate Limiting**: Implement rate limiting to prevent abuse

## Dependencies

We regularly update dependencies to address security vulnerabilities. Run `pip audit` or use [Dependabot](https://docs.github.com/en/code-security/supply-chain-security/about-dependabot-version-updates) to stay updated.

## Scope

This security policy covers:

- The Supertonic TTS API server
- Authentication and authorization mechanisms
- API endpoints
- Configuration handling

This policy does NOT cover:

- Client-side applications using the API
- Third-party integrations
- Deployment infrastructure (please consult your cloud provider's security docs)

---

Thank you for helping keep Supertonic TTS secure!
