import asyncio
from dataclasses import dataclass

from tdp.modules.scanner.domain.errors import ScanInProgressError, ScanNotFoundError
from tdp.modules.scanner.domain.model import ScanId, ScanResult, ScanStatus
from tdp.modules.scanner.infrastructure.document_generator import suggest_documents
from tdp.modules.scanner.infrastructure.file_analyzer import analyze_files
from tdp.modules.scanner.infrastructure.git_operations import cleanup_temp_dir, clone_repository
from tdp.modules.scanner.infrastructure.health_calculator import calculate_health
from tdp.modules.scanner.infrastructure.sqlite_repository import SqliteScanRepository
from tdp.modules.scanner.infrastructure.tech_stack_detector import detect_tech_stack
from tdp.modules.scanner.infrastructure.test_runner import run_lint, run_security_scan, run_tests


@dataclass(frozen=True, slots=True)
class ScanDto:
    id: str
    repository_url: str
    repository_name: str
    branch: str
    status: str
    stage: str
    file_analysis: dict
    tech_stack: dict
    test_suites: list[dict]
    lint_results: list[dict]
    security_scan: dict
    health: dict
    suggestions: list[dict]
    error_message: str
    started_at: str
    completed_at: str | None

    @classmethod
    def from_domain(cls, scan: ScanResult) -> "ScanDto":
        return cls(
            id=str(scan.id),
            repository_url=scan.repository_url,
            repository_name=scan.repository_name,
            branch=scan.branch,
            status=scan.status.value,
            stage=scan.stage.value,
            file_analysis={
                "total_files": scan.file_analysis.total_files,
                "total_lines": scan.file_analysis.total_lines,
                "languages": scan.file_analysis.languages,
                "directories": scan.file_analysis.directories,
                "has_readme": scan.file_analysis.has_readme,
                "has_license": scan.file_analysis.has_license,
                "has_changelog": scan.file_analysis.has_changelog,
                "has_dockerfile": scan.file_analysis.has_dockerfile,
                "has_docker_compose": scan.file_analysis.has_docker_compose,
                "config_files": scan.file_analysis.config_files,
            },
            tech_stack={
                "languages": scan.tech_stack.languages,
                "frameworks": scan.tech_stack.frameworks,
                "databases": scan.tech_stack.databases,
                "tools": scan.tech_stack.tools,
                "package_manager": scan.tech_stack.package_manager,
                "has_docker": scan.tech_stack.has_docker,
                "has_ci_cd": scan.tech_stack.has_ci_cd,
                "has_tests": scan.tech_stack.has_tests,
                "has_linting": scan.tech_stack.has_linting,
                "has_type_checking": scan.tech_stack.has_type_checking,
            },
            test_suites=[{
                "name": s.name, "framework": s.framework, "total": s.total,
                "passed": s.passed, "failed": s.failed, "skipped": s.skipped,
                "error_output": s.error_output,
            } for s in scan.test_suites],
            lint_results=[{
                "tool": r.tool, "total_issues": r.total_issues,
                "errors": r.errors, "warnings": r.warnings,
            } for r in scan.lint_results],
            security_scan={
                "tool": scan.security_scan.tool,
                "total_vulnerabilities": scan.security_scan.total_vulnerabilities,
                "critical": scan.security_scan.critical,
                "high": scan.security_scan.high,
                "medium": scan.security_scan.medium,
                "low": scan.security_scan.low,
                "issues": [{"package": i.package, "severity": i.severity, "description": i.description, "fix_version": i.fix_version} for i in scan.security_scan.issues],
            },
            health={
                "overall": scan.health.overall.value,
                "test_coverage": scan.health.test_coverage.value,
                "code_quality": scan.health.code_quality.value,
                "security": scan.health.security.value,
                "documentation": scan.health.documentation.value,
                "score": scan.health.score,
                "issues": scan.health.issues,
            },
            suggestions=[{
                "template_key": s.template_key, "document_type": s.document_type,
                "name": s.name, "reason": s.reason, "priority": s.priority,
                "auto_generated": s.auto_generated,
            } for s in scan.suggestions],
            error_message=scan.error_message,
            started_at=scan.started_at.isoformat(),
            completed_at=scan.completed_at.isoformat() if scan.completed_at else None,
        )


class ScannerApplicationService:
    def __init__(self, repository: SqliteScanRepository) -> None:
        self._repository = repository

    async def get_scan(self, scan_id: str) -> ScanDto:
        scan = await self._repository.get(ScanId.from_string(scan_id))
        if scan is None:
            raise ScanNotFoundError(f"Scan {scan_id} not found.")
        return ScanDto.from_domain(scan)

    async def list_scans(self) -> list[ScanDto]:
        scans = await self._repository.list_all()
        return [ScanDto.from_domain(s) for s in scans]

    async def delete_scan(self, scan_id: str) -> None:
        scan = await self._repository.get(ScanId.from_string(scan_id))
        if scan is None:
            raise ScanNotFoundError(f"Scan {scan_id} not found.")
        if scan.status in (ScanStatus.CLONING, ScanStatus.ANALYZING, ScanStatus.TESTING):
            raise ScanInProgressError("Cannot delete a scan that is in progress.")
        await self._repository.delete(scan.id)

    async def start_scan(self, repository_url: str, branch: str = "main") -> ScanDto:
        scan = ScanResult.create(repository_url, branch)
        await self._repository.save(scan)
        asyncio.create_task(self._execute_scan(scan.id))
        return ScanDto.from_domain(scan)

    async def rescan(self, scan_id: str) -> ScanDto:
        existing = await self._repository.get(ScanId.from_string(scan_id))
        if existing is None:
            raise ScanNotFoundError(f"Scan {scan_id} not found.")
        if existing.status in (ScanStatus.CLONING, ScanStatus.ANALYZING, ScanStatus.TESTING, ScanStatus.GENERATING):
            raise ScanInProgressError("Cannot re-scan while scan is in progress.")
        # Create a fresh scan for the same repo
        new_scan = ScanResult.create(existing.repository_url, existing.branch)
        await self._repository.save(new_scan)
        asyncio.create_task(self._execute_scan(new_scan.id))
        return ScanDto.from_domain(new_scan)

    async def _execute_scan(self, scan_id: ScanId) -> None:
        scan = await self._repository.get(scan_id)
        if scan is None:
            return
        temp_path = None
        try:
            scan.status = ScanStatus.CLONING
            await self._repository.save(scan)
            temp_path = clone_repository(scan.repository_url, scan.branch)

            scan.status = ScanStatus.ANALYZING
            await self._repository.save(scan)
            scan.file_analysis = analyze_files(temp_path)
            scan.tech_stack = detect_tech_stack(scan.file_analysis, temp_path)

            scan.status = ScanStatus.TESTING
            await self._repository.save(scan)
            scan.test_suites = run_tests(temp_path)
            scan.lint_results = run_lint(temp_path)
            scan.security_scan = run_security_scan(temp_path)

            scan.status = ScanStatus.GENERATING
            await self._repository.save(scan)
            scan.health = calculate_health(scan.tech_stack, scan.file_analysis, scan.test_suites, scan.lint_results, scan.security_scan)
            scan.suggestions = suggest_documents(scan.tech_stack, scan.file_analysis, scan.stage)

            scan.mark_completed()
            await self._repository.save(scan)
        except Exception as exc:
            scan.mark_failed(str(exc))
            await self._repository.save(scan)
        finally:
            if temp_path:
                cleanup_temp_dir(temp_path)
