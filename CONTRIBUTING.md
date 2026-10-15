# Contributing to EvalForge20

Thank you for your interest in contributing to EvalForge20!

## 1. Development Principles

- **Local First**: Every feature must work offline without requiring paid API keys or mandatory cloud services.
- **Evidence Driven**: Implement real evaluators with mathematical rigor; never generate fabricated metrics.
- **Clean Architecture**: Preserve the separation between Domain, Application, Providers, Evaluators, and API/CLI.
- **Automated Tests**: Every new feature or fix must include unit and integration tests.

## 2. Setting Up Your Environment

```bash
# Clone the repository
git clone https://github.com/reddy895/EvalForge20.git
cd EvalForge20

# Create virtual environment with Python 3.11+
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt
```

## 3. Git Commit Conventions

We follow Conventional Commits:
- `feat:` new feature or capability
- `fix:` bug fix
- `test:` test addition or improvement
- `docs:` documentation updates
- `chore:` dependency or configuration maintenance
- `refactor:` code restructuring without changing behavior

## 4. Quality Gates

Before submitting a Pull Request, ensure:
```bash
./.venv/bin/ruff check .
./.venv/bin/ruff format .
./.venv/bin/pytest
```
