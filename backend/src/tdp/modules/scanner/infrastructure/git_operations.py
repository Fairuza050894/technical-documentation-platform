import contextlib
import shutil
import subprocess
import tempfile


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
    except (subprocess.CalledProcessError, OSError) as exc:
        cleanup_temp_dir(temp_dir)
        detail = exc.stderr.strip() if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        raise RuntimeError(f"Failed to clone repository: {detail}") from exc
    return temp_dir


def cleanup_temp_dir(path: str) -> None:
    with contextlib.suppress(OSError):
        shutil.rmtree(path, ignore_errors=True)
