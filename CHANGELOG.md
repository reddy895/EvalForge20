# Changelog

All notable changes to EvalForge20 are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses semantic versioning for release tags.

## [Unreleased]

### Added

- Optional shared-secret bearer authentication (`AUTH_TOKEN`) for self-hosted deployments.
- Request body ceiling, per-client rate limiting, and expanded security headers.
- SSRF validation with DNS resolution and private/metadata address blocking.
- Startup recovery that marks interrupted evaluation runs as `interrupted`.
- Dataset preview, pagination, integrity fingerprint, duplication, and individual case deletion APIs.
- Import duplicate detection with explicit warnings and strict UTF-8 validation.
- Judge reproducibility metadata (prompt version, rubric hash, execution config) and a prompt-injection guard.
- Secret redaction in structured logs.
- Non-root multi-stage production Docker image, `.dockerignore`, migration entrypoint, healthchecks, and optional PostgreSQL Compose profile.
- Database backup and restore scripts.
- Migration verification, TypeScript typecheck, and advisory dependency audit in CI.
- Professional documentation: security policy, privacy notice, contribution guide, code of conduct, and this changelog.

### Fixed

- Experiment listing reported the page size instead of the true total.
- Evaluation lookup silently swallowed internal errors while falling back to workflow executions.
- Cancellation could be overwritten by a late completion write.
- Health endpoints reported database connectivity as always healthy and exposed hardware details.
- The frontend dataset view consumed a different response shape than the API produced and showed fabricated fallback datasets.
- Health/readiness probes now reflect real database connectivity.

### Changed

- README rewritten to describe the actual Vite/React + FastAPI architecture and an honest feature matrix.
- Project license metadata aligned with the AGPL-3.0 `LICENSE` file.
- Backend lint baseline cleaned; `ruff check` passes.

### Security

- Log redaction for credentials and bearer tokens.
- Strict UTF-8 dataset decoding instead of silent replacement.
- Dataset export filenames sanitized.

## [2.1.0]

- Prior baseline: visual evaluation playground, Ollama integration, evaluator suite, results workspace, analytics, and initial test coverage.
