# Security Policy for EvalForge20

## 1. Supported Versions

| Version | Supported |
|---|---|
| `0.1.x` | :white_check_mark: |

## 2. Security Design Principles

- **No Arbitrary Code Execution**: Datasets and evaluator rules must never execute untrusted Python code. All assertions and checks are predefined and safe.
- **Controlled Tool Execution**: AI agent evaluators use strict allowlists (`DeterministicMockAgent`). Shell execution and arbitrary subprocesses are prohibited by default.
- **Automatic Secret Redaction**: Application logs filter and redact API keys (`sk-...`, `ls__...`), Bearer tokens, and secrets via `SecretRedactionFilter`.
- **Data Privacy & Retention**: JSON reports support optional masking of raw prompt inputs and model outputs (`--redact-inputs`, `--redact-outputs`).
- **No Silent Data Sharing**: Local evaluation data is never transmitted to LangSmith or third parties unless explicitly requested via CLI commands or settings.

## 3. Reporting a Vulnerability

If you discover a security vulnerability in EvalForge20, please do not file a public issue. Instead, report it privately to the maintainers at `security@evalforge20.org` or open a private GitHub Advisory.
