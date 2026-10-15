"""Security utilities for safe path validation and prevention of path traversal attacks."""

from pathlib import Path

# System directories that must never be targeted by user exports or dataset reads
RESTRICTED_SYSTEM_DIRECTORIES: tuple[str, ...] = (
    "/etc",
    "/usr",
    "/boot",
    "/dev",
    "/proc",
    "/sys",
    "/root",
)


def validate_safe_path(
    target_path: Path | str,
    base_dir: Path | str | None = None,
    must_exist: bool = False,
) -> Path:
    """Validate that target_path is canonical, does not escape base_dir, and does not touch system directories."""
    resolved = Path(target_path).expanduser().resolve()

    # Prevent access to critical operating system directories
    for restricted in RESTRICTED_SYSTEM_DIRECTORIES:
        if str(resolved) == restricted or str(resolved).startswith(restricted + "/"):
            raise ValueError(
                f"Security error: Access to system directory '{restricted}' is restricted: {target_path}"
            )

    # If base_dir is enforced, ensure resolved path is contained within base_dir
    if base_dir is not None:
        resolved_base = Path(base_dir).expanduser().resolve()
        try:
            resolved.relative_to(resolved_base)
        except ValueError as exc:
            raise ValueError(
                f"Security error: Path traversal detected. '{target_path}' escapes base directory '{base_dir}'."
            ) from exc

    if must_exist and not resolved.exists():
        raise FileNotFoundError(f"File not found: {resolved}")

    return resolved
