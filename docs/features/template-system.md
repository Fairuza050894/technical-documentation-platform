# Template System

## Overview

The template system provides 17 built-in document templates following international standards (IEEE 830, IEEE 829, ISO 9001, ISO 26514, BABOK, etc.) and allows users to create custom templates by customizing built-in ones.

## Architecture

### Backend (Hexagonal Architecture)

src/tdp/modules/templates/
  domain/model.py          - DocumentTemplate, TemplateCategory, TemplateStandard
  domain/errors.py         - TemplateNotFoundError, TemplateKeyConflictError
  domain/repository.py     - TemplateRepository protocol
  application/dto.py       - TemplateDto, TemplateSummaryDto
  application/service.py   - TemplateApplicationService
  infrastructure/sqlite_repository.py - SqliteTemplateRepository
  infrastructure/builtin_templates.py - 17 built-in templates
  infrastructure/seed.py   - seed_builtin_templates (idempotent)
  presentation/http/router.py - FastAPI router

### Frontend

frontend/src/modules/templates/
  types.ts              - TemplateCategory, TemplateSummary, TemplateDetail
  api.ts                - listTemplates, getTemplate, createTemplate
  TemplateWorkspace.tsx - Category sidebar, grid, preview modal

## Built-in Templates (17)

| Key | Category | Standard | Document Type |
|-----|----------|----------|---------------|
| BRD | Requirements | BABOK | BRD |
| PRD | Requirements | IEEE 830 | PRD |
| SRS | Requirements | IEEE 830 | SRS |
| ARCH | Architecture | ISO 42010 | HLD |
| API_DOC | Architecture | OpenAPI 3.0 | LLD |
| DB_DOC | Architecture | Custom | LLD |
| TEST_CASES | Testing | IEEE 829 | UAT_EVIDENCE |
| UAT_REPORT | Testing | IEEE 829 | UAT_EVIDENCE |
| TEST_REPORT | Testing | IEEE 829 | AS_BUILT |
| DEPLOY_GUIDE | Operations | Custom | INSTALLATION_GUIDE |
| INSTALL_GUIDE | Operations | Custom | INSTALLATION_GUIDE |
| SOP | Operations | ISO 9001 | SOP |
| USER_GUIDE | User-Facing | ISO 26514 | USER_GUIDE |
| ONBOARD_GUIDE | User-Facing | Custom | DEVELOPER_ONBOARDING_BRIEF |
| RELEASE_NOTES | User-Facing | Custom | AS_BUILT |
| HANDOVER | Governance | Custom | PROJECT_HANDOVER |
| NCR | Governance | ISO 9001 | SOP |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/templates | List all (filter: ?category=, ?document_type=) |
| GET | /api/templates/{id} | Get template detail |
| GET | /api/templates/by-key/{key} | Get by key |
| POST | /api/templates | Create custom template |
| PATCH | /api/templates/{id} | Update custom template |
| DELETE | /api/templates/{id} | Delete custom template |
| POST | /api/templates/{id}/duplicate | Duplicate template |

## Workflow

### Customize Built-in Template
1. User clicks Customize on a built-in template
2. System prompts for new key (default: KEY_CUSTOM)
3. System duplicates with is_builtin=false, preserves document_type
4. Editor opens for custom copy
5. User edits content (logo, contact, sections)
6. User saves - version increments

## Key Design Decisions
1. Built-in templates are read-only - must customize to edit
2. document_type preserved on duplicate - ensures filtering works
3. Idempotent seed - only inserts if not present
4. Markdown preview in modal
5. 204 No Content handled in requestJson
