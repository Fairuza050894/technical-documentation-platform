from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Annotated

router = APIRouter(tags=["scanner-dashboard"])


async def get_scanner_service(request: Request):
    return request.app.state.scanner_service


async def get_webhook_service(request: Request):
    return request.app.state.webhook_service


ScannerServiceDependency = Annotated[object, Depends(get_scanner_service)]
WebhookServiceDependency = Annotated[object, Depends(get_webhook_service)]


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


@router.get("/scanner/dashboard", response_model=DashboardResponse)
async def get_dashboard(service: ScannerServiceDependency) -> DashboardResponse:
    scans = await service.list_scans()

    # Group by repository URL
    repo_map: dict[str, list] = {}
    for scan in scans:
        url = scan.repository_url
        if url not in repo_map:
            repo_map[url] = []
        repo_map[url].append(scan)

    repos = []
    all_scores = []
    alerts = []

    for url, repo_scans in repo_map.items():
        # Sort by date descending
        repo_scans.sort(key=lambda s: s.started_at, reverse=True)
        latest = repo_scans[0]
        all_scores.append(latest.health.score)

        # Score trend (last 10 scans)
        trend = []
        for s in repo_scans[:10]:
            trend.append({
                "scan_id": s.id,
                "score": s.health.score,
                "sonarqube_score": s.sonarqube.get("total_score", 0) if isinstance(s.sonarqube, dict) else 0,
                "date": s.started_at,
            })
        trend.reverse()  # chronological order

        # Count scans
        completed_scans = [s for s in repo_scans if s.status == "COMPLETED"]

        # Alerts
        if latest.status == "COMPLETED":
            # Score drop alert
            if len(completed_scans) >= 2:
                prev = completed_scans[1]
                delta = latest.health.score - prev.health.score
                if delta < -5:
                    alerts.append({
                        "type": "score_drop",
                        "severity": "critical" if delta < -20 else "warning",
                        "repository_name": latest.repository_name,
                        "message": f"Score dropped {abs(delta)} points ({prev.health.score} → {latest.health.score})",
                        "scan_id": latest.id,
                    })

            # Security alert
            if latest.security_scan.get("critical", 0) if isinstance(latest.security_scan, dict) else latest.security_scan.critical > 0:
                alerts.append({
                    "type": "security",
                    "severity": "critical",
                    "repository_name": latest.repository_name,
                    "message": f"{latest.security_scan.get('critical', 0) if isinstance(latest.security_scan, dict) else latest.security_scan.critical} critical vulnerabilities",
                    "scan_id": latest.id,
                })

            # Failed tests alert
            test_total = sum(t.get("total", 0) if isinstance(t, dict) else t.total for t in latest.test_suites)
            test_failed = sum(t.get("failed", 0) if isinstance(t, dict) else t.failed for t in latest.test_suites)
            if test_total > 0 and test_failed / test_total > 0.2:
                alerts.append({
                    "type": "test_failure",
                    "severity": "warning",
                    "repository_name": latest.repository_name,
                    "message": f"Test failure rate: {test_failed}/{test_total} ({test_failed/test_total:.0%})",
                    "scan_id": latest.id,
                })

        # Build summary
        sq_score = None
        if isinstance(latest.sonarqube, dict):
            sq = latest.sonarqube
            if sq.get("total_score", 0) > 0:
                sq_score = sq["total_score"]

        test_suites_count = len(latest.test_suites)
        total_tests = sum(t.get("total", 0) if isinstance(t, dict) else t.total for t in latest.test_suites)
        tests_passed = sum(t.get("passed", 0) if isinstance(t, dict) else t.passed for t in latest.test_suites)
        lint_total = sum(r.get("total_issues", 0) if isinstance(r, dict) else r.total_issues for r in latest.lint_results)
        vuln_total = latest.security_scan.get("total_vulnerabilities", 0) if isinstance(latest.security_scan, dict) else latest.security_scan.total_vulnerabilities

        repos.append(RepoSummary(
            repository_name=latest.repository_name,
            repository_url=url,
            latest_scan_id=latest.id,
            branch=latest.branch,
            status=latest.status,
            health_score=latest.health.score,
            sonarqube_score=sq_score,
            total_files=latest.file_analysis.get("total_files", 0) if isinstance(latest.file_analysis, dict) else latest.file_analysis.total_files,
            total_lines=latest.file_analysis.get("total_lines", 0) if isinstance(latest.file_analysis, dict) else latest.file_analysis.total_lines,
            frameworks=latest.tech_stack.get("frameworks", []) if isinstance(latest.tech_stack, dict) else latest.tech_stack.frameworks,
            test_suites=test_suites_count,
            total_tests=total_tests,
            tests_passed=tests_passed,
            lint_issues=lint_total,
            vulnerabilities=vuln_total,
            last_scan_at=latest.started_at,
            scan_count=len(repo_scans),
            score_trend=trend,
        ))

    # Sort by health score ascending (worst first)
    repos.sort(key=lambda r: r.health_score)

    # Sort alerts by severity
    severity_order = {"critical": 0, "warning": 1, "info": 2}
    alerts.sort(key=lambda a: severity_order.get(a.get("severity", "info"), 2))

    avg_score = sum(all_scores) / len(all_scores) if all_scores else 0

    return DashboardResponse(
        repos=repos,
        total_repos=len(repos),
        total_scans=len(scans),
        avg_health_score=int(avg_score),
        alerts=alerts,
    )
