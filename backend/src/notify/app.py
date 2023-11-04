import os
from asyncio import get_running_loop

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from backend.src.notify.api.dependencies import services
from backend.src.notify.api.v1.router import v1_router
from backend.src.notify.config import get_settings
from backend.src.notify.extensions.db import create_mongo_connection, get_my_sql_db_connection

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

    # attach_exception_handlers(app)

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
            my_sql_connection=await get_my_sql_db_connection(
                user=settings.MY_SQL_DB_USER,
                host=settings.MY_SQL_DB_HOST,
                port=settings.MY_SQL_DB_PORT,
                db=settings.MY_SQL_DB_NAME,
                password=settings.MY_SQL_DB_PASSWORD,
                loop=get_running_loop(),
            ),
            mongo_db_connection=create_mongo_connection(db_url=settings.MONGO_DB_URL),
        )
