import os
from asyncio import get_running_loop

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.notify.api.dependencies import services
from src.notify.api.exception_handling import attach_exception_handlers
from src.notify.api.v1.router import v1_router
from src.notify.config import get_settings
from src.notify.extensions.db import (
    create_mongo_connection,
    get_my_sql_db_connection_pool,
)

settings = get_settings()


def create_app() -> FastAPI:
    """Application factory."""
    os.makedirs(settings.STATIC_DIR, exist_ok=True)

    docs_args = {}
    if settings.USE_DOCS:
        docs_args = {
            "docs_url": "/api/docs/",
            "openapi_url": "/api/openapi.json",
        }

    app = FastAPI(
        title="Notify service API",
        strict_slashes=True,
        **docs_args,
    )
    setup_middleware(app)

    app.include_router(v1_router, prefix="/api")

    attach_exception_handlers(app)

    register_events(app=app)

    return app


def setup_middleware(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    )


def register_events(app: FastAPI):
    @app.on_event("startup")
    async def init_service_manager():
        await services.init_service_manager(
            settings=settings,
            my_sql_connection_pool=await get_my_sql_db_connection_pool(
                host=settings.MY_SQL_DB_HOST,
                port=settings.MY_SQL_DB_PORT,
                user=settings.MY_SQL_DB_USER,
                password=settings.MY_SQL_DB_PASSWORD,
                db=settings.MY_SQL_DB_NAME,
                loop=get_running_loop(),
                charset=settings.MY_SQL_DB_CHARSET,
            ),
            mongo_db_connection=create_mongo_connection(db_url=settings.MONGO_DB_URL),
        )
