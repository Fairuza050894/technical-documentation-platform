from typing import Protocol

from tdp.modules.evidence.domain.materialization import EvidenceMaterialization
from tdp.modules.evidence.domain.model import (
    Claim,
    ClaimId,
    EvidenceArtifact,
    EvidenceArtifactId,
    EvidenceKind,
)


class EvidenceRepository(Protocol):
    async def add_artifact(self, artifact: EvidenceArtifact) -> None: ...

    async def get_artifact(
        self,
        artifact_id: EvidenceArtifactId,
    ) -> EvidenceArtifact | None: ...

    async def get_artifact_by_origin(
        self,
        kind: EvidenceKind,
        origin_id: str,
    ) -> EvidenceArtifact | None: ...

    async def list_artifacts_by_project(
        self,
        project_id: str,
    ) -> list[EvidenceArtifact]: ...

    async def add_materialization(
        self,
        materialization: EvidenceMaterialization,
    ) -> None: ...

    async def get_materialization(
        self,
        artifact_id: EvidenceArtifactId,
    ) -> EvidenceMaterialization | None: ...

    async def list_materializations_by_project(
        self,
        project_id: str,
    ) -> list[EvidenceMaterialization]: ...

    async def add_claim(self, claim: Claim) -> None: ...

    async def get_claim(self, claim_id: ClaimId) -> Claim | None: ...

    async def list_claims_by_project(self, project_id: str) -> list[Claim]: ...
