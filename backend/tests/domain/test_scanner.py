from datetime import UTC

from tdp.modules.scanner.domain.model import (
    FileAnalysis,
    HealthLevel,
    ProjectHealth,
    ScanComparison,
    ScanId,
    ScanResult,
    ScanStatus,
    SecurityScan,
    TechStack,
    TestSuite,
)


class TestScanId:
    def test_new_generates_unique_ids(self) -> None:
        first = ScanId.new()
        second = ScanId.new()
        assert str(first) != str(second)

    def test_from_string_roundtrip(self) -> None:
        scan_id = ScanId.new()
        restored = ScanId.from_string(str(scan_id))
        assert str(scan_id) == str(restored)

    def test_from_string_rejects_invalid_uuid(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            ScanId.from_string("not-a-uuid")


class TestScanResultCreate:
    def test_create_extracts_repo_name_from_url(self) -> None:
        scan = ScanResult.create("https://github.com/org/my-repo.git", "main")
        assert scan.repository_name == "my-repo"

    def test_create_extracts_name_without_git_suffix(self) -> None:
        scan = ScanResult.create("https://github.com/org/service-api")
        assert scan.repository_name == "service-api"

    def test_create_strips_trailing_slash(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo/")
        assert scan.repository_name == "repo"

    def test_create_defaults_to_pending(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        assert scan.status == ScanStatus.PENDING

    def test_create_defaults_branch_to_main(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        assert scan.branch == "main"

    def test_create_accepts_custom_branch(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git", "develop")
        assert scan.branch == "develop"

    def test_create_initializes_empty_health(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        assert scan.health.score == 0
        assert scan.health.overall == HealthLevel.UNKNOWN
        assert scan.health.test_coverage == HealthLevel.UNKNOWN

    def test_create_initializes_empty_tech_stack(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        assert scan.tech_stack.languages == {}
        assert scan.tech_stack.frameworks == []
        assert scan.tech_stack.has_docker is False

    def test_create_initializes_empty_file_analysis(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        assert scan.file_analysis.total_files == 0
        assert scan.file_analysis.total_lines == 0

    def test_create_has_no_completed_at(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        assert scan.completed_at is None

    def test_create_generates_unique_ids(self) -> None:
        first = ScanResult.create("https://github.com/org/repo.git")
        second = ScanResult.create("https://github.com/org/repo.git")
        assert str(first.id) != str(second.id)


class TestScanResultLifecycle:
    def test_mark_completed_sets_status(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        scan.mark_completed()
        assert scan.status == ScanStatus.COMPLETED

    def test_mark_completed_sets_completed_at(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        assert scan.completed_at is None
        scan.mark_completed()
        assert scan.completed_at is not None

    def test_mark_failed_sets_status(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        scan.mark_failed("clone failed")
        assert scan.status == ScanStatus.FAILED

    def test_mark_failed_sets_error_message(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        scan.mark_failed("permission denied")
        assert scan.error_message == "permission denied"

    def test_mark_failed_sets_completed_at(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git")
        scan.mark_failed("timeout")
        assert scan.completed_at is not None


class TestProjectHealth:
    def test_default_health_is_unknown(self) -> None:
        health = ProjectHealth()
        assert health.overall == HealthLevel.UNKNOWN
        assert health.score == 0
        assert health.issues == []

    def test_health_with_issues(self) -> None:
        health = ProjectHealth(
            overall=HealthLevel.WARNING,
            score=50,
            issues=["No tests found", "No README"],
        )
        assert len(health.issues) == 2
        assert health.score == 50


class TestTechStack:
    def test_default_tech_stack(self) -> None:
        stack = TechStack()
        assert stack.languages == {}
        assert stack.frameworks == []
        assert stack.has_docker is False
        assert stack.has_ci_cd is False

    def test_tech_stack_with_data(self) -> None:
        stack = TechStack(
            languages={"Python": 70.0, "JavaScript": 30.0},
            frameworks=["FastAPI", "React"],
            has_docker=True,
        )
        assert stack.languages["Python"] == 70.0
        assert "FastAPI" in stack.frameworks
        assert stack.has_docker is True


class TestFileAnalysis:
    def test_default_file_analysis(self) -> None:
        analysis = FileAnalysis()
        assert analysis.total_files == 0
        assert analysis.has_readme is False
        assert analysis.config_files == []


class TestSecurityScan:
    def test_default_security_scan(self) -> None:
        scan = SecurityScan(tool="none")
        assert scan.total_vulnerabilities == 0
        assert scan.critical == 0
        assert scan.issues == []


class TestTestSuite:
    def test_default_test_suite(self) -> None:
        suite = TestSuite(name="unit", framework="pytest")
        assert suite.total == 0
        assert suite.passed == 0
        assert suite.failed == 0
