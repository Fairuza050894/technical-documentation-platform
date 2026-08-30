from typing import Annotated, cast

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from tdp.modules.scanner.application.service import ScannerApplicationService, ScanDto
from tdp.modules.scanner.domain.model import ScanId
from tdp.modules.scanner.domain.errors import ScannerError, ScanInProgressError, ScanNotFoundError
from tdp.modules.scanner.infrastructure.document_builder import DocumentStore, build_document
from tdp.modules.scanner.infrastructure.scan_comparator import compare_scans

router = APIRouter(tags=["scanner"])


class StartScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repository_url: str = Field(min_length=10)
    branch: str = Field(default="main", max_length=100)


class ScanComparisonResponse(BaseModel):
    scan_before_id: str
    scan_after_id: str
    repository_name: str
    time_between: str
    health_score_before: int
    health_score_after: int
    health_score_delta: int
    files_before: int
    files_after: int
    files_delta: int
    lines_before: int
    lines_after: int
    lines_delta: int
    issues_added: list[str]
    issues_removed: list[str]
    frameworks_added: list[str]
    frameworks_removed: list[str]
    test_total_before: int
    test_total_after: int
    test_passed_before: int
    test_passed_after: int
    security_total_before: int
    security_total_after: int
    security_critical_before: int
    security_critical_after: int
    metrics: list[dict]
    is_identical: bool


class GenerateDocumentsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    template_keys: list[str]


class GeneratedDocumentResponse(BaseModel):
    id: str
    scan_id: str
    template_key: str
    name: str
    content: str
    created_at: str


class ScanCollectionResponse(BaseModel):
    items: list[ScanDto]
    total: int


def get_scanner_service(request: Request) -> ScannerApplicationService:
    return cast(ScannerApplicationService, request.app.state.scanner_service)


def get_document_store(request: Request) -> DocumentStore:
    return cast(DocumentStore, request.app.state.document_store)


DocumentStoreDependency = Annotated[DocumentStore, Depends(get_document_store)]


ScannerServiceDependency = Annotated[ScannerApplicationService, Depends(get_scanner_service)]


@router.post("/scanner/scan", response_model=ScanDto, status_code=status.HTTP_202_ACCEPTED)
async def start_scan(payload: StartScanRequest, service: ScannerServiceDependency) -> ScanDto:
    return await service.start_scan(payload.repository_url, payload.branch)


@router.get("/scanner/scans", response_model=ScanCollectionResponse)
async def list_scans(service: ScannerServiceDependency) -> ScanCollectionResponse:
    scans = await service.list_scans()
    return ScanCollectionResponse(items=scans, total=len(scans))


@router.get("/scanner/scans/{scan_id}", response_model=ScanDto)
async def get_scan(scan_id: str, service: ScannerServiceDependency) -> ScanDto:
    return await service.get_scan(scan_id)


@router.delete("/scanner/scans/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scan(scan_id: str, service: ScannerServiceDependency) -> None:
    await service.delete_scan(scan_id)


@router.post("/scanner/scans/{scan_id}/generate", response_model=list[GeneratedDocumentResponse])
async def generate_documents(
    scan_id: str,
    payload: GenerateDocumentsRequest,
    service: ScannerServiceDependency,
    doc_store: DocumentStoreDependency,
) -> list[GeneratedDocumentResponse]:
    scan = await service.get_scan(scan_id)
    from tdp.modules.scanner.domain.model import ScanId
    scan_domain = await service._repository.get(ScanId.from_string(scan_id))
    if scan_domain is None:
        from tdp.modules.scanner.domain.errors import ScanNotFoundError
        raise ScanNotFoundError(f"Scan {scan_id} not found.")
    results = []
    for key in payload.template_keys:
        doc = build_document(scan_domain, key)
        doc_store.save(doc)
        results.append(GeneratedDocumentResponse(**doc.to_dict()))
    return results


@router.get("/scanner/scans/{scan_id}/documents", response_model=list[GeneratedDocumentResponse])
async def list_generated_documents(
    scan_id: str,
    doc_store: DocumentStoreDependency,
) -> list[GeneratedDocumentResponse]:
    docs = doc_store.get_by_scan(scan_id)
    return [GeneratedDocumentResponse(**d.to_dict()) for d in docs]


@router.get("/scanner/documents/{doc_id}", response_model=GeneratedDocumentResponse)
async def get_document(
    doc_id: str,
    doc_store: DocumentStoreDependency,
) -> GeneratedDocumentResponse:
    doc = doc_store.get(doc_id)
    if doc is None:
        from tdp.modules.scanner.domain.errors import ScanNotFoundError
        raise ScanNotFoundError(f"Document {doc_id} not found.")
    return GeneratedDocumentResponse(**doc.to_dict())


@router.post("/scanner/scans/{scan_id}/rescan", response_model=ScanDto, status_code=status.HTTP_202_ACCEPTED)
async def rescan(scan_id: str, service: ScannerServiceDependency) -> ScanDto:
    return await service.rescan(scan_id)


@router.get("/scanner/scans/{scan_id}/compare/{other_id}", response_model=ScanComparisonResponse)
async def compare_scans_endpoint(
    scan_id: str,
    other_id: str,
    service: ScannerServiceDependency,
) -> ScanComparisonResponse:
    scan_before = await service._repository.get(ScanId.from_string(other_id))
    scan_after = await service._repository.get(ScanId.from_string(scan_id))
    if scan_before is None or scan_after is None:
        raise ScanNotFoundError("One or both scans not found.")
    comparison = compare_scans(scan_before, scan_after)
    return ScanComparisonResponse(
        scan_before_id=comparison.scan_before_id,
        scan_after_id=comparison.scan_after_id,
        repository_name=comparison.repository_name,
        time_between=comparison.time_between,
        health_score_before=comparison.health_score_before,
        health_score_after=comparison.health_score_after,
        health_score_delta=comparison.health_score_delta,
        files_before=comparison.files_before,
        files_after=comparison.files_after,
        files_delta=comparison.files_delta,
        lines_before=comparison.lines_before,
        lines_after=comparison.lines_after,
        lines_delta=comparison.lines_delta,
        issues_added=comparison.issues_added,
        issues_removed=comparison.issues_removed,
        frameworks_added=comparison.frameworks_added,
        frameworks_removed=comparison.frameworks_removed,
        test_total_before=comparison.test_total_before,
        test_total_after=comparison.test_total_after,
        test_passed_before=comparison.test_passed_before,
        test_passed_after=comparison.test_passed_after,
        security_total_before=comparison.security_total_before,
        security_total_after=comparison.security_total_after,
        security_critical_before=comparison.security_critical_before,
        security_critical_after=comparison.security_critical_after,
        metrics=[{
            "label": m.label, "before": m.before, "after": m.after,
            "direction": m.direction, "value_change": m.value_change,
        } for m in comparison.metrics],
        is_identical=comparison.is_identical,
    )


async def scanner_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, ScannerError):
        raise exc
    request_id = getattr(request.state, "request_id", "unknown")
    code = 404 if isinstance(exc, ScanNotFoundError) else 409 if isinstance(exc, ScanInProgressError) else 400
    return JSONResponse(status_code=code, content={"error": {"code": exc.code, "message": str(exc), "requestId": request_id}})
