import shutil
import subprocess
import tempfile
from contextlib import suppress


def clone_repository(url: str, branch: str = "main", depth: int = 1) -> str:
    temp_dir = tempfile.mkdtemp(prefix="tdp_scan_")
    try:
        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                str(depth),
                "--branch",
                branch,
                "--single-branch",
                url,
                temp_dir,
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        cleanup_temp_dir(temp_dir)
        raise
    return temp_dir


def cleanup_temp_dir(path: str) -> None:
    with suppress(OSError):
        shutil.rmtree(path, ignore_errors=True)
