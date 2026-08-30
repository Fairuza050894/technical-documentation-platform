from datetime import datetime

from tdp.modules.scanner.domain.model import MetricDelta, ScanComparison, ScanResult


def compare_scans(before: ScanResult, after: ScanResult) -> ScanComparison:
    # Time between
    if before.started_at and after.started_at:
        diff = after.started_at - before.started_at
        hours = diff.total_seconds() / 3600
        if hours < 1:
            time_between = str(int(diff.total_seconds() / 60)) + " minutes"
        elif hours < 24:
            time_between = str(int(hours)) + " hours"
        else:
            time_between = str(int(hours / 24)) + " days"
    else:
        time_between = "N/A"

    # Issues diff
    issues_before = set(before.health.issues)
    issues_after = set(after.health.issues)
    issues_added = sorted(issues_after - issues_before)
    issues_removed = sorted(issues_before - issues_after)

    # Frameworks diff
    fw_before = set(before.tech_stack.frameworks)
    fw_after = set(after.tech_stack.frameworks)
    fw_added = sorted(fw_after - fw_before)
    fw_removed = sorted(fw_before - fw_after)

    # Test totals
    test_total_before = sum(s.total for s in before.test_suites)
    test_total_after = sum(s.total for s in after.test_suites)
    test_passed_before = sum(s.passed for s in before.test_suites)
    test_passed_after = sum(s.passed for s in after.test_suites)

    # Security totals
    sec_before = before.security_scan
    sec_after = after.security_scan

    # Health score delta
    h_before = before.health.score
    h_after = after.health.score
    h_delta = h_after - h_before

    # Files/lines delta
    f_before = before.file_analysis.total_files
    f_after = after.file_analysis.total_files
    l_before = before.file_analysis.total_lines
    l_after = after.file_analysis.total_lines

    # Build metrics list
    metrics = []

    def add_metric(label, val_before, val_after, higher_is_better=True):
        delta = val_after - val_before
        if delta > 0:
            direction = "up" if higher_is_better else "down"
        elif delta < 0:
            direction = "down" if higher_is_better else "up"
        else:
            direction = "same"
        metrics.append(MetricDelta(
            label=label,
            before=str(val_before),
            after=str(val_after),
            direction=direction,
            value_change=delta,
        ))

    add_metric("Health Score", h_before, h_after, True)
    add_metric("Total Files", f_before, f_after, True)
    add_metric("Total Lines", l_before, l_after, True)
    add_metric("Test Cases", test_total_before, test_total_after, True)
    add_metric("Tests Passed", test_passed_before, test_passed_after, True)
    add_metric("Vulnerabilities", sec_before.total_vulnerabilities, sec_after.total_vulnerabilities, False)
    add_metric("Critical Issues", sec_before.critical, sec_after.critical, False)
    add_metric("Issues Count", len(issues_before), len(issues_after), False)

    # Check if identical
    is_identical = (
        h_delta == 0
        and f_before == f_after
        and l_before == l_after
        and len(issues_added) == 0
        and len(issues_removed) == 0
        and len(fw_added) == 0
        and len(fw_removed) == 0
        and sec_before.total_vulnerabilities == sec_after.total_vulnerabilities
    )

    return ScanComparison(
        scan_before_id=str(before.id),
        scan_after_id=str(after.id),
        repository_name=after.repository_name,
        time_between=time_between,
        health_score_before=h_before,
        health_score_after=h_after,
        health_score_delta=h_delta,
        files_before=f_before,
        files_after=f_after,
        files_delta=f_after - f_before,
        lines_before=l_before,
        lines_after=l_after,
        lines_delta=l_after - l_before,
        issues_before=sorted(issues_before),
        issues_after=sorted(issues_after),
        issues_added=issues_added,
        issues_removed=issues_removed,
        frameworks_before=sorted(fw_before),
        frameworks_after=sorted(fw_after),
        frameworks_added=fw_added,
        frameworks_removed=fw_removed,
        test_total_before=test_total_before,
        test_total_after=test_total_after,
        test_passed_before=test_passed_before,
        test_passed_after=test_passed_after,
        security_total_before=sec_before.total_vulnerabilities,
        security_total_after=sec_after.total_vulnerabilities,
        security_critical_before=sec_before.critical,
        security_critical_after=sec_after.critical,
        metrics=metrics,
        is_identical=is_identical,
    )
