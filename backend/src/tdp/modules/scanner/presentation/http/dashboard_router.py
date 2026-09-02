from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Annotated

router = APIRouter(tags=["scanner-dashboard"])


async def get_scanner_service(request: Request):
    return request.app.state.scanner_service


ScannerServiceDependency = Annotated[object, Depends(get_scanner_service)]


class RepoSummary(BaseModel):
    repository_name: str
    repository_url: str
    latest_scan_id: str
    branch: str
    status: str
    health_score: int
    sonarqube_score: int | None
    total_files: int
    total_lines: int
    frameworks: list[str]
    test_suites: int
    total_tests: int
    tests_passed: int
    lint_issues: int
    vulnerabilities: int
    last_scan_at: str
    scan_count: int
    score_trend: list[dict]


class DashboardResponse(BaseModel):
    repos: list[RepoSummary]
    total_repos: int
    total_scans: int
    avg_health_score: int
    alerts: list[dict]


def _get(d, key, default=None):
    """Safe get from dict or object."""
    if isinstance(d, dict):
        return d.get(key, default)
    return getattr(d, key, default)


@router.get("/scanner/dashboard", response_model=DashboardResponse)
async def get_dashboard(service: ScannerServiceDependency) -> DashboardResponse:
    scans = await service.list_scans()

    repo_map: dict[str, list] = {}
    for scan in scans:
        url = _get(scan, "repository_url", "")
        if url not in repo_map:
            repo_map[url] = []
        repo_map[url].append(scan)

    repos = []
    all_scores = []
    alerts = []

    for url, repo_scans in repo_map.items():
        repo_scans.sort(key=lambda s: _get(s, "started_at", ""), reverse=True)
        latest = repo_scans[0]
        health = _get(latest, "health", {})
        health_score = _get(health, "score", 0)
        all_scores.append(health_score)

        completed_scans = [s for s in repo_scans if _get(s, "status") == "COMPLETED"]

        # Score trend
        trend = []
        for s in repo_scans[:10]:
            sh = _get(s, "health", {})
            sq = _get(s, "sonarqube", {})
            trend.append({
                "scan_id": _get(s, "id", ""),
                "score": _get(sh, "score", 0),
                "sonarqube_score": _get(sq, "total_score", 0),
                "date": _get(s, "started_at", ""),
            })
        trend.reverse()

        # Alerts
        if _get(latest, "status") == "COMPLETED":
            if len(completed_scans) >= 2:
                prev = completed_scans[1]
                prev_health = _get(prev, "health", {})
                delta = health_score - _get(prev_health, "score", 0)
                if delta < -5:
                    alerts.append({
                        "type": "score_drop",
                        "severity": "critical" if delta < -20 else "warning",
                        "repository_name": _get(latest, "repository_name", ""),
                        "message": f"Score dropped {abs(delta)} points ({_get(prev_health, 'score', 0)} -> {health_score})",
                        "scan_id": _get(latest, "id", ""),
                    })

            sec = _get(latest, "security_scan", {})
            critical_vulns = _get(sec, "critical", 0)
            if critical_vulns and critical_vulns > 0:
                alerts.append({
                    "type": "security",
                    "severity": "critical",
                    "repository_name": _get(latest, "repository_name", ""),
                    "message": f"{critical_vulns} critical vulnerabilities",
                    "scan_id": _get(latest, "id", ""),
                })

            test_suites = _get(latest, "test_suites", [])
            total_tests = sum(_get(t, "total", 0) for t in test_suites)
            failed_tests = sum(_get(t, "failed", 0) for t in test_suites)
            if total_tests > 0 and failed_tests / total_tests > 0.2:
                alerts.append({
                    "type": "test_failure",
                    "severity": "warning",
                    "repository_name": _get(latest, "repository_name", ""),
                    "message": f"Test failure rate: {failed_tests}/{total_tests} ({failed_tests/total_tests:.0%})",
                    "scan_id": _get(latest, "id", ""),
                })

        # SonarQube score
        sq_data = _get(latest, "sonarqube", {})
        sq_score = _get(sq_data, "total_score", 0)
        sq_score_out = sq_score if sq_score and sq_score > 0 else None

        # Metrics
        fa = _get(latest, "file_analysis", {})
        ts = _get(latest, "tech_stack", {})
        sec = _get(latest, "security_scan", {})
        test_suites = _get(latest, "test_suites", [])
        lint_results = _get(latest, "lint_results", [])

        total_tests = sum(_get(t, "total", 0) for t in test_suites)
        tests_passed = sum(_get(t, "passed", 0) for t in test_suites)
        lint_total = sum(_get(r, "total_issues", 0) for r in lint_results)
        vuln_total = _get(sec, "total_vulnerabilities", 0)

        repos.append(RepoSummary(
            repository_name=_get(latest, "repository_name", ""),
            repository_url=url,
            latest_scan_id=_get(latest, "id", ""),
            branch=_get(latest, "branch", ""),
            status=_get(latest, "status", ""),
            health_score=health_score,
            sonarqube_score=sq_score_out,
            total_files=_get(fa, "total_files", 0),
            total_lines=_get(fa, "total_lines", 0),
            frameworks=_get(ts, "frameworks", []),
            test_suites=len(test_suites),
            total_tests=total_tests,
            tests_passed=tests_passed,
            lint_issues=lint_total,
            vulnerabilities=vuln_total,
            last_scan_at=_get(latest, "started_at", ""),
            scan_count=len(repo_scans),
            score_trend=trend,
        ))

    repos.sort(key=lambda r: r.health_score)

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: severity_order.get(a.get("severity", "info"), 2))

    avg_score = int(sum(all_scores) / len(all_scores)) if all_scores else 0

    return DashboardResponse(
        repos=repos,
        total_repos=len(repos),
        total_scans=len(scans),
        avg_health_score=avg_score,
        alerts=alerts,
    )
