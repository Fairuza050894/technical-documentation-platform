# Changelog and Versioning Policy

| Field | Value |
|---|---|
| Document ID | TDP-GOV-003 |
| Status | Controlled draft |
| Owner | Technical Documentation and Engineering |
| Classification | Internal project documentation |
| Review cadence | At each material change or release |
| Source of truth | This repository |

## Policy objective

Maintain a consistent, traceable changelog that follows Semantic Versioning and Keep a Changelog conventions, ensuring every user-visible change is documented and linked to its pull request.

## Scope

This policy applies to all changes committed to the main branch via pull request.

## Versioning standard

The project follows Semantic Versioning 2.0.0:

    MAJOR.MINOR.PATCH

    MAJOR - incompatible API or product changes
    MINOR - backward-compatible new capabilities
    PATCH - backward-compatible bug fixes, corrections, and polish

Pre-1.0 exceptions:

- MINOR releases may contain substantial evolution
- Incompatible changes must be documented in BREAKING CHANGE sections
- PATCH releases must not introduce new features

## Changelog format

The project follows Keep a Changelog 1.1.0 convention.

### Structure

    # Changelog

    ## [Unreleased]
    ### Added
    ### Changed
    ### Deprecated
    ### Removed
    ### Fixed
    ### Security

    ## [X.Y.Z] - YYYY-MM-DD
    ### Added
    ### Changed

### Entry rules

1. Every PR must include at least one entry under [Unreleased].
2. Entries are grouped by category: Added, Changed, Deprecated, Removed, Fixed, Security.
3. Each entry uses bold project/area reference and an em-dash description.
4. Format: - **Area** - Description of change

Example:

    ### Added
    - **Scanner Documents** - SVG checkbox icons for Select All / Deselect All

    ### Fixed
    - **Scanner Header** - Button alignment consistent across repository name lengths

    ### Removed
    - **Scanner Dashboard** - Redundant page removed; functionality merged into Scanner Workspace

## Version bumping

| Trigger | Version | Example |
|---|---|---|
| New feature, UI improvement | MINOR bump | 0.1.0 to 0.2.0 |
| Bug fix, CSS polish, text correction | PATCH bump | 0.2.0 to 0.2.1 |
| Breaking change, architecture overhaul | MAJOR bump | 0.x.x to 1.0.0 |
| Documentation only | PATCH bump | 0.2.1 to 0.2.2 |

### Version bump process

1. All changes accumulate under [Unreleased] in CHANGELOG.md.
2. When ready to release, rename [Unreleased] to [X.Y.Z] - YYYY-MM-DD.
3. Update version in CHANGELOG.md header, package.json (frontend), and pyproject.toml (backend) if applicable.
4. Create git tag: git tag vX.Y.Z
5. Push tag: git push origin vX.Y.Z

## PR workflow integration

Every pull request must:

1. Add entry to CHANGELOG.md under [Unreleased]
2. Reference the affected area in bold (e.g., **Scanner**, **Templates**, **Backend API**)
3. Use the correct category (Added, Changed, Fixed, Removed, Deprecated, Security)
4. Be linked to a GitHub issue or task when applicable

## Release cadence

| Release type | Cadence |
|---|---|
| PATCH | As needed for critical fixes |
| MINOR | Bi-weekly or when features accumulate |
| MAJOR | Planned milestone (e.g., 1.0.0 production release) |

## References

- Semantic Versioning 2.0.0: https://semver.org/
- Keep a Changelog 1.1.0: https://keepachangelog.com/
- Release Policy: docs/releases/release-policy.md
- Documentation Policy: docs/governance/documentation-policy.md
