import asyncio
from contextlib import suppress
from pathlib import Path

from tdp.modules.sources.application.ports import StoredArtifact
from tdp.modules.sources.domain.model import SourceFileName, SourceId


class LocalArtifactStore:
    def __init__(self, root_path: Path) -> None:
        self._root_path = root_path
        self._root_path.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        source_id: SourceId,
        file_name: SourceFileName,
        content: bytes,
    ) -> StoredArtifact:
        return await asyncio.to_thread(self._save, source_id, file_name, content)

    async def read(self, artifact_key: str) -> bytes:
        return await asyncio.to_thread(self._read, artifact_key)

    async def delete(self, artifact_key: str) -> None:
        await asyncio.to_thread(self._delete, artifact_key)

    def _save(
        self,
        source_id: SourceId,
        file_name: SourceFileName,
        content: bytes,
    ) -> StoredArtifact:
        relative_path = Path(str(source_id)) / f"source{file_name.suffix}"
        target = self._root_path / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(f"{target.suffix}.tmp")
        temporary.write_bytes(content)
        temporary.replace(target)
        return StoredArtifact(key=relative_path.as_posix())

    def _read(self, artifact_key: str) -> bytes:
        root = self._root_path.resolve()
        target = (root / Path(artifact_key)).resolve()
        if not target.is_relative_to(root):
            raise FileNotFoundError(artifact_key)
        return target.read_bytes()

    def _delete(self, artifact_key: str) -> None:
        root = self._root_path.resolve()
        target = (root / Path(artifact_key)).resolve()
        if not target.is_relative_to(root):
            return
        try:
            target.unlink()
        except FileNotFoundError:
            return
        with suppress(OSError):
            target.parent.rmdir()
