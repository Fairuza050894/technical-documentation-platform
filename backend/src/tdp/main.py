from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tdp.config import get_settings
from tdp.presentation.http.middleware.request_id import RequestIdMiddleware
from tdp.presentation.http.routers.health import router as health_router


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    application.add_middleware(RequestIdMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Content-Type", "X-Request-ID"],
    )
    application.include_router(health_router, prefix=settings.api_prefix)
    return application


app = create_app()
