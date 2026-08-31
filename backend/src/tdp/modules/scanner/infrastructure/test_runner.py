import subprocess
import sys
from pathlib import Path

from tdp.modules.scanner.domain.model import LintResult, SecurityIssue, SecurityScan, TestSuite


def run_tests(repo_path: str) -> list[TestSuite]:
    root = Path(repo_path)
    suites: list[TestSuite] = []
    cfg_files = {f.name for f in root.iterdir() if f.is_file()}

    if (root / "pytest.ini").exists() or (root / "pyproject.toml").exists():
        suite = _run_pytest(repo_path)
        if suite:
            suites.append(suite)

    if "package.json" in cfg_files:
        if _file_contains(root / "package.json", "jest"):
            suite = _run_jest(repo_path)
            if suite:
                suites.append(suite)

    if "go.mod" in cfg_files:
        suite = _run_go_test(repo_path)
        if suite:
            suites.append(suite)

    return suites


def run_lint(repo_path: str) -> list[LintResult]:
    root = Path(repo_path)
    results: list[LintResult] = []
    cfg_files = {f.name for f in root.iterdir() if f.is_file()}

    if (root / ".flake8").exists() or (root / "pyproject.toml").exists():
        result = _run_flake8(repo_path)
        if result:
            results.append(result)

    eslint_configs = {".eslintrc", ".eslintrc.js", ".eslintrc.json", "eslint.config.js"}
    if cfg_files & eslint_configs:
        result = _run_eslint(repo_path)
        if result:
            results.append(result)

    return results


def run_security_scan(repo_path: str) -> SecurityScan:
    root = Path(repo_path)
    cfg_files = {f.name for f in root.iterdir() if f.is_file()}

    if "requirements.txt" in cfg_files or "pyproject.toml" in cfg_files:
        return _run_pip_audit(repo_path)
    if "package.json" in cfg_files:
        return _run_npm_audit(repo_path)

    return SecurityScan(tool="none")


def _run_pytest(repo_path: str) -> TestSuite | None:
    try:
        # Install dependencies if possible
        root = Path(repo_path)
        if (root / "pyproject.toml").exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", ".", "-q"],
                cwd=repo_path, capture_output=True, text=True, timeout=180,
            )
        if (root / "requirements.txt").exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
                cwd=repo_path, capture_output=True, text=True, timeout=180,
            )
        if (root / "requirements" / "dev.txt").exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements/dev.txt", "-q"],
                cwd=repo_path, capture_output=True, text=True, timeout=180,
            )
        if (root / "requirements" / "test.txt").exists():
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements/test.txt", "-q"],
                cwd=repo_path, capture_output=True, text=True, timeout=180,
            )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--tb=short", "-q", "--no-header"],
            cwd=repo_path, capture_output=True, text=True, timeout=120,
        )
        suite = TestSuite(name="pytest", framework="pytest")
        suite.error_output = result.stderr[:2000] if result.stderr else ""
        for line in result.stdout.split("\n"):
            parts = line.strip().split()
            for i, part in enumerate(parts):
                try:
                    num = int(part)
                    if i > 0:
                        prev = parts[i - 1].lower()
                        if "pass" in prev:
                            suite.passed = num
                        elif "fail" in prev:
                            suite.failed = num
                        elif "skip" in prev:
                            suite.skipped = num
                except ValueError:
                    pass
        suite.total = suite.passed + suite.failed + suite.skipped
        return suite if suite.total > 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _run_jest(repo_path: str) -> TestSuite | None:
    try:
        import json as _json
        # Install dependencies first
        subprocess.run(
            ["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund"],
            cwd=repo_path, capture_output=True, text=True, timeout=120,
        )
        result = subprocess.run(
            ["npx", "jest", "--passWithNoTests", "--json", "--silent"],
            cwd=repo_path, capture_output=True, text=True, timeout=120,
        )
        suite = TestSuite(name="jest", framework="jest")
        try:
            data = _json.loads(result.stdout)
            suite.total = data.get("numTotalTests", 0)
            suite.passed = data.get("numPassedTests", 0)
            suite.failed = data.get("numFailedTests", 0)
            suite.skipped = data.get("numPendingTests", 0)
        except (_json.JSONDecodeError, KeyError):
            suite.error_output = result.stderr[:2000]
        return suite if suite.total > 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _run_go_test(repo_path: str) -> TestSuite | None:
    try:
        result = subprocess.run(
            ["go", "test", "-v", "-count=1", "./..."],
            cwd=repo_path, capture_output=True, text=True, timeout=120,
        )
        suite = TestSuite(name="go test", framework="go test")
        for line in result.stdout.split("\n"):
            if "--- PASS:" in line:
                suite.passed += 1
            elif "--- FAIL:" in line:
                suite.failed += 1
        suite.total = suite.passed + suite.failed
        if suite.total == 0:
            suite.error_output = result.stderr[:2000]
        return suite if suite.total > 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _run_flake8(repo_path: str) -> LintResult | None:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "flake8", ".", "--count", "--statistics", "--max-line-length=120"],
            cwd=repo_path, capture_output=True, text=True, timeout=60,
        )
        lint = LintResult(tool="flake8")
        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        # Count actual issue lines (contain filename:line:col pattern)
        issue_lines = [l for l in lines if ":" in l and not l[0].isdigit()]
        lint.total_issues = len(issue_lines)
        lint.errors = len([l for l in issue_lines if ": E" in l or ": F" in l])
        lint.warnings = len([l for l in issue_lines if ": W" in l or ": C" in l])
        lint.issues = issue_lines[:20]
        return lint if lint.total_issues > 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _run_eslint(repo_path: str) -> LintResult | None:
    try:
        # Install dependencies first
        subprocess.run(
            ["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund"],
            cwd=repo_path, capture_output=True, text=True, timeout=120,
        )
        result = subprocess.run(
            ["npx", "eslint", ".", "--format=compact"],
            cwd=repo_path, capture_output=True, text=True, timeout=60,
        )
        lint = LintResult(tool="eslint")
        lines = result.stdout.strip().split("\n")
        lint.total_issues = len([l for l in lines if "Error" in l or "Warning" in l])
        lint.errors = len([l for l in lines if "Error" in l])
        lint.warnings = len([l for l in lines if "Warning" in l])
        lint.issues = [l for l in lines if l.strip()][:20]
        return lint if lint.total_issues > 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def _run_pip_audit(repo_path: str) -> SecurityScan:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--format=json"],
            cwd=repo_path, capture_output=True, text=True, timeout=120,
        )
        import json as _json
        scan = SecurityScan(tool="pip-audit")
        try:
            data = _json.loads(result.stdout)
            vulns = data if isinstance(data, list) else data.get("dependencies", data.get("vulnerabilities", []))
            if isinstance(vulns, dict):
                vulns = list(vulns.values())
            for vuln in vulns:
                if not isinstance(vuln, dict):
                    continue
                severity = str(vuln.get("severity", "unknown")).lower()
                name = vuln.get("name", vuln.get("package", "unknown")) if isinstance(vuln.get("name"), str) else "unknown"
                scan.issues.append(SecurityIssue(
                    package=name, severity=severity,
                    description=str(vuln.get("description", "")),
                    fix_version=vuln.get("fix_versions", [""])[0] if vuln.get("fix_versions") else "",
                ))
                if severity == "critical": scan.critical += 1
                elif severity == "high": scan.high += 1
                elif severity == "medium": scan.medium += 1
                else: scan.low += 1
            scan.total_vulnerabilities = len(scan.issues)
        except (_json.JSONDecodeError, KeyError, AttributeError, TypeError) as exc:
            scan.error_output = f"{exc}: {result.stderr[:1500]}"
        return scan
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return SecurityScan(tool="pip-audit", error_output="pip-audit not available")


def _run_npm_audit(repo_path: str) -> SecurityScan:
    try:
        # Install dependencies first
        subprocess.run(
            ["npm", "install", "--ignore-scripts", "--no-audit", "--no-fund"],
            cwd=repo_path, capture_output=True, text=True, timeout=120,
        )
        result = subprocess.run(
            ["npm", "audit", "--json"],
            cwd=repo_path, capture_output=True, text=True, timeout=60,
        )
        import json as _json
        scan = SecurityScan(tool="npm audit")
        try:
            data = _json.loads(result.stdout)
            vulns = data.get("vulnerabilities", {})
            if isinstance(vulns, dict):
                for name, info in vulns.items():
                    if not isinstance(info, dict):
                        continue
                    severity = str(info.get("severity", "unknown")).lower()
                    scan.issues.append(SecurityIssue(package=str(name), severity=severity, description=""))
                    if severity == "critical": scan.critical += 1
                    elif severity == "high": scan.high += 1
                    elif severity == "medium": scan.medium += 1
                    else: scan.low += 1
            scan.total_vulnerabilities = len(scan.issues)
        except (_json.JSONDecodeError, KeyError, AttributeError, TypeError) as exc:
            scan.error_output = f"{exc}: {result.stderr[:1500]}"
        return scan
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return SecurityScan(tool="npm audit", error_output="npm audit not available")


def _file_contains(filepath: Path, term: str) -> bool:
    try:
        return term in filepath.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
