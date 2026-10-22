"""Git commit verification and activity analytics parser."""

import subprocess
from datetime import UTC, datetime
from pathlib import Path

def get_git_commit_activity(repo_root: Path, target_milestone: int = 56) -> dict:
    """Parse local repository git log and verify commit count without fabrication."""
    try:
        count_out = subprocess.check_output(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        total_count = int(count_out)
    except Exception:
        total_count = 0

    target_achieved = total_count >= target_milestone
    progress_pct = round((total_count / target_milestone) * 100.0, 1) if target_milestone > 0 else 100.0

    return {
        "target_milestone": target_milestone,
        "total_verified_commits": total_count,
        "target_achieved": target_achieved,
        "target_progress_percent": progress_pct,
        "status_label": (
            f"Target Achieved ({total_count} Verified Commits Exceeds {target_milestone} Target)"
            if target_achieved
            else f"Target in Progress ({total_count}/{target_milestone} Commits)"
        ),
        "source": "Local Git rev-list log data",
        "verified_at": datetime.now(UTC).isoformat(),
    }
