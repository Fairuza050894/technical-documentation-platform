import json
import sqlite3
from datetime import datetime

from tdp.modules.scanner.domain.model import (
    DocumentSuggestion, FileAnalysis, HealthLevel, LintResult,
    ProjectHealth, ProjectStage, ScanId, ScanResult, ScanStatus,
    SecurityIssue, SecurityScan, TechStack, TestCase, TestSuite,
)
from tdp.modules.scanner.domain.repository import ScanRepository


class SqliteScanRepository(ScanRepository):
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path
        self._ensure_schema()

    def _connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _ensure_schema(self) -> None:
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_results (
                    id TEXT PRIMARY KEY,
                    repository_url TEXT NOT NULL,
                    repository_name TEXT NOT NULL,
                    branch TEXT NOT NULL DEFAULT 'main',
                    status TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    file_analysis_json TEXT NOT NULL DEFAULT '{}',
                    tech_stack_json TEXT NOT NULL DEFAULT '{}',
                    test_suites_json TEXT NOT NULL DEFAULT '[]',
                    lint_results_json TEXT NOT NULL DEFAULT '[]',
                    security_scan_json TEXT NOT NULL DEFAULT '{}',
                    health_json TEXT NOT NULL DEFAULT '{}',
                    suggestions_json TEXT NOT NULL DEFAULT '[]',
                    error_message TEXT NOT NULL DEFAULT '',
                    started_at TEXT NOT NULL,
                    completed_at TEXT
                )
                """
            )

    async def get(self, scan_id: ScanId) -> ScanResult | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM scan_results WHERE id = ?", (str(scan_id),)
            ).fetchone()
            return _row_to_scan(row) if row else None

    async def list_all(self) -> list[ScanResult]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM scan_results ORDER BY started_at DESC"
            ).fetchall()
            return [_row_to_scan(row) for row in rows]

    async def save(self, scan: ScanResult) -> None:
        with self._connection() as connection:
            existing = connection.execute(
                "SELECT id FROM scan_results WHERE id = ?", (str(scan.id),)
            ).fetchone()

            fa = json.dumps({"total_files": scan.file_analysis.total_files, "total_lines": scan.file_analysis.total_lines, "languages": scan.file_analysis.languages, "directories": scan.file_analysis.directories, "has_readme": scan.file_analysis.has_readme, "has_license": scan.file_analysis.has_license, "has_changelog": scan.file_analysis.has_changelog, "has_dockerfile": scan.file_analysis.has_dockerfile, "has_docker_compose": scan.file_analysis.has_docker_compose, "config_files": scan.file_analysis.config_files})
            ts = json.dumps({"languages": scan.tech_stack.languages, "frameworks": scan.tech_stack.frameworks, "databases": scan.tech_stack.databases, "tools": scan.tech_stack.tools, "package_manager": scan.tech_stack.package_manager, "has_docker": scan.tech_stack.has_docker, "has_ci_cd": scan.tech_stack.has_ci_cd, "has_tests": scan.tech_stack.has_tests, "has_linting": scan.tech_stack.has_linting, "has_type_checking": scan.tech_stack.has_type_checking})
            tst = json.dumps([{"name": s.name, "framework": s.framework, "total": s.total, "passed": s.passed, "failed": s.failed, "skipped": s.skipped, "error_output": s.error_output} for s in scan.test_suites])
            lt = json.dumps([{"tool": r.tool, "total_issues": r.total_issues, "errors": r.errors, "warnings": r.warnings, "issues": r.issues} for r in scan.lint_results])
            sc = json.dumps({"tool": scan.security_scan.tool, "total_vulnerabilities": scan.security_scan.total_vulnerabilities, "critical": scan.security_scan.critical, "high": scan.security_scan.high, "medium": scan.security_scan.medium, "low": scan.security_scan.low, "issues": [{"package": i.package, "severity": i.severity, "description": i.description, "fix_version": i.fix_version} for i in scan.security_scan.issues]})
            hl = json.dumps({"overall": scan.health.overall.value, "test_coverage": scan.health.test_coverage.value, "code_quality": scan.health.code_quality.value, "security": scan.health.security.value, "documentation": scan.health.documentation.value, "score": scan.health.score, "issues": scan.health.issues})
            sg = json.dumps([{"template_key": s.template_key, "document_type": s.document_type, "name": s.name, "reason": s.reason, "priority": s.priority, "auto_generated": s.auto_generated, "content": s.content} for s in scan.suggestions])

            if existing:
                connection.execute(
                    "UPDATE scan_results SET status=?, stage=?, file_analysis_json=?, tech_stack_json=?, test_suites_json=?, lint_results_json=?, security_scan_json=?, health_json=?, suggestions_json=?, error_message=?, completed_at=? WHERE id=?",
                    (scan.status.value, scan.stage.value, fa, ts, tst, lt, sc, hl, sg, scan.error_message, scan.completed_at.isoformat() if scan.completed_at else None, str(scan.id))
                )
            else:
                connection.execute(
                    "INSERT INTO scan_results (id, repository_url, repository_name, branch, status, stage, file_analysis_json, tech_stack_json, test_suites_json, lint_results_json, security_scan_json, health_json, suggestions_json, error_message, started_at, completed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (str(scan.id), scan.repository_url, scan.repository_name, scan.branch, scan.status.value, scan.stage.value, fa, ts, tst, lt, sc, hl, sg, scan.error_message, scan.started_at.isoformat(), scan.completed_at.isoformat() if scan.completed_at else None)
                )

    async def delete(self, scan_id: ScanId) -> None:
        with self._connection() as connection:
            connection.execute("DELETE FROM scan_results WHERE id = ?", (str(scan_id),))


def _row_to_scan(row: sqlite3.Row) -> ScanResult:
    fa_d = json.loads(row["file_analysis_json"])
    ts_d = json.loads(row["tech_stack_json"])
    tst_d = json.loads(row["test_suites_json"])
    lt_d = json.loads(row["lint_results_json"])
    sc_d = json.loads(row["security_scan_json"])
    hl_d = json.loads(row["health_json"])
    sg_d = json.loads(row["suggestions_json"])

    return ScanResult(
        id=ScanId.from_string(row["id"]),
        repository_url=row["repository_url"],
        repository_name=row["repository_name"],
        branch=row["branch"],
        status=ScanStatus(row["status"]),
        stage=ProjectStage(row["stage"]),
        file_analysis=FileAnalysis(**fa_d),
        tech_stack=TechStack(**ts_d),
        test_suites=[TestSuite(**s) for s in tst_d],
        lint_results=[LintResult(**r) for r in lt_d],
        security_scan=SecurityScan(
            tool=sc_d["tool"], total_vulnerabilities=sc_d["total_vulnerabilities"],
            critical=sc_d["critical"], high=sc_d["high"], medium=sc_d["medium"], low=sc_d["low"],
            issues=[SecurityIssue(**i) for i in sc_d.get("issues", [])],
            error_output=sc_d.get("error_output", ""),
        ),
        health=ProjectHealth(
            overall=HealthLevel(hl_d["overall"]), test_coverage=HealthLevel(hl_d["test_coverage"]),
            code_quality=HealthLevel(hl_d["code_quality"]), security=HealthLevel(hl_d["security"]),
            documentation=HealthLevel(hl_d["documentation"]), score=hl_d["score"], issues=hl_d["issues"],
        ),
        suggestions=[DocumentSuggestion(**s) for s in sg_d],
        error_message=row["error_message"],
        started_at=datetime.fromisoformat(row["started_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
    )
