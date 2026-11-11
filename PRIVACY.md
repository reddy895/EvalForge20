# Privacy and Data Handling

EvalForge20 is self-hosted software. The operator deploying it is responsible for the data it processes.

## What is stored

- Datasets and test cases (prompts, reference answers, optional context, tags, metadata).
- Evaluation runs, per-case model outputs, metrics, timings, token usage, and errors.
- Model/provider catalog metadata and configured provider status.
- Application logs (structured by default in production).

## Where data goes

- **Local Ollama:** prompts and outputs stay on the machine hosting Ollama unless you configure a remote endpoint.
- **Cloud providers:** if you configure a cloud provider adapter and run an evaluation against it, prompts, context, and outputs are sent to that provider under its terms. EvalForge does not claim local-only processing in that case.
- **LLM-as-a-judge:** the judge model receives the prompt, reference, context, and candidate output as part of the judging request.

## Data minimization and retention

- EvalForge stores what is needed to reproduce and inspect evaluations. It does not intentionally collect end-user personal data beyond dataset content an operator uploads.
- There is no automatic retention expiry. Operators should define retention and delete datasets/runs they no longer need.
- Deleting a dataset cascades to its test cases; runs referencing the dataset keep their dataset name snapshot but the foreign key is set to null.

## Deletion

Use the dataset delete endpoint/UI and database tooling for bulk deletion. For a full wipe, stop the service and remove the database file or drop the PostgreSQL database, then run migrations again.

## Logs

Logs may contain prompts or error messages originating from provider responses. Secret-looking keys are redacted, but operators should treat logs as potentially sensitive and restrict access. Do not enable debug logging in production unless necessary.

## Cookies and analytics

The EvalForge20 frontend does not include third-party analytics or advertising trackers. If authentication is enabled via `AUTH_TOKEN`, the token is supplied by the client; no tracking cookies are required by the core application.
