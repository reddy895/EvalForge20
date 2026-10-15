"""Module entry point executing 'python -m evalforge'."""

import sys

from app.cli.main import cli_app


def main() -> None:
    """Forward command-line invocation from python -m evalforge to cli_app."""
    # If invoked directly as 'python -m evalforge report <run_id> ...' without 'export',
    # rewrite sys.argv so typer routes to export sub-command seamlessly
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        if len(sys.argv) > 2 and sys.argv[2] not in ("export", "--help", "-h"):
            sys.argv.insert(2, "export")

    cli_app()


if __name__ == "__main__":
    main()
