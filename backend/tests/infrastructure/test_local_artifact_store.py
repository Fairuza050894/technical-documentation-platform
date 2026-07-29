import asyncio
from pathlib import Path

from tdp.modules.sources.domain.model import SourceFileName, SourceId
from tdp.modules.sources.infrastructure.local_artifact_store import LocalArtifactStore


def test_artifact_store_writes_and_deletes_relative_artifact(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path)
    source_id = SourceId.new()

    stored = asyncio.run(store.save(source_id, SourceFileName("commerce.yaml"), b"openapi: 3.1.0"))

    target = tmp_path / stored.key
    assert target.read_bytes() == b"openapi: 3.1.0"

    asyncio.run(store.delete(stored.key))
    assert not target.exists()
