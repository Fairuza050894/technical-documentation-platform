# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Changelog Policy** - Formalized changelog and versioning policy (TDP-GOV-003) following Keep a Changelog and Semantic Versioning standards

### Changed
- **Header button alignment** - Re-scan and Delete buttons now consistently align to the right regardless of repository name length (PR #16)
- **Header layout** - Title row and actions use flexbox with space-between for consistent positioning
- **Scanner workspace consolidation** - Scanner workspace now serves as the single entry point for all scanner features (PR #14)
- **Documents tab UX** - Replaced text buttons (Select All / Deselect All) with SVG checkbox icons (PR #14)
- **Generate button text** - Shows "Select documents to generate" when no documents are selected (PR #14)
- **Document labels** - Replaced technical abbreviations (BRD, SRS, HLD) with readable labels (PR #15)
- **Sidebar items polish** - Added borders and white backgrounds to sidebar items (PR #14)
- **Tech stack tags** - Added border styling for better visual definition
- **Overview cards** - Added subtle box shadows for depth
- **CHANGELOG format** - Restructured to follow Keep a Changelog convention

### Removed
- **Scanner Dashboard page** - Redundant page removed; stats and alerts consolidated into Scanner Workspace (PR #14)
- **Generate Docs button** - Removed redundant header button; document generation handled via Documents tab (PR #16)
- **document-generation route** - Cleaned up unused route reference from router

## [0.1.0] - 2026-08-31

### Added
- **Repository Scanner** - Code health analysis, security scanning, and documentation generation
- **SonarQube Integration** - Dual scoring system with SonarQube quality gate comparison
- **Document Generation** - Deterministic document generation from scan evidence
- **Template System** - Document template management with 17 built-in templates
- **Project Workspace** - Multi-workspace support with project-centric routing
- **Audit Trail** - Change tracking and governance evidence
- **System Status** - Platform health monitoring dashboard
- **Branch Protection** - Main branch protection requiring PR approval before merge
