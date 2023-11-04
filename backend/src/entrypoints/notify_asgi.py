import uvicorn

from backend.src.logging_utils import configure_logging
from backend.src.notify.app import create_app
from backend.src.notify.config import get_settings

app = create_app()
settings = get_settings()

if __name__ == "__main__":
    configure_logging(settings.LOG_LEVEL)
    uvicorn.run(
        "src.entrypoints.notify_asgi:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
