# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Email: security@agentregress.dev

We will acknowledge your report within **48 hours** and provide a remediation
timeline within 7 days.

Public disclosure follows 90 days after the report date, or after a patch ships,
whichever comes first.

## Scope

This policy covers the core library (`src/agent_regress/`). Third-party
integrations are covered on a best-effort basis.

## What We Consider a Vulnerability

- Code execution via malformed input to any public API function
- Credential leakage via log output or error messages
- Dependency with a known CVE in the default install

## Out of Scope

- Issues in optional dependencies when not installed
- Security issues in user-provided agent callables passed to `compare()`
