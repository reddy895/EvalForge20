# Security Policy

## Supported versions

EvalForge20 is developed on the `main` branch. Security fixes target the latest release.

## Reporting a vulnerability

Please **do not** open a public issue for a security vulnerability. Report it privately to the repository maintainer through GitHub's private vulnerability reporting ("Security" → "Report a vulnerability") or by contacting the maintainer listed on the repository profile.

Include:

- A description of the issue and affected endpoint/component.
- Reproduction steps or a proof of concept.
- Impact assessment (confidentiality, integrity, availability).
- The version/commit tested.

We will acknowledge reports as quickly as possible and coordinate disclosure after a fix is available.

## Threat model and access model

EvalForge20 is designed for **trusted, self-hosted, single-user or small-team use** by default. It is **not** a multi-tenant SaaS.

- The server binds to `127.0.0.1` by default.
- Setting `ENVIRONMENT=production` forces the operator to either bind to loopback or configure `AUTH_TOKEN`.
- `AUTH_TOKEN` is a single shared bearer secret. It is not a user account system, does not provide per-user authorization, and does not support RBAC.
- If you expose EvalForge publicly, place it behind an authenticating reverse proxy (and HTTPS) and use PostgreSQL with backups.
- Datasets and model outputs are untrusted input. Do not execute uploaded content as code. The code-execution evaluator is sandboxed by design but is not a hardened isolation boundary for hostile multi-tenant workloads.

## Security controls in this repository

- Centralized exception handling that does not leak stack traces to clients.
- Server-side Pydantic validation and parameterized SQLAlchemy queries.
- Upload size limits, content-type/format checks, strict UTF-8 decoding, and sanitized filenames.
- Optional request-body ceiling, per-client rate limiting, and security headers.
- SSRF validation that resolves DNS and rejects loopback, private, link-local, reserved, and cloud-metadata addresses unless `ALLOW_PRIVATE_PROVIDER_ENDPOINTS=true`.
- Secret redaction in structured logs.
- Optional bearer authentication for `/api` routes, with health probes exempt.
- Non-root container execution.

## Known limitations

- In-process background execution: a hard process kill can interrupt runs. Interrupted runs are reconciled to `interrupted` on restart, never marked successful.
- Rate limiting is in-process; multi-worker deployments should also enforce limits at the proxy.
- No built-in audit-log retention policy or compliance certification.
- Cloud provider adapters are configuration-dependent; only Ollama and the mock provider are continuously exercised in CI.

## Secrets

Never commit `.env` files, API keys, tokens, database dumps, or uploaded datasets. Rotate any credential that may have been exposed. Use environment-based secrets or a secrets manager.
