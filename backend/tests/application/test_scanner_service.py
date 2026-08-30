import asyncio

import pytest

from tdp.modules.scanner.application.service import (
    ScannerApplicationService,
    ScanDto,
    ScanInProgressError,
    ScanNotFoundError,
)
from tdp.modules.scanner.domain.model import (
    ScanId,
    ScanResult,
    ScanStatus,
)
from tdp.modules.scanner.domain.repository import ScanRepository


class InMemoryScanRepository:
    def __init__(self) -> None:
        self._scans: dict[str, ScanResult] = {}

    async def save(self, scan: ScanResult) -> None:
        self._scans[str(scan.id)] = scan

    async def get(self, scan_id: ScanId) -> ScanResult | None:
        return self._scans.get(str(scan_id))

    async def list_all(self) -> list[ScanResult]:
        return sorted(
            self._scans.values(),
            key=lambda s: s.started_at,
            reverse=True,
        )

    async def delete(self, scan_id: ScanId) -> bool:
        key = str(scan_id)
        if key in self._scans:
            del self._scans[key]
            return True
        return False


class TestScannerServiceGetScan:
    @pytest.mark.asyncio
    async def test_get_existing_scan(self) -> None:
        repo = InMemoryScanRepository()
        service = ScannerApplicationService(repo)
        scan = ScanResult.create("https://github.com/org/repo.git")
        await repo.save(scan)

        result = await service.get_scan(str(scan.id))
        assert result.id == str(scan.id)

    @pytest.mark.asyncio
    async def test_get_nonexistent_scan_raises(self) -> None:
        repo = InMemoryScanRepository()
        service = ScannerApplicationService(repo)

        with pytest.raises(ScanNotFoundError):
            await service.get_scan("00000000-0000-0000-0000-000000000000")


class TestScannerServiceListScans:
    @pytest.mark.asyncio
    async def test_list_empty(self) -> None:
        repo = InMemoryScanRepository()
        service = ScannerApplicationService(repo)

        result = await service.list_scans()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_returns_all_scans(self) -> None:
        repo = InMemoryScanRepository()
        service = ScannerApplicationService(repo)
        scan1 = ScanResult.create("https://github.com/org/repo1.git")
        scan2 = ScanResult.create("https://github.com/org/repo2.git")
        await repo.save(scan1)
        await repo.save(scan2)

        result = await service.list_scans()
        assert len(result) == 2


class TestScannerServiceDeleteScan:
    @pytest.mark.asyncio
    async def test_delete_existing_scan(self) -> None:
        repo = InMemoryScanRepository()
        service = ScannerApplicationService(repo)
        scan = ScanResult.create("https://github.com/org/repo.git")
        await repo.save(scan)

        await service.delete_scan(str(scan.id))
        result = await service.list_scans()
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises(self) -> None:
        repo = InMemoryScanRepository()
        service = ScannerApplicationService(repo)

        with pytest.raises(ScanNotFoundError):
            await service.delete_scan("00000000-0000-0000-0000-000000000000")


class TestScannerServiceStartScan:
    @pytest.mark.asyncio
    async def test_start_scan_creates_new_scan(self) -> None:
        repo = InMemoryScanRepository()
        service = ScannerApplicationService(repo)

        result = await service.start_scan("https://github.com/org/repo.git", "main")
        assert result.status == "PENDING"
        assert result.repository_url == "https://github.com/org/repo.git"

        scans = await service.list_scans()
        assert len(scans) == 1


class TestScannerServiceRescan:
    @pytest.mark.asyncio
    async def test_rescan_creates_new_scan_for_same_repo(self) -> None:
        repo = InMemoryScanRepository()
        service = ScannerApplicationService(repo)
        original = ScanResult.create("https://github.com/org/repo.git", "main")
        original.status = ScanStatus.COMPLETED
        await repo.save(original)

        rescanned = await service.rescan(str(original.id))
        assert rescanned.id != str(original.id)
        assert rescanned.repository_url == original.repository_url
        assert rescanned.status == "PENDING"

        scans = await service.list_scans()
        assert len(scans) == 2

    @pytest.mark.asyncio
    async def test_rescan_nonexistent_raises(self) -> None:
        repo = InMemoryScanRepository()
        service = ScannerApplicationService(repo)

        with pytest.raises(ScanNotFoundError):
            await service.rescan("00000000-0000-0000-0000-000000000000")

    @pytest.mark.asyncio
    async def test_rescan_in_progress_raises(self) -> None:
        repo = InMemoryScanRepository()
        service = ScannerApplicationService(repo)
        scan = ScanResult.create("https://github.com/org/repo.git")
        scan.status = ScanStatus.CLONING
        await repo.save(scan)

        with pytest.raises(ScanInProgressError):
            await service.rescan(str(scan.id))


class TestScanDto:
    @pytest.mark.asyncio
    async def test_dto_from_domain(self) -> None:
        scan = ScanResult.create("https://github.com/org/repo.git", "main")
        dto = ScanDto.from_domain(scan)
        assert dto.id == str(scan.id)
        assert dto.repository_url == scan.repository_url
        assert dto.repository_name == "repo"
        assert dto.branch == "main"
        assert dto.status == "PENDING"
