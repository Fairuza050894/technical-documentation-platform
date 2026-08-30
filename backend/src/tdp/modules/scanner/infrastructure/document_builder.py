import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from tdp.modules.scanner.domain.model import ScanResult


class GeneratedDocument:
    def __init__(self, doc_id, scan_id, template_key, name, content, created_at):
        self.id = doc_id
        self.scan_id = scan_id
        self.template_key = template_key
        self.name = name
        self.content = content
        self.created_at = created_at

    def to_dict(self):
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "template_key": self.template_key,
            "name": self.name,
            "content": self.content,
            "created_at": self.created_at,
        }


def build_document(scan, template_key):
    builders = {
        "BRD": _build_brd,
        "SRS": _build_srs,
        "ARCH": _build_arch,
        "API_DOC": _build_api_doc,
        "DB_DOC": _build_db_doc,
        "TEST_CASES": _build_test_cases,
        "TEST_REPORT": _build_test_report,
        "UAT_REPORT": _build_uat_report,
        "DEPLOY_GUIDE": _build_deploy_guide,
        "INSTALL_GUIDE": _build_install_guide,
        "SOP": _build_sop,
        "USER_GUIDE": _build_user_guide,
        "RELEASE_NOTES": _build_release_notes,
        "HANDOVER": _build_handover,
    }
    builder = builders.get(template_key, _build_generic)
    content = builder(scan)
    return GeneratedDocument(
        doc_id=str(uuid4()),
        scan_id=str(scan.id),
        template_key=template_key,
        name=_get_name(template_key),
        content=content,
        created_at=datetime.now().isoformat(),
    )


def _get_name(key):
    names = {
        "BRD": "Business Requirements Document",
        "SRS": "Software Requirements Specification",
        "ARCH": "System Architecture Document",
        "API_DOC": "API Documentation",
        "DB_DOC": "Database Schema Documentation",
        "TEST_CASES": "Test Case Specification",
        "TEST_REPORT": "Test Report",
        "UAT_REPORT": "UAT Report",
        "DEPLOY_GUIDE": "Deployment Guide",
        "INSTALL_GUIDE": "Installation Guide",
        "SOP": "Standard Operating Procedure",
        "USER_GUIDE": "User Guide",
        "RELEASE_NOTES": "Release Notes",
        "HANDOVER": "Project Handover Document",
    }
    return names.get(key, "Document (" + key + ")")


def _ctx(scan):
    ts = scan.tech_stack
    fa = scan.file_analysis
    lang_list = ", ".join(ts.languages.keys()) or "N/A"
    fw_list = ", ".join(ts.frameworks) or "Not detected"
    db_list = ", ".join(ts.databases) or "Not detected"
    tool_list = ", ".join(ts.tools) or "Not detected"
    return {
        "repo_name": scan.repository_name,
        "repo_url": scan.repository_url,
        "branch": scan.branch,
        "languages": lang_list,
        "frameworks": fw_list,
        "databases": db_list,
        "tools": tool_list,
        "package_manager": ts.package_manager or "N/A",
        "has_docker": "Yes" if ts.has_docker else "No",
        "has_ci_cd": "Yes" if ts.has_ci_cd else "No",
        "has_tests": "Yes" if ts.has_tests else "No",
        "has_linting": "Yes" if ts.has_linting else "No",
        "total_files": str(fa.total_files),
        "total_lines": str(fa.total_lines),
        "health_score": str(scan.health.score),
        "health_overall": scan.health.overall.value,
        "test_coverage": scan.health.test_coverage.value,
        "code_quality": scan.health.code_quality.value,
        "security": scan.health.security.value,
        "documentation": scan.health.documentation.value,
        "issues": scan.health.issues,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "has_readme": "Yes" if fa.has_readme else "No",
        "has_license": "Yes" if fa.has_license else "No",
        "has_changelog": "Yes" if fa.has_changelog else "No",
        "directories": fa.directories,
        "languages_dict": ts.languages,
        "frameworks_list": ts.frameworks,
        "databases_list": ts.databases,
        "tools_list": ts.tools,
        "test_suites": scan.test_suites,
        "lint_results": scan.lint_results,
        "security_scan": scan.security_scan,
    }


def _issues_section(issues):
    if not issues:
        return "No critical issues detected."
    return "\n".join("- " + issue for issue in issues)


def _dir_tree(dirs):
    if not dirs:
        return "No directory structure detected."
    lines = []
    for d in sorted(dirs)[:30]:
        depth = d.count("/")
        indent = "  " * depth
        name = d.split("/")[-1]
        lines.append(indent + "- " + name + "/")
    if len(dirs) > 30:
        lines.append("  ... and " + str(len(dirs) - 30) + " more directories")
    return "\n".join(lines)


def _lang_breakdown(langs_dict):
    if not langs_dict:
        return "No languages detected."
    lines = []
    for lang, pct in sorted(langs_dict.items(), key=lambda x: -x[1]):
        bar_len = int(pct / 5)
        bar = "#" * bar_len
        lines.append("| " + lang.ljust(20) + " | " + str(pct).rjust(5) + "% | " + bar + " |")
    return "\n".join(lines)


def _test_summary(suites):
    if not suites:
        return "No test results available."
    lines = []
    total_all = sum(s.total for s in suites)
    passed_all = sum(s.passed for s in suites)
    failed_all = sum(s.failed for s in suites)
    rate = str(round(passed_all / total_all * 100, 1)) + "%" if total_all > 0 else "N/A"
    lines.append("Total: " + str(total_all) + " tests | Passed: " + str(passed_all) + " | Failed: " + str(failed_all) + " | Pass Rate: " + rate)
    for s in suites:
        lines.append("- " + s.name + " (" + s.framework + "): " + str(s.passed) + "/" + str(total_all) + " passed")
    return "\n".join(lines)


def _mermaid_architecture(c):
    nodes = []
    edges = []
    dirs = [d.lower() for d in c.get("directories", [])]
    langs = c.get("languages_dict", {})
    fws = c["frameworks_list"]
    has_backend = any(l in langs for l in ["Python", "Java", "Go", "Rust", "Ruby", "PHP", "C#"])
    has_frontend = any(l in langs for l in ["JavaScript", "TypeScript", "TypeScript (React)", "JavaScript (React)"])
    has_react = "React" in fws or "Next.js" in fws or "Vue.js" in fws or any("react" in d for d in dirs) or any("components" in d for d in dirs)
    has_api = any(fw in fws for fw in ["FastAPI", "Flask", "Django", "Express.js", "NestJS", "Spring Boot", "Gin", "Echo"])
    has_backend_dir = any(d.startswith("backend") or d.startswith("src/tdp") or d.startswith("server") or d.startswith("api") for d in dirs)
    has_frontend_dir = any(d.startswith("frontend") or d.startswith("src/modules") or d.startswith("client") or d.startswith("web") for d in dirs)
    is_monorepo = has_backend_dir and has_frontend_dir

    nodes.append('    User["End User"]')

    if is_monorepo:
        if has_react or has_frontend:
            nodes.append('    FE["Frontend Application"]')
            nodes.append('    subgraph FE_STACK ["Frontend Stack"]')
            nodes.append('        FE')
            nodes.append('    end')
            edges.append('    User --> FE')
        if has_api:
            fw_name = fws[0] if fws else "Backend API"
            nodes.append('    API["' + fw_name + ' API"]')
            nodes.append('    subgraph BE_STACK ["Backend Stack"]')
            nodes.append('        API')
            nodes.append('    end')
            if has_react or has_frontend:
                edges.append('    FE -->|"REST/GraphQL"| API')
            else:
                edges.append('    User --> API')
        else:
            nodes.append('    API["Backend API Server"]')
            nodes.append('    subgraph BE_STACK ["Backend Stack"]')
            nodes.append('        API')
            nodes.append('    end')
            if has_react or has_frontend:
                edges.append('    FE -->|"HTTP"| API')
            else:
                edges.append('    User --> API')
    elif has_react or has_frontend:
        nodes.append('    FE["' + (fws[0] if fws else "Frontend") + ' Application"]')
        edges.append('    User --> FE')
        if has_api:
            nodes.append('    API["API Server"]')
            edges.append('    FE -->|"REST"| API')
    elif has_api:
        fw_name = fws[0] if fws else "Backend API"
        nodes.append('    API["' + fw_name + ' Server"]')
        edges.append('    User -->|"HTTP"| API')
    elif has_backend:
        nodes.append('    APP["Application Server"]')
        edges.append('    User --> APP')
    else:
        nodes.append('    APP["Application"]')
        edges.append('    User --> APP')

    api_target = "API" if any("API[" in n for n in nodes) else "APP" if any("APP[" in n for n in nodes) else "FE"

    for db in c["databases_list"]:
        db_id = db.replace(" ", "_").replace("/", "_")
        nodes.append('    ' + db_id + '["' + db + '"]')
        edges.append('    ' + api_target + ' --> ' + db_id)

    if c["has_docker"] == "Yes":
        nodes.append('    Docker["Docker"]')
    if c["has_ci_cd"] == "Yes":
        nodes.append('    CICD["CI/CD Pipeline"]')
        edges.append('    CICD -.->|"build & deploy"| Docker')

    if c["has_tests"] == "Yes":
        nodes.append('    Tests["Test Suite"]')
        edges.append('    CICD -.->|"run tests"| Tests') if c["has_ci_cd"] == "Yes" else None

    lines = ["```mermaid", "graph TD"] + nodes + [e for e in edges if e is not None] + ["```"]
    return "\n".join(lines)


def _mermaid_er(databases_list):
    if not databases_list:
        return "<!-- No database detected to generate ER diagram -->"
    lines = [
        "```mermaid",
        "erDiagram",
        "    USER {",
        "        uuid id PK",
        "        string email",
        "        string name",
        "        datetime created_at",
        "    }",
        "    PROJECT {",
        "        uuid id PK",
        "        string name",
        "        string description",
        "        uuid owner_id FK",
        "        datetime created_at",
        "    }",
        "    DOCUMENT {",
        "        uuid id PK",
        "        uuid project_id FK",
        "        string title",
        "        string status",
        "        datetime updated_at",
        "    }",
        "    USER ||--o{ PROJECT : owns",
        "    PROJECT ||--o{ DOCUMENT : contains",
        "```",
        "",
        "> Note: This is an inferred schema based on common patterns. Update with your actual database schema.",
    ]
    return "\n".join(lines)


def _mermaid_sequence(frameworks_list):
    fw = frameworks_list[0] if frameworks_list else "Server"
    lines = [
        "```mermaid",
        "sequenceDiagram",
        "    participant C as Client",
        "    participant A as " + fw,
        "    participant D as Database",
        "    C->>A: HTTP Request",
        "    A->>A: Validate & Process",
        "    A->>D: Query Data",
        "    D-->>A: Result Set",
        "    A-->>C: HTTP Response",
        "```",
        "",
        "> Note: This is a generic request flow. Update with your actual API interactions.",
    ]
    return "\n".join(lines)


def _mermaid_deployment(c):
    lines = ["```mermaid", "graph LR"]
    lines.append('    Dev["Developer"] -->|"git push"| Repo["Git Repository"]')
    if c["has_ci_cd"] == "Yes":
        lines.append('    Repo -->|"trigger"| CI["CI/CD Pipeline"]')
        lines.append('    CI -->|"test"| Test["Test Suite"]')
        lines.append('    CI -->|"build"| Build["Build Artifacts"]')
    if c["has_docker"] == "Yes":
        lines.append('    Build -->|"docker build"| Image["Docker Image"]')
        lines.append('    Image -->|"deploy"| Prod["Production"]')
    else:
        lines.append('    Build -->|"deploy"| Prod["Production"]')
    lines.append('    Prod -->|"serve"| Users["End Users"]')
    lines += ["```"]
    return "\n".join(lines)


def _build_brd(scan):
    c = _ctx(scan)
    lines = [
        "# Business Requirements Document",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"] + "  ",
        "> **Health Score:** " + c["health_score"] + "/100 (" + c["health_overall"] + ")",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        "**" + c["repo_name"] + "** is a software project built with " + c["languages"] + ".",
        "The system uses " + c["frameworks"] + " and persists data in " + c["databases"] + ".",
        "",
        "## 2. Project Context",
        "",
        "| Attribute | Value |",
        "|-----------|-------|",
        "| Repository | " + c["repo_url"] + " |",
        "| Branch | " + c["branch"] + " |",
        "| Languages | " + c["languages"] + " |",
        "| Frameworks | " + c["frameworks"] + " |",
        "| Databases | " + c["databases"] + " |",
        "| Total Files | " + c["total_files"] + " |",
        "| Lines of Code | " + c["total_lines"] + " |",
        "",
        "### Language Breakdown",
        "",
        "| Language | Share | Distribution |",
        "|----------|-------|--------------|",
    ]
    for lang, pct in sorted(c["languages_dict"].items(), key=lambda x: -x[1]):
        bar = "#" * int(pct / 5)
        lines.append("| " + lang + " | " + str(pct) + "% | " + bar + " |")
    lines += [
        "",
        "## 3. Functional Requirements",
        "",
        "<!-- TODO: Define core business features and user stories -->",
        "",
        "## 4. Non-Functional Requirements",
        "",
        "| Requirement | Current Status |",
        "|-------------|----------------|",
        "| Testing | " + c["has_tests"] + " |",
        "| CI/CD | " + c["has_ci_cd"] + " |",
        "| Docker | " + c["has_docker"] + " |",
        "| Linting | " + c["has_linting"] + " |",
        "| License | " + c["has_license"] + " |",
        "",
        "## 5. Health Assessment",
        "",
        "| Metric | Status |",
        "|--------|--------|",
        "| Overall | " + c["health_overall"] + " (" + c["health_score"] + "/100) |",
        "| Test Coverage | " + c["test_coverage"] + " |",
        "| Code Quality | " + c["code_quality"] + " |",
        "| Security | " + c["security"] + " |",
        "| Documentation | " + c["documentation"] + " |",
        "",
        "### Issues",
        _issues_section(c["issues"]),
        "",
        "---",
        "*Auto-generated from repository analysis. Complete TODO sections with business-specific requirements.*",
    ]
    return "\n".join(lines)


def _build_srs(scan):
    c = _ctx(scan)
    lines = [
        "# Software Requirements Specification",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"] + "  ",
        "> **Version:** 1.0",
        "",
        "---",
        "",
        "## 1. Introduction",
        "",
        "This SRS defines the technical requirements for **" + c["repo_name"] + "**.",
        "",
        "## 2. Technology Stack",
        "",
        "| Component | Technology |",
        "|-----------|------------|",
        "| Languages | " + c["languages"] + " |",
        "| Frameworks | " + c["frameworks"] + " |",
        "| Databases | " + c["databases"] + " |",
        "| Package Manager | " + c["package_manager"] + " |",
        "| Docker | " + c["has_docker"] + " |",
        "| CI/CD | " + c["has_ci_cd"] + " |",
        "| Tools | " + c["tools"] + " |",
        "",
        "### Language Distribution",
        "",
        "| Language | Share |",
        "|----------|-------|",
    ]
    for lang, pct in sorted(c["languages_dict"].items(), key=lambda x: -x[1]):
        lines.append("| " + lang + " | " + str(pct) + "% |")
    lines += [
        "",
        "## 3. System Architecture",
        "",
        _mermaid_architecture(c),
        "",
        "## 4. Request Flow",
        "",
        _mermaid_sequence(c["frameworks_list"]),
        "",
        "## 5. Functional Requirements",
        "",
        "<!-- TODO: Define user stories and acceptance criteria -->",
        "",
        "## 6. Non-Functional Requirements",
        "",
        "| Requirement | Target | Current |",
        "|-------------|--------|---------|",
        "| Test Coverage | 80% | " + c["test_coverage"] + " |",
        "| Code Quality | Good | " + c["code_quality"] + " |",
        "| Security | No critical | " + c["security"] + " |",
        "| Documentation | Complete | " + c["documentation"] + " |",
        "",
        "## 7. Data Model",
        "",
        _mermaid_er(c["databases_list"]),
        "",
        "## 8. Health Status",
        "",
        "| Metric | Status |",
        "|--------|--------|",
        "| Overall | " + c["health_overall"] + " (" + c["health_score"] + "/100) |",
        "| Tests | " + c["test_coverage"] + " |",
        "| Quality | " + c["code_quality"] + " |",
        "| Security | " + c["security"] + " |",
        "",
        "### Issues",
        _issues_section(c["issues"]),
        "",
        "---",
        "*Auto-generated. Complete TODO sections with specific requirements.*",
    ]
    return "\n".join(lines)


def _build_arch(scan):
    c = _ctx(scan)
    lines = [
        "# System Architecture Document",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## 1. Overview",
        "",
        "**" + c["repo_name"] + "** is built with " + c["languages"] + ".",
        "",
        "## 2. Technology Stack",
        "",
        "| Layer | Technology |",
        "|-------|------------|",
        "| Languages | " + c["languages"] + " |",
        "| Frameworks | " + c["frameworks"] + " |",
        "| Databases | " + c["databases"] + " |",
        "| Infrastructure | " + ("Docker" if c["has_docker"] == "Yes" else "N/A") + ", " + ("CI/CD" if c["has_ci_cd"] == "Yes" else "No CI/CD") + " |",
        "| Tooling | " + c["tools"] + " |",
        "",
        "## 3. System Architecture Diagram",
        "",
        _mermaid_architecture(c),
        "",
        "## 4. Entity Relationship Diagram",
        "",
        _mermaid_er(c["databases_list"]),
        "",
        "## 5. Request Flow",
        "",
        _mermaid_sequence(c["frameworks_list"]),
        "",
        "## 6. Deployment Architecture",
        "",
        _mermaid_deployment(c),
        "",
        "## 7. Directory Structure",
        "",
        "The project contains **" + c["total_files"] + " files** across **" + str(len(c["directories"])) + " directories**.",
        "",
        "```",
        _dir_tree(c["directories"]),
        "```",
        "",
        "## 8. Health Assessment",
        "",
        "| Metric | Status |",
        "|--------|--------|",
        "| Score | " + c["health_score"] + "/100 |",
        "| Tests | " + c["test_coverage"] + " |",
        "| Quality | " + c["code_quality"] + " |",
        "| Security | " + c["security"] + " |",
        "",
        _issues_section(c["issues"]),
        "",
        "---",
        "*Auto-generated. Update diagrams with actual architecture details.*",
    ]
    return "\n".join(lines)


def _build_api_doc(scan):
    c = _ctx(scan)
    fw = c["frameworks_list"][0] if c["frameworks_list"] else "Backend"
    lines = [
        "# API Documentation",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Framework:** " + fw + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## 1. Overview",
        "",
        "API documentation for **" + c["repo_name"] + "** built with " + fw + ".",
        "",
        "## 2. Base URL",
        "",
        "| Environment | URL |",
        "|-------------|-----|",
        "| Development | http://localhost:8000/api |",
        "| Production | https://your-domain.com/api |",
        "",
        "## 3. Authentication",
        "",
        "<!-- TODO: Describe authentication method (JWT, API Key, OAuth) -->",
        "",
        "## 4. Request Flow",
        "",
        _mermaid_sequence(c["frameworks_list"]),
        "",
        "## 5. Endpoints",
        "",
        "### 5.1 Health Check",
        "",
        "```",
        "GET /health",
        "Response: { status: ok, version: 0.1.0 }",
        "```",
        "",
        "### 5.2 <!-- TODO: Add your API endpoints -->",
        "",
        "## 6. Error Codes",
        "",
        "| Code | Description |",
        "|------|-------------|",
        "| 400 | Bad Request - Invalid input |",
        "| 401 | Unauthorized - Authentication required |",
        "| 403 | Forbidden - Insufficient permissions |",
        "| 404 | Not Found - Resource does not exist |",
        "| 422 | Validation Error - Request validation failed |",
        "| 500 | Internal Server Error |",
        "",
        "## 7. Rate Limiting",
        "",
        "<!-- TODO: Describe rate limiting policies -->",
        "",
        "---",
        "*Auto-generated. Add specific endpoint documentation manually.*",
    ]
    return "\n".join(lines)


def _build_db_doc(scan):
    c = _ctx(scan)
    lines = [
        "# Database Schema Documentation",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Database:** " + c["databases"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## 1. Overview",
        "",
        "**" + c["repo_name"] + "** uses **" + c["databases"] + "** for data persistence.",
        "",
        "## 2. Entity Relationship Diagram",
        "",
        _mermaid_er(c["databases_list"]),
        "",
        "## 3. Tables",
        "",
        "<!-- TODO: Document each table with columns, types, and constraints -->",
        "",
        "## 4. Indexes",
        "",
        "<!-- TODO: Document database indexes -->",
        "",
        "## 5. Migrations",
        "",
        "<!-- TODO: Document migration strategy -->",
        "",
        "---",
        "*Auto-generated. Update ER diagram with actual schema.*",
    ]
    return "\n".join(lines)


def _build_test_cases(scan):
    c = _ctx(scan)
    lines = [
        "# Test Case Specification",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## 1. Test Strategy",
        "",
        _test_summary(c["test_suites"]),
        "",
        "## 2. Test Cases",
        "",
        "| ID | Module | Description | Steps | Expected | Priority |",
        "|----|--------|-------------|-------|----------|----------|",
        "| TC-001 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> | High |",
        "| TC-002 | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> | <!-- TODO --> | Medium |",
        "",
        "## 3. Test Environment",
        "",
        "<!-- TODO: Describe test environment setup -->",
        "",
        "---",
        "*Auto-generated. Add specific test cases for each module.*",
    ]
    return "\n".join(lines)


def _build_test_report(scan):
    c = _ctx(scan)
    tests_rows = []
    for suite in c["test_suites"]:
        rate = str(round(suite.passed / suite.total * 100, 1)) + "%" if suite.total > 0 else "N/A"
        tests_rows.append("| " + suite.name + " | " + suite.framework + " | " + str(suite.total) + " | " + str(suite.passed) + " | " + str(suite.failed) + " | " + rate + " |")
    lint_rows = []
    for lint in c["lint_results"]:
        lint_rows.append("| " + lint.tool + " | " + str(lint.total_issues) + " | " + str(lint.errors) + " | " + str(lint.warnings) + " |")
    if not lint_rows:
        lint_rows.append("| N/A | - | - | - |")
    sec = c["security_scan"]
    lines = [
        "# Test Report",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"] + "  ",
        "> **Health Score:** " + c["health_score"] + "/100",
        "",
        "---",
        "",
        "## 1. Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        "| Overall Health | " + c["health_overall"] + " |",
        "| Test Coverage | " + c["test_coverage"] + " |",
        "| Code Quality | " + c["code_quality"] + " |",
        "| Security | " + c["security"] + " |",
        "",
        "## 2. Test Results",
        "",
        "| Suite | Framework | Total | Passed | Failed | Pass Rate |",
        "|-------|-----------|-------|--------|--------|-----------|",
    ] + tests_rows + [
        "",
        "## 3. Code Quality",
        "",
        "| Tool | Issues | Errors | Warnings |",
        "|------|--------|--------|----------|",
    ] + lint_rows + [
        "",
        "## 4. Security Scan",
        "",
        "| Severity | Count |",
        "|----------|-------|",
        "| Critical | " + str(sec.critical) + " |",
        "| High | " + str(sec.high) + " |",
        "| Medium | " + str(sec.medium) + " |",
        "| Low | " + str(sec.low) + " |",
        "| **Total** | **" + str(sec.total_vulnerabilities) + "** |",
        "",
        "## 5. Issues",
        "",
        _issues_section(c["issues"]),
        "",
        "---",
        "*Auto-generated on " + c["date"] + "*",
    ]
    return "\n".join(lines)


def _build_uat_report(scan):
    c = _ctx(scan)
    lines = [
        "# UAT Report",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## 1. Summary",
        "",
        "UAT for **" + c["repo_name"] + "** - Health: " + c["health_score"] + "/100.",
        "",
        "## 2. Test Scenarios",
        "",
        "| ID | Scenario | Status | Tester | Notes |",
        "|----|----------|--------|--------|-------|",
        "| UAT-001 | <!-- TODO --> | Pending | | |",
        "",
        "## 3. Sign-off",
        "",
        "| Role | Name | Date | Status |",
        "|------|------|------|--------|",
        "| Product Owner | | | Pending |",
        "| QA Lead | | | Pending |",
        "",
        "---",
        "*Auto-generated. Complete test scenarios and sign-off.*",
    ]
    return "\n".join(lines)


def _build_deploy_guide(scan):
    c = _ctx(scan)
    lines = [
        "# Deployment Guide",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## 1. Prerequisites",
        "",
        "| Requirement | Value |",
        "|-------------|-------|",
        "| Package Manager | " + c["package_manager"] + " |",
        "| Docker | " + c["has_docker"] + " |",
        "| CI/CD | " + c["has_ci_cd"] + " |",
        "",
        "## 2. Deployment Flow",
        "",
        _mermaid_deployment(c),
        "",
        "## 3. Environment Variables",
        "",
        "<!-- TODO: List required environment variables -->",
        "",
        "```env",
        "DATABASE_URL=...",
        "API_KEY=...",
        "```",
        "",
    ]
    if c["has_docker"] == "Yes":
        lines += [
            "## 4. Docker Deployment",
            "",
            "```bash",
            "docker-compose build",
            "docker-compose up -d",
            "docker-compose ps",
            "docker-compose logs -f",
            "```",
        ]
    lines += [
        "",
        "## 5. Health Check",
        "",
        "```bash",
        "curl http://localhost:8000/api/health",
        "```",
        "",
        "---",
        "*Auto-generated. Add environment-specific details.*",
    ]
    return "\n".join(lines)


def _build_install_guide(scan):
    c = _ctx(scan)
    setup_cmd = "<!-- TODO -->"
    pm = c["package_manager"]
    if pm == "pip": setup_cmd = "pip install -r requirements.txt"
    elif pm == "npm": setup_cmd = "npm install"
    elif pm == "yarn": setup_cmd = "yarn install"
    elif pm == "pnpm": setup_cmd = "pnpm install"
    elif pm == "go modules": setup_cmd = "go mod download"
    elif pm == "cargo": setup_cmd = "cargo build"
    lines = [
        "# Installation Guide",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## 1. Prerequisites",
        "",
        "| Requirement | Value |",
        "|-------------|-------|",
        "| Languages | " + c["languages"] + " |",
        "| Package Manager | " + c["package_manager"] + " |",
        "",
        "## 2. Setup",
        "",
        "```bash",
        "git clone " + c["repo_url"],
        "cd " + c["repo_name"],
        setup_cmd,
        "```",
        "",
        "## 3. Run",
        "",
        "<!-- TODO: Add run commands -->",
        "",
        "---",
        "*Auto-generated. Add project-specific steps.*",
    ]
    return "\n".join(lines)


def _build_sop(scan):
    c = _ctx(scan)
    lines = [
        "# Standard Operating Procedure",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## 1. Development Workflow",
        "",
        "<!-- TODO: Branch strategy, code review process -->",
        "",
        "## 2. CI/CD Pipeline",
        "",
        "- CI/CD: " + c["has_ci_cd"],
        "- Linting: " + c["has_linting"],
        "- Tests: " + c["has_tests"],
        "",
        "## 3. Incident Response",
        "",
        "| Level | Description | Response Time |",
        "|-------|-------------|---------------|",
        "| Critical | System down | Immediate |",
        "| High | Major feature broken | 1 hour |",
        "| Medium | Minor issue | 4 hours |",
        "",
        "---",
        "*Auto-generated. Customize for your team.*",
    ]
    return "\n".join(lines)


def _build_user_guide(scan):
    c = _ctx(scan)
    lines = [
        "# User Guide",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## 1. Introduction",
        "",
        "Welcome to **" + c["repo_name"] + "**.",
        "",
        "<!-- TODO: Describe what the application does -->",
        "",
        "## 2. Getting Started",
        "",
        "<!-- TODO: Quick start guide -->",
        "",
        "## 3. Features",
        "",
        "<!-- TODO: Feature descriptions -->",
        "",
        "## 4. FAQ",
        "",
        "<!-- TODO: Common questions and answers -->",
        "",
        "---",
        "*Auto-generated. Add feature descriptions.*",
    ]
    return "\n".join(lines)


def _build_release_notes(scan):
    c = _ctx(scan)
    lines = [
        "# Release Notes",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## Version 1.0.0",
        "",
        "### Tech Stack",
        "- Languages: " + c["languages"],
        "- Frameworks: " + c["frameworks"],
        "- Databases: " + c["databases"],
        "",
        "### Features",
        "<!-- TODO: List features -->",
        "",
        "### Known Issues",
        _issues_section(c["issues"]),
        "",
        "### Health: " + c["health_score"] + "/100",
        "",
        "---",
        "*Auto-generated.*",
    ]
    return "\n".join(lines)


def _build_handover(scan):
    c = _ctx(scan)
    lines = [
        "# Project Handover Document",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## 1. Overview",
        "",
        "| Attribute | Value |",
        "|-----------|-------|",
        "| Repository | " + c["repo_url"] + " |",
        "| Stack | " + c["languages"] + ", " + c["frameworks"] + " |",
        "| Database | " + c["databases"] + " |",
        "| Package Manager | " + c["package_manager"] + " |",
        "",
        "## 2. Architecture",
        "",
        _mermaid_architecture(c),
        "",
        "## 3. Development Setup",
        "",
        "```bash",
        "git clone " + c["repo_url"],
        "cd " + c["repo_name"],
        "```",
        "",
        "- Docker: " + c["has_docker"],
        "- CI/CD: " + c["has_ci_cd"],
        "- Tests: " + c["has_tests"],
        "",
        "## 4. Health Status",
        "",
        "| Metric | Status |",
        "|--------|--------|",
        "| Overall | " + c["health_overall"] + " (" + c["health_score"] + "/100) |",
        "| Tests | " + c["test_coverage"] + " |",
        "| Quality | " + c["code_quality"] + " |",
        "| Security | " + c["security"] + " |",
        "| Docs | " + c["documentation"] + " |",
        "",
        "### Issues",
        _issues_section(c["issues"]),
        "",
        "## 5. Contacts",
        "",
        "| Role | Name | Contact |",
        "|------|------|---------|",
        "| Tech Lead | <!-- TODO --> | <!-- TODO --> |",
        "",
        "---",
        "*Auto-generated. Complete TODO sections.*",
    ]
    return "\n".join(lines)


def _build_generic(scan):
    c = _ctx(scan)
    lines = [
        "# Document",
        "",
        "> **Project:** " + c["repo_name"] + "  ",
        "> **Generated:** " + c["date"],
        "",
        "---",
        "",
        "## Overview",
        "",
        "- Stack: " + c["languages"] + ", " + c["frameworks"],
        "- Health: " + c["health_score"] + "/100",
        "",
        "## Details",
        "",
        "<!-- TODO -->",
        "",
        "---",
        "*Auto-generated.*",
    ]
    return "\n".join(lines)


class DocumentStore:
    def __init__(self, database_path):
        self._database_path = database_path
        self._ensure_schema()

    def _connection(self):
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _ensure_schema(self):
        with self._connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS scanner_generated_docs (id TEXT PRIMARY KEY, scan_id TEXT NOT NULL, template_key TEXT NOT NULL, name TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT NOT NULL)"
            )

    def save(self, doc):
        with self._connection() as conn:
            conn.execute(
                "INSERT INTO scanner_generated_docs (id, scan_id, template_key, name, content, created_at) VALUES (?,?,?,?,?,?)",
                (doc.id, doc.scan_id, doc.template_key, doc.name, doc.content, doc.created_at),
            )

    def get_by_scan(self, scan_id):
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT * FROM scanner_generated_docs WHERE scan_id = ? ORDER BY created_at DESC",
                (scan_id,),
            ).fetchall()
            return [GeneratedDocument(row["id"], row["scan_id"], row["template_key"], row["name"], row["content"], row["created_at"]) for row in rows]

    def get(self, doc_id):
        with self._connection() as conn:
            row = conn.execute(
                "SELECT * FROM scanner_generated_docs WHERE id = ?", (doc_id,)
            ).fetchone()
            if row:
                return GeneratedDocument(row["id"], row["scan_id"], row["template_key"], row["name"], row["content"], row["created_at"])
            return None

    def delete_by_scan(self, scan_id):
        with self._connection() as conn:
            conn.execute("DELETE FROM scanner_generated_docs WHERE scan_id = ?", (scan_id,))
