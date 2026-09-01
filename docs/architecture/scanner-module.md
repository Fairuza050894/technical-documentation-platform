# Scanner Module Architecture

## Overview

The Repository Scanner is a self-contained module that clones repositories, analyzes code structure, executes real tests and linters, integrates with SonarQube, and generates document suggestions.

## Clean Architecture Layers

```text
presentation/http/router.py
    └── application/service.py (ScannerApplicationService)
        ├── domain/model.py (ScanResult, ScanId, SonarQubeResult, ...)
        ├── domain/repository.py (ScanRepository interface)
        ├── domain/errors.py (ScannerError, ScanNotFoundError, ...)
        └── infrastructure/
            ├── git_operations.py (clone, cleanup)
            ├── file_analyzer.py (files, lines, languages)
            ├── tech_stack_detector.py (frameworks, tools, databases)
            ├── health_calculator.py (score from real data)
            ├── test_runner.py (pytest, jest, go test, flake8, eslint, pip-audit, npm audit)
            ├── scan_comparator.py (delta analysis)
            ├── sonarqube_client.py (SonarQube API integration)
            ├── document_generator.py (suggestions based on tech stack)
            ├── document_builder.py (document store)
            └── sqlite_repository.py (persistence)
```

## Scan Pipeline

```text
1. PENDING    → ScanResult.create()
2. CLONING    → clone_repository() → temp directory
3. ANALYZING  → analyze_files() → detect_tech_stack()
4. TESTING    → run_tests() → run_lint() → run_security_scan()
                → SonarQubeClient.fetch_metrics() (if configured)
5. GENERATING → calculate_health() → suggest_documents()
6. COMPLETED  → mark_completed()
```

## Dual Scoring System

When SonarQube is configured, the scanner produces two scores:

| Score | Source | Dimensions |
|-------|--------|------------|
| Internal | health_calculator.py | Test pass rate, lint issues, security vulns, documentation artifacts |
| SonarQube | sonarqube_client.py | Bugs, vulnerabilities, code smells, coverage, security/reliability/maintainability ratings |

The UI displays both scores side-by-side with a delta indicator.

## SonarQube Integration

Configuration via environment variables:

| Variable | Description |
|----------|-------------|
| SONARQUBE_URL | SonarQube instance URL (e.g., http://localhost:9000) |
| SONARQUBE_TOKEN | User token (not analysis token) for reading measures |
| SONARQUBE_PROJECT_KEY | SonarQube project key |

### Token types

- **GLOBAL_ANALYSIS_TOKEN** — For submitting analysis reports (used by sonar-scanner CLI)
- **USER_TOKEN** — For reading measures and issues via API (used by ScannerModule)

## Health Score Calculation

Internal health score (0-100) based on real data:

| Dimension | Max Points | Data Source |
|-----------|-----------|-------------|
| Test Coverage | 30 | test_runner.py (pass rate) |
| Code Quality | 25 | test_runner.py (lint issues) |
| Security | 25 | test_runner.py (vulnerabilities) |
| Documentation | 20 | file_analyzer.py (README, LICENSE, CHANGELOG, etc.) |

## Scan Comparison

compare_scans(before, after) produces:

- Health score delta
- Files/lines delta
- Issues added/removed
- Frameworks added/removed
- Test count delta
- Security vulnerability delta
- Metric-level comparison (direction: up/down/same)
- Time between scans

## Data Model

### ScanResult

Core aggregate containing all analysis results:

- id: ScanId — Unique identifier
- repository_url/name/branch — Repository metadata
- status: ScanStatus — PENDING → CLONING → ANALYZING → TESTING → GENERATING → COMPLETED/FAILED
- file_analysis: FileAnalysis — File counts, languages, config files
- tech_stack: TechStack — Frameworks, databases, tools, capabilities
- test_suites: list[TestSuite] — Test results per framework
- lint_results: list[LintResult] — Lint results per tool
- security_scan: SecurityScan — Vulnerability scan results
- sonarqube: SonarQubeResult — SonarQube metrics and scores
- health: ProjectHealth — Computed health score and issues
- suggestions: list[DocumentSuggestion] — Recommended documents

### SonarQubeResult

SonarQube metrics snapshot:

- Ratings: security, reliability, maintainability (A-E)
- Counts: bugs, vulnerabilities, code smells, hotspots
- Percentages: coverage, duplications
- Issues by severity: blocker, critical, major, minor, info
- Computed scores: total, security, reliability, maintainability, coverage
