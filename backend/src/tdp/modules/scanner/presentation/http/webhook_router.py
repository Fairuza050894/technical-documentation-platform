from fastapi import APIRouter, Header, HTTPException, Request, status
from pydantic import BaseModel

from tdp.modules.scanner.application.webhook_service import (
    WebhookApplicationService,
    WebhookEventDto,
    WebhookEventNotFoundError,
    WebhookSignatureError,
)

router = APIRouter(tags=["webhooks"])


class WebhookListResponse(BaseModel):
    items: list[WebhookEventDto]
    total: int


def webhook_signature_error_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=401,
        content={"detail": str(exc)},
    )


def webhook_not_found_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


# Dependency
async def get_webhook_service(request: Request) -> WebhookApplicationService:
    return request.app.state.webhook_service


from typing import Annotated
from fastapi import Depends

WebhookServiceDependency = Annotated[WebhookApplicationService, Depends(get_webhook_service)]


@router.post(
    "/scanner/webhooks/github",
    response_model=WebhookEventDto,
    status_code=status.HTTP_202_ACCEPTED,
)
async def github_webhook(
    request: Request,
    service: WebhookServiceDependency,
    x_github_event: str = Header(...),
    x_hub_signature_256: str = Header(default=""),
) -> WebhookEventDto:
    payload = await request.json()

    if x_github_event == "push":
        return await service.process_github_push(payload, x_hub_signature_256)
    elif x_github_event == "pull_request":
        return await service.process_github_pr(payload, x_hub_signature_256)
    else:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Event '{x_github_event}' acknowledged but not processed.",
        )


@router.get("/scanner/webhooks/events", response_model=WebhookListResponse)
async def list_webhook_events(
    service: WebhookServiceDependency,
    limit: int = 50,
) -> WebhookListResponse:
    events = await service.list_events(limit)
    return WebhookListResponse(items=events, total=len(events))


@router.get("/scanner/webhooks/events/{event_id}", response_model=WebhookEventDto)
async def get_webhook_event(
    event_id: str,
    service: WebhookServiceDependency,
) -> WebhookEventDto:
    return await service.get_event(event_id)
