from tdp.modules.scanner.domain.model import (
    FileAnalysis,
    HealthLevel,
    LintResult,
    ProjectHealth,
    SecurityScan,
    TechStack,
    TestSuite,
)


def calculate_health(
    tech_stack: TechStack,
    file_analysis: FileAnalysis,
    test_suites: list[TestSuite],
    lint_results: list[LintResult],
    security_scan: SecurityScan,
) -> ProjectHealth:
    issues: list[str] = []
    score = 0

    test_score = 0
    if tech_stack.has_tests:
        test_score += 15
        total = sum(s.total for s in test_suites)
        passed = sum(s.passed for s in test_suites)
        if total > 0:
            ratio = passed / total
            test_score += int(ratio * 15)
            if ratio < 0.8:
                issues.append(f"Test pass rate is {ratio:.0%}. Aim for 80%+.")
    else:
        issues.append("No test infrastructure detected.")
    score += test_score

    quality_score = 25
    if lint_results:
        total_issues = sum(r.total_issues for r in lint_results)
        if total_issues > 100:
            quality_score = 5
            issues.append(f"{total_issues} lint issues found.")
        elif total_issues > 50:
            quality_score = 10
        elif total_issues > 20:
            quality_score = 15
        elif total_issues > 0:
            quality_score = 20
    else:
        quality_score = 15 if not tech_stack.has_linting else 20
    score += quality_score

    security_score = 25
    if security_scan.total_vulnerabilities > 0:
        if security_scan.critical > 0:
            security_score = 0
            issues.append(f"{security_scan.critical} critical vulnerabilities!")
        elif security_scan.high > 0:
            security_score = 5
        elif security_scan.medium > 0:
            security_score = 15
        else:
            security_score = 20
    score += security_score

    doc_score = 0
    if file_analysis.has_readme:
        doc_score += 5
    else:
        issues.append("No README found.")
    if file_analysis.has_license:
        doc_score += 3
    if file_analysis.has_changelog:
        doc_score += 4
    else:
        issues.append("No CHANGELOG found.")
    if file_analysis.has_env_example:
        doc_score += 3
    if file_analysis.has_dockerfile:
        doc_score += 3
    if file_analysis.has_makefile:
        doc_score += 2
    score += doc_score

    def score_to_level(s: int, max_val: int) -> HealthLevel:
        ratio = s / max_val if max_val > 0 else 0
        if ratio >= 0.7:
            return HealthLevel.GOOD
        if ratio >= 0.4:
            return HealthLevel.WARNING
        return HealthLevel.CRITICAL

    overall = HealthLevel.GOOD if score >= 70 else HealthLevel.WARNING if score >= 40 else HealthLevel.CRITICAL

    return ProjectHealth(
        overall=overall,
        test_coverage=score_to_level(test_score, 30),
        code_quality=score_to_level(quality_score, 25),
        security=score_to_level(security_score, 25),
        documentation=score_to_level(doc_score, 20),
        score=score,
        issues=issues,
    )
