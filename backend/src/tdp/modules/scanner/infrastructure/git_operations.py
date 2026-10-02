import shutil
import tempfile
from contextlib import suppress

from git import Repo


def clone_repository(url: str, branch: str = "main", depth: int = 1) -> str:
    temp_dir = tempfile.mkdtemp(prefix="tdp_scan_")
    try:
        Repo.clone_from(url, temp_dir, branch=branch, depth=depth, single_branch=True)
    except Exception:
        cleanup_temp_dir(temp_dir)
        raise
    return temp_dir


def cleanup_temp_dir(path: str) -> None:
    with suppress(OSError):
        shutil.rmtree(path, ignore_errors=True)
