from datetime import datetime, timedelta, UTC

from tdp.modules.scanner.domain.model import (
    FileAnalysis,
    HealthLevel,
    ProjectHealth,
    ScanResult,
    ScanStatus,
    SecurityIssue,
    SecurityScan,
    TechStack,
    TestSuite,
)
from tdp.modules.scanner.infrastructure.scan_comparator import compare_scans


def _make_scan(
    score: int = 50,
    files: int = 100,
    lines: int = 5000,
    issues: list[str] | None = None,
    frameworks: list[str] | None = None,
    test_total: int = 0,
    test_passed: int = 0,
    vuln_total: int = 0,
    vuln_critical: int = 0,
    started_at: datetime | None = None,
) -> ScanResult:
    scan = ScanResult.create("https://github.com/org/repo.git")
    scan.status = ScanStatus.COMPLETED
    scan.health = ProjectHealth(
        overall=HealthLevel.GOOD,
        score=score,
        issues=issues or [],
    )
    scan.file_analysis = FileAnalysis(total_files=files, total_lines=lines)
    scan.tech_stack = TechStack(frameworks=frameworks or [])
    scan.test_suites = [
        TestSuite(name="unit", framework="pytest", total=test_total, passed=test_passed)
    ]
    scan.security_scan = SecurityScan(
        tool="safety",
        total_vulnerabilities=vuln_total,
        critical=vuln_critical,
    )
    if started_at:
        scan.started_at = started_at
    return scan


class TestCompareScansIdentical:
    def test_identical_scans_detected(self) -> None:
        before = _make_scan()
        after = _make_scan()
        result = compare_scans(before, after)
        assert result.is_identical is True

    def test_identical_has_zero_deltas(self) -> None:
        before = _make_scan()
        after = _make_scan()
        result = compare_scans(before, after)
        assert result.health_score_delta == 0
        assert result.files_delta == 0
        assert result.lines_delta == 0


class TestCompareScansHealthDelta:
    def test_score_improvement(self) -> None:
        before = _make_scan(score=40)
        after = _make_scan(score=80)
        result = compare_scans(before, after)
        assert result.health_score_delta == 40
        assert result.health_score_before == 40
        assert result.health_score_after == 80

    def test_score_regression(self) -> None:
        before = _make_scan(score=80)
        after = _make_scan(score=50)
        result = compare_scans(before, after)
        assert result.health_score_delta == -30


class TestCompareScansFileDelta:
    def test_files_increased(self) -> None:
        before = _make_scan(files=100)
        after = _make_scan(files=150)
        result = compare_scans(before, after)
        assert result.files_delta == 50

    def test_lines_decreased(self) -> None:
        before = _make_scan(lines=10000)
        after = _make_scan(lines=8000)
        result = compare_scans(before, after)
        assert result.lines_delta == -2000


class TestCompareScansIssues:
    def test_issues_added(self) -> None:
        before = _make_scan(issues=["old issue"])
        after = _make_scan(issues=["old issue", "new issue"])
        result = compare_scans(before, after)
        assert "new issue" in result.issues_added
        assert result.issues_removed == []

    def test_issues_removed(self) -> None:
        before = _make_scan(issues=["fixed issue", "remaining"])
        after = _make_scan(issues=["remaining"])
        result = compare_scans(before, after)
        assert "fixed issue" in result.issues_removed
        assert result.issues_added == []

    def test_issues_mixed(self) -> None:
        before = _make_scan(issues=["removed"])
        after = _make_scan(issues=["added"])
        result = compare_scans(before, after)
        assert "added" in result.issues_added
        assert "removed" in result.issues_removed


class TestCompareScansFrameworks:
    def test_frameworks_added(self) -> None:
        before = _make_scan(frameworks=["React"])
        after = _make_scan(frameworks=["React", "Next.js"])
        result = compare_scans(before, after)
        assert "Next.js" in result.frameworks_added

    def test_frameworks_removed(self) -> None:
        before = _make_scan(frameworks=["React", "Redux"])
        after = _make_scan(frameworks=["React"])
        result = compare_scans(before, after)
        assert "Redux" in result.frameworks_removed


class TestCompareScansTests:
    def test_test_count_increased(self) -> None:
        before = _make_scan(test_total=10, test_passed=8)
        after = _make_scan(test_total=20, test_passed=18)
        result = compare_scans(before, after)
        assert result.test_total_after == 20
        assert result.test_passed_after == 18


class TestCompareScansSecurity:
    def test_vulnerabilities_decreased(self) -> None:
        before = _make_scan(vuln_total=10, vuln_critical=3)
        after = _make_scan(vuln_total=5, vuln_critical=1)
        result = compare_scans(before, after)
        assert result.security_total_before == 10
        assert result.security_total_after == 5
        assert result.security_critical_before == 3
        assert result.security_critical_after == 1


class TestCompareScansMetrics:
    def test_metrics_contain_all_dimensions(self) -> None:
        before = _make_scan()
        after = _make_scan()
        result = compare_scans(before, after)
        labels = [m.label for m in result.metrics]
        assert "Health Score" in labels
        assert "Total Files" in labels
        assert "Total Lines" in labels
        assert "Test Cases" in labels
        assert "Vulnerabilities" in labels

    def test_metric_direction_up_for_improvement(self) -> None:
        before = _make_scan(score=40)
        after = _make_scan(score=80)
        result = compare_scans(before, after)
        health_metric = next(m for m in result.metrics if m.label == "Health Score")
        assert health_metric.direction == "up"
        assert health_metric.value_change == 40

    def test_metric_direction_down_for_regression(self) -> None:
        before = _make_scan(vuln_total=2)
        after = _make_scan(vuln_total=8)
        result = compare_scans(before, after)
        vuln_metric = next(m for m in result.metrics if m.label == "Vulnerabilities")
        assert vuln_metric.direction == "down"


class TestCompareScansTimeBetween:
    def test_time_between_minutes(self) -> None:
        now = datetime.now(UTC)
        before = _make_scan(started_at=now)
        after = _make_scan(started_at=now + timedelta(minutes=30))
        result = compare_scans(before, after)
        assert "minutes" in result.time_between

    def test_time_between_hours(self) -> None:
        now = datetime.now(UTC)
        before = _make_scan(started_at=now)
        after = _make_scan(started_at=now + timedelta(hours=3))
        result = compare_scans(before, after)
        assert "hours" in result.time_between

    def test_time_between_days(self) -> None:
        now = datetime.now(UTC)
        before = _make_scan(started_at=now)
        after = _make_scan(started_at=now + timedelta(days=5))
        result = compare_scans(before, after)
        assert "days" in result.time_between
