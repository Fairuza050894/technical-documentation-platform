import hashlib
import json
from dataclasses import asdict

from tdp.identity.model import RequestPrincipal
from tdp.modules.evidence.application.dto import EvidenceArtifactDto
from tdp.modules.evidence.domain.errors import (
    EvidenceFeatureArchivedError,
    EvidenceFeatureNotFoundError,
    EvidenceProjectArchivedError,
    EvidenceProjectNotFoundError,
    EvidenceRepositoryScanNotCompletedError,
    EvidenceRepositoryScanNotFoundError,
    EvidenceWorkspaceArchivedError,
    EvidenceWorkspaceNotFoundError,
)
from tdp.modules.evidence.domain.model import (
    EvidenceArtifact,
    EvidenceCollectionMethod,
    EvidenceKind,
    EvidenceSourceSystem,
)
from tdp.modules.evidence.domain.repository import EvidenceRepository
from tdp.modules.features.domain.model import FeatureId, FeatureStatus
from tdp.modules.features.domain.repository import FeatureRepository
from tdp.modules.projects.domain.model import Project, ProjectId, ProjectStatus
from tdp.modules.projects.domain.repository import ProjectRepository
from tdp.modules.scanner.domain.model import ScanId, ScanResult, ScanStatus
from tdp.modules.scanner.domain.repository import ScanRepository
from tdp.modules.workspaces.domain.model import WorkspaceId, WorkspaceStatus
from tdp.modules.workspaces.domain.repository import WorkspaceRepository


class ScannerEvidenceApplicationService:
    """Converts completed repository scanner output into immutable evidence artifacts."""

    def __init__(
        self,
        evidence_repository: EvidenceRepository,
        scan_repository: ScanRepository,
        project_repository: ProjectRepository,
        workspace_repository: WorkspaceRepository,
        feature_repository: FeatureRepository,
    ) -> None:
        self._evidence_repository = evidence_repository
        self._scan_repository = scan_repository
        self._project_repository = project_repository
        self._workspace_repository = workspace_repository
        self._feature_repository = feature_repository

    async def register(
        self,
        *,
        project_id: str,
        scan_id: str,
        feature_id: str | None,
        principal: RequestPrincipal,
    ) -> list[EvidenceArtifactDto]:
        project = await self._require_project(project_id)
        resolved_feature_id = await self._validate_feature(project_id, feature_id)
        scan = await self._scan_repository.get(ScanId.from_string(scan_id))
        if scan is None:
            raise EvidenceRepositoryScanNotFoundError(
                f"Repository scan {scan_id} was not found."
            )
        if scan.status is not ScanStatus.COMPLETED or scan.completed_at is None:
            raise EvidenceRepositoryScanNotCompletedError(
                "Only completed repository scans can become evidence artifacts."
            )

        specs = (
            (
                EvidenceKind.REPOSITORY_SCAN,
                "repository",
                {
                    "repository_url": scan.repository_url,
                    "repository_name": scan.repository_name,
                    "branch": scan.branch,
                    "stage": scan.stage.value,
                    "file_analysis": asdict(scan.file_analysis),
                    "tech_stack": asdict(scan.tech_stack),
                    "health": asdict(scan.health),
                    "sonarqube": asdict(scan.sonarqube),
                },
            ),
            (
                EvidenceKind.TEST_RESULT,
                "quality",
                {
                    "test_suites": [asdict(item) for item in scan.test_suites],
                    "lint_results": [asdict(item) for item in scan.lint_results],
                },
            ),
            (
                EvidenceKind.SECURITY_RESULT,
                "security",
                {
                    "security_scan": asdict(scan.security_scan),
                    "sonarqube_security": {
                        "vulnerabilities": scan.sonarqube.vulnerabilities,
                        "security_rating": scan.sonarqube.security_rating,
                        "security_hotspots": scan.sonarqube.security_hotspots,
                        "security_score": scan.sonarqube.security_score,
                    },
                },
            ),
        )

        results: list[EvidenceArtifactDto] = []
        for kind, suffix, payload in specs:
            origin_id = f"{scan.id}:{suffix}"
            existing = await self._evidence_repository.get_artifact_by_origin(kind, origin_id)
            if existing is not None:
                results.append(EvidenceArtifactDto.from_domain(existing))
                continue
            artifact = EvidenceArtifact.create(
                workspace_id=project.workspace_id,
                project_id=str(project.id),
                feature_id=resolved_feature_id,
                kind=kind,
                source_system=EvidenceSourceSystem.REPOSITORY_SCANNER,
                source_reference=f"repository-scan:{scan.id}",
                origin_id=origin_id,
                checksum=_payload_checksum(payload),
                content_reference=f"repository-scan:{scan.id}#{suffix}",
                collection_method=EvidenceCollectionMethod.SCANNER_CAPTURE,
                collected_by=principal.audit_actor,
                captured_at=scan.completed_at,
            )
            await self._evidence_repository.add_artifact(artifact)
            results.append(EvidenceArtifactDto.from_domain(artifact))
        return results

    async def _require_project(self, project_id: str) -> Project:
        project = await self._project_repository.get(ProjectId.from_string(project_id))
        if project is None:
            raise EvidenceProjectNotFoundError(f"Project {project_id} was not found.")
        workspace = await self._workspace_repository.get(
            WorkspaceId.from_string(project.workspace_id)
        )
        if workspace is None:
            raise EvidenceWorkspaceNotFoundError(
                f"Workspace {project.workspace_id} for project {project_id} was not found."
            )
        if project.status is ProjectStatus.ARCHIVED:
            raise EvidenceProjectArchivedError(
                "Evidence mutations are not allowed for an archived project."
            )
        if workspace.status is WorkspaceStatus.ARCHIVED:
            raise EvidenceWorkspaceArchivedError(
                "Evidence mutations are not allowed for an archived workspace."
            )
        return project

    async def _validate_feature(self, project_id: str, feature_id: str | None) -> str | None:
        if feature_id is None:
            return None
        feature = await self._feature_repository.get(FeatureId.from_string(feature_id))
        if feature is None or feature.project_id != project_id:
            raise EvidenceFeatureNotFoundError(
                f"Feature {feature_id} was not found for project {project_id}."
            )
        if feature.status is FeatureStatus.ARCHIVED:
            raise EvidenceFeatureArchivedError(
                "New evidence cannot be scoped to an archived feature."
            )
        return str(feature.id)


def _payload_checksum(payload: object) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
