from tdp.modules.templates.domain.model import (
    DocumentTemplate,
    TemplateCategory,
    TemplateStandard,
)

BUILTIN_TEMPLATES: list[DocumentTemplate] = []


def _register(
    key: str,
    name: str,
    description: str,
    category: TemplateCategory,
    standard: TemplateStandard,
    content: str,
) -> None:
    BUILTIN_TEMPLATES.append(
        DocumentTemplate.create(
            key=key,
            name=name,
            description=description,
            category=category,
            standard=standard,
            content=content,
            is_builtin=True,
        )
    )


# -- Requirements --

_register(
    "BRD",
    "Business Requirements Document",
    "Structured business requirements following BABOK methodology.",
    TemplateCategory.REQUIREMENTS,
    TemplateStandard.BABOK,
    """# Business Requirements Document
## [Project Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Version | [auto] |
| Status | Draft |
| Author | [current user] |

---

## 1. Executive Summary

### 1.1 Business Problem
<!-- Masalah bisnis yang ingin diselesaikan -->

### 1.2 Proposed Solution
<!-- Solusi yang diusulkan secara high-level -->

### 1.3 Expected Benefits
<!-- Manfaat yang diharapkan -->

---

## 2. Business Objectives

| ID | Objective | Success Metric | Priority |
|----|-----------|---------------|----------|
| BO01 | | | Must |

---

## 3. Stakeholders

| Role | Name/Group | Interest | Influence | Communication |
|------|-----------|----------|-----------|---------------|
| Sponsor | | High | High | Weekly report |
| End User | | High | Low | Training |
| IT Team | | Medium | High | Daily standup |

---

## 4. Current State (As-Is)

### 4.1 Current Process
<!-- Deskripsi proses bisnis saat ini -->

### 4.2 Pain Points

| # | Pain Point | Impact | Affected Stakeholder |
|---|-----------|--------|---------------------|

---

## 5. Future State (To-Be)

### 5.1 Desired Process

### 5.2 Functional Requirements

| ID | Requirement | Priority | Acceptance Criteria |
|----|------------|----------|-------------------|
| FR01 | | Must | |

### 5.3 Non-Functional Requirements

| Category | Requirement | Target |
|----------|------------|--------|
| Performance | Response time | < 2 seconds |

### 5.4 Business Rules

| ID | Rule | Affected Requirements |
|----|------|----------------------|

---

## 6. Scope

### 6.1 In Scope
- [ ] Feature 1

### 6.2 Out of Scope

### 6.3 Assumptions

### 6.4 Constraints

---

## 7. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|

---

## 8. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
""",
)

_register(
    "PRD",
    "Product Requirements Document",
    "Product requirements with user stories and acceptance criteria.",
    TemplateCategory.REQUIREMENTS,
    TemplateStandard.IEEE_830,
    """# Product Requirements Document
## [Product Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Version | [auto] |
| Status | Draft |

---

## 1. Purpose and Scope

### 1.1 Purpose
### 1.2 Scope
### 1.3 Definitions

| Term | Definition |
|------|-----------|

---

## 2. User Personas

| Attribute | Detail |
|-----------|--------|
| Role | |
| Goals | |
| Pain Points | |

---

## 3. User Stories

| ID | As a... | I want to... | So that... | Priority | Acceptance Criteria |
|----|---------|-------------|-----------|----------|-------------------|
| US01 | | | | Must | |

---

## 4. Functional Requirements

| ID | Requirement | User Story | Priority | Status |
|----|------------|-----------|----------|--------|

---

## 5. Non-Functional Requirements

| ID | Category | Requirement | Metric | Target |
|----|----------|------------|--------|--------|

---

## 6. User Flows

<!-- Describe primary user flows -->

---

## 7. Data Model

<!-- High-level data entities -->

---

## 8. API Contract

| Endpoint | Method | Description | Auth |
|----------|--------|------------|------|

---

## 9. Release Criteria

| Criteria | Target |
|----------|--------|

---

## 10. Open Questions

| # | Question | Owner | Status |
|---|---------|-------|--------|

---

## 11. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
""",
)

_register(
    "SRS",
    "Software Requirements Specification",
    "Detailed software requirements following IEEE 830-1998.",
    TemplateCategory.REQUIREMENTS,
    TemplateStandard.IEEE_830,
    """# Software Requirements Specification
## [System Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Version | [auto] |
| Status | Draft |

---

## 1. Introduction

### 1.1 Purpose
### 1.2 Scope
### 1.3 Definitions
### 1.4 References

---

## 2. Overall Description

### 2.1 Product Perspective
### 2.2 Product Functions
### 2.3 User Characteristics
### 2.4 Constraints
### 2.5 Assumptions

---

## 3. Specific Requirements

### 3.1 Functional Requirements

| ID | Description | Input | Output | Priority |
|----|------------|-------|--------|----------|

### 3.2 Non-Functional Requirements

#### 3.2.1 Performance
#### 3.2.2 Security
#### 3.2.3 Reliability

### 3.3 Interface Requirements

#### 3.3.1 User Interfaces
#### 3.3.2 Software Interfaces

---

## 4. System Features

---

## 5. Appendices

### 5.1 Glossary
### 5.2 Issues List
""",
)

# -- Architecture --

_register(
    "ARCH",
    "System Architecture Document",
    "System architecture following ISO/IEC/IEEE 42010.",
    TemplateCategory.ARCHITECTURE,
    TemplateStandard.ISO_42010,
    """# System Architecture Document
## [System Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Version | [auto] |
| Status | Draft |

---

## 1. Introduction

### 1.1 Purpose
### 1.2 Scope
### 1.3 Definitions

---

## 2. Architectural Representation

### 2.1 System Context
<!-- Who uses the system and what external systems does it interact with? -->

### 2.2 Container View
<!-- Major deployable units and their responsibilities -->

### 2.3 Component View
<!-- Key components within each container -->

---

## 3. Architectural Goals and Constraints

| Goal/Constraint | Rationale |
|----------------|-----------|

---

## 4. Use Case View

---

## 5. Data Architecture

### 5.1 Database Schema
### 5.2 Data Flow

---

## 6. Deployment Architecture

---

## 7. Security Architecture

| Layer | Control | Implementation |
|-------|---------|---------------|
| Transport | TLS | HTTPS only |
| Authentication | JWT | OAuth2/OIDC |
| Authorization | RBAC | Role-based |

---

## 8. Quality Attributes

| Attribute | Scenario | Measure |
|-----------|---------|---------|

---

## 9. Technical Debt and Risks

| Item | Impact | Mitigation |
|------|--------|------------|
""",
)

_register(
    "API_DOC",
    "API Documentation",
    "REST API documentation with endpoint reference and examples.",
    TemplateCategory.ARCHITECTURE,
    TemplateStandard.OPENAPI_3,
    """# API Documentation
## [System Name] API

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Base URL | [auto] |
| Auth Method | [auto] |

---

## 1. Overview

### 1.1 Base URL
### 1.2 Authentication
### 1.3 Common Headers
### 1.4 Error Response Format

---

## 2. Endpoints

### 2.1 [Resource Name]

#### GET /api/[resource]

**Parameters:**

| Name | In | Type | Required | Description |
|------|----|------|----------|-------------|

**Response: 200 OK**

#### POST /api/[resource]

**Request Body:**
**Response: 201 Created**

---

## 3. Data Models

| Field | Type | Required | Description |
|-------|------|----------|-------------|

---

## 4. Changelog

| Version | Date | Changes |
|---------|------|---------|
""",
)

_register(
    "DB_DOC",
    "Database Schema Documentation",
    "Database schema documentation with ERD and data dictionary.",
    TemplateCategory.ARCHITECTURE,
    TemplateStandard.CUSTOM,
    """# Database Schema Documentation
## [System Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Database | [auto] |
| Version | [auto] |

---

## 1. Overview

| Metric | Value |
|--------|-------|
| Database Engine | |
| Total Tables | |

---

## 2. Entity Relationship Diagram

---

## 3. Tables

### 3.1 [table_name]

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|

**Indexes:**
**Foreign Keys:**

---

## 4. Relationships Summary

| From | To | Type | Description |
|------|----|------|-------------|

---

## 5. Data Dictionary

---

## 6. Migration History
""",
)

# -- Testing --

_register(
    "TEST_CASES",
    "Test Case Specification",
    "Test cases with steps, expected results, and traceability.",
    TemplateCategory.TESTING,
    TemplateStandard.IEEE_829,
    """# Test Case Specification
## [Project Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Version | [auto] |

---

## 1. Features to Test

| Feature | Priority | Requirement ID |
|---------|----------|---------------|

---

## 2. Test Cases

### TC-001: [Test Case Name]

| Attribute | Detail |
|-----------|--------|
| ID | TC-001 |
| Feature | |
| Requirement | FR-001 |
| Priority | High |
| Preconditions | |

| Step | Action | Expected Result | Actual Result | Status |
|------|--------|----------------|---------------|--------|

---

## 3. Test Data Requirements

---

## 4. Traceability Matrix

| Requirement | Test Case(s) | Coverage |
|------------|-------------|----------|
""",
)

_register(
    "UAT_REPORT",
    "UAT Report",
    "User acceptance test report with execution results and sign-off.",
    TemplateCategory.TESTING,
    TemplateStandard.IEEE_829,
    """# User Acceptance Test Report
## [Project Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Test Cycle | |
| Status | In Progress |

---

## 1. Test Summary

| Metric | Value |
|--------|-------|
| Total Test Cases | |
| Passed | |
| Failed | |
| Blocked | |
| Pass Rate | % |

---

## 2. Test Environment

---

## 3. Test Cases

| ID | Test Case | Expected | Actual | Status | Tester | Date |
|----|----------|----------|--------|--------|--------|------|

---

## 4. Defects Found

| ID | Severity | Description | Status | Assigned To |
|----|----------|-------------|--------|-------------|

---

## 5. Sign-Off

| Role | Name | Decision | Date |
|------|------|----------|------|
""",
)

_register(
    "TEST_REPORT",
    "Test Report",
    "Summary test report with metrics and coverage analysis.",
    TemplateCategory.TESTING,
    TemplateStandard.IEEE_829,
    """# Test Report
## [Project Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Report Date | [auto] |

---

## 1. Executive Summary

---

## 2. Test Results

| Category | Total | Passed | Failed | Pass Rate |
|----------|-------|--------|--------|-----------|

---

## 3. Defect Summary

| Severity | Open | Fixed | Total |
|----------|------|-------|-------|

---

## 4. Coverage Analysis

| Module | Coverage | Test Cases | Status |
|--------|----------|-----------|--------|

---

## 5. Recommendations

---

## 6. Approval

| Role | Name | Decision | Date |
|------|------|----------|------|
""",
)

# -- Operations --

_register(
    "DEPLOY_GUIDE",
    "Deployment Guide",
    "Step-by-step deployment instructions with verification.",
    TemplateCategory.OPERATIONS,
    TemplateStandard.CUSTOM,
    """# Deployment Guide
## [System Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Environment | Production/Staging |

---

## 1. Prerequisites

| Requirement | Version | Check Command |
|------------|---------|--------------|

---

## 2. Infrastructure Requirements

| Resource | Spec | Quantity |
|----------|------|----------|

---

## 3. Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|

---

## 4. Deployment Steps

### 4.1 Database Setup
### 4.2 Application Setup
### 4.3 Frontend Setup

---

## 5. Verification

| Step | Check | Expected |
|------|-------|---------|

---

## 6. Rollback Procedure

| Step | Action |
|------|--------|

---

## 7. Monitoring

| Metric | Tool | Threshold |
|--------|------|-----------|
""",
)

_register(
    "INSTALL_GUIDE",
    "Installation Guide",
    "Complete installation instructions with system requirements.",
    TemplateCategory.OPERATIONS,
    TemplateStandard.CUSTOM,
    """# Installation Guide
## [System Name]

---

## 1. System Requirements

### 1.1 Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|

### 1.2 Software

| Software | Version | Purpose |
|----------|---------|---------|

---

## 2. Pre-Installation Checklist

- [ ] Server provisioned
- [ ] Domain/DNS configured
- [ ] SSL certificate obtained

---

## 3. Installation Steps

### 3.1 Database
### 3.2 Application Server
### 3.3 Frontend
### 3.4 Reverse Proxy
### 3.5 SSL/TLS

---

## 4. Post-Installation Verification

| # | Check | Command | Expected |
|---|-------|---------|---------|

---

## 5. Configuration Reference

| Parameter | File | Default | Description |
|-----------|------|---------|-------------|
""",
)

_register(
    "SOP",
    "Standard Operating Procedure",
    "Operational procedures following ISO 9001:2015 requirements.",
    TemplateCategory.OPERATIONS,
    TemplateStandard.ISO_9001,
    """# Standard Operating Procedure
## [Procedure Name]

| Field | Value |
|-------|-------|
| Document ID | SOP-[XXX] |
| Version | [auto] |
| Effective Date | [date] |
| Review Date | [date + 1 year] |
| Owner | [role] |
| Approved By | [name] |

---

## 1. Purpose

## 2. Scope

## 3. Definitions

| Term | Definition |
|------|-----------|

## 4. Responsibilities

| Role | Responsibility |
|------|---------------|

## 5. Procedure

### 5.1 [Step Group 1]

| Step | Action | Who | When | Tools/Systems |
|------|--------|-----|------|---------------|

---

## 6. Records

| Record | Retention | Location |
|--------|----------|----------|

## 7. References

## 8. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
""",
)

# -- User-Facing --

_register(
    "USER_GUIDE",
    "User Guide",
    "End-user guide following ISO/IEC 26514.",
    TemplateCategory.USER_FACING,
    TemplateStandard.ISO_26514,
    """# User Guide
## [System Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Version | [auto] |
| Audience | End Users |

---

## 1. Getting Started

### 1.1 System Requirements
### 1.2 Accessing the System
### 1.3 Login

---

## 2. Dashboard Overview

| Area | Description |
|------|------------|

---

## 3. [Feature 1]

### 3.1 Purpose
### 3.2 How to Use

**Step 1:** [Action]
**Step 2:** [Action]

### 3.3 Tips and Notes

---

## 4. Frequently Asked Questions

| Question | Answer |
|----------|--------|

---

## 5. Troubleshooting

| Problem | Cause | Solution |
|---------|-------|---------|

---

## 6. Contact and Support
""",
)

_register(
    "ONBOARD_GUIDE",
    "Developer Onboarding Guide",
    "Technical onboarding guide for new team members.",
    TemplateCategory.USER_FACING,
    TemplateStandard.CUSTOM,
    """# Developer Onboarding Guide
## [System Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Audience | New Developers |

---

## 1. Welcome

### 1.1 About This System
### 1.2 Team Structure
### 1.3 Communication Channels

---

## 2. Getting Access

| System | Access | How to Get |
|--------|--------|-----------|

---

## 3. Development Setup

### 3.1 Prerequisites
### 3.2 Clone Repository
### 3.3 Install Dependencies
### 3.4 Run Locally
### 3.5 Verify Setup

---

## 4. System Architecture Overview

---

## 5. Key Concepts

| Concept | Description | Documentation |
|---------|------------|---------------|

---

## 6. Codebase Navigation

| Directory | Purpose |
|-----------|---------|

---

## 7. Development Workflow

1. Pick task from board
2. Create feature branch
3. Code and test locally
4. Submit pull request
5. Code review
6. Merge and deploy to staging

---

## 8. First Tasks

| # | Task | Difficulty | Time |
|---|------|-----------|------|

---

## 9. FAQ

| Question | Answer |
|----------|--------|
""",
)

_register(
    "RELEASE_NOTES",
    "Release Notes",
    "Release notes with features, fixes, and breaking changes.",
    TemplateCategory.USER_FACING,
    TemplateStandard.CUSTOM,
    """# Release Notes
## [System Name] Version [X.X.X]

**Release Date:** [auto]
**Release Type:** Major / Minor / Patch

---

## Summary

---

## New Features

| # | Feature | Description |
|---|---------|------------|

---

## Improvements

| # | Improvement | Description |
|---|------------|------------|

---

## Bug Fixes

| # | Bug | Description | Severity |
|---|-----|------------|----------|

---

## Breaking Changes

| # | Change | Migration Steps |
|---|--------|----------------|

---

## Known Issues

| # | Issue | Workaround |
|---|-------|-----------|
""",
)

# -- Governance --

_register(
    "HANDOVER",
    "Project Handover Document",
    "Project handover with access, documentation index, and sign-off.",
    TemplateCategory.GOVERNANCE,
    TemplateStandard.CUSTOM,
    """# Project Handover Document
## [Project Name]

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Handover Date | [date] |
| From | [name/team] |
| To | [name/team] |

---

## 1. Project Summary

| Attribute | Detail |
|-----------|--------|
| Project Name | |
| Duration | |
| Status | |
| Repository | |
| Live URL | |

---

## 2. Access and Credentials

| System | URL | Credentials Location | Notes |
|--------|-----|---------------------|-------|

---

## 3. Documentation Index

| Document | Location | Status |
|----------|----------|--------|

---

## 4. Known Issues and Technical Debt

| # | Issue | Severity | Workaround | Priority |
|---|-------|----------|-----------|----------|

---

## 5. Pending Items

| # | Item | Owner | Deadline | Status |
|---|------|-------|----------|--------|

---

## 6. Key Contacts

| Role | Name | Contact | Responsibility |
|------|------|---------|---------------|

---

## 7. Sign-Off

| Role | Name | Signature | Date |
|------|------|-----------|------|
""",
)

_register(
    "NCR",
    "Nonconformity Register",
    "Nonconformity and corrective action tracking for ISO 9001.",
    TemplateCategory.GOVERNANCE,
    TemplateStandard.ISO_9001,
    """# Nonconformity Register

| Field | Value |
|-------|-------|
| Document ID | [auto] |
| Version | [auto] |

---

## 1. Nonconformity Log

| ID | Date | Source | Description | Severity | Clause | Root Cause | Corrective Action | Owner | Due Date | Status |
|----|------|--------|-------------|----------|--------|-----------|-------------------|-------|----------|--------|

---

## 2. Corrective Action Summary

| NCR ID | Action | Assigned To | Due Date | Completed | Verified |
|--------|--------|------------|----------|-----------|----------|

---

## 3. Trend Analysis

| Period | Total NCRs | Major | Minor | Closed | Open |
|--------|-----------|-------|-------|--------|------|

---

## 4. Review Schedule

| Review Date | Participants | Notes |
|------------|-------------|-------|
""",
)
