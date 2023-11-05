import logging

from fastapi import FastAPI, Request
from pydantic import ValidationError
from starlette.responses import JSONResponse

from src.notify.adapters.repos.exceptions import RepoObjectNotFound
from src.notify.adapters.services.base import ServiceError

logger = logging.getLogger(__name__)


async def catch_service_error(request: Request, exception: ServiceError):
    logger.debug(exception, exc_info=True)
    resp = {"message": "invalid data", "detail": [exception.message]}
    return JSONResponse(content=resp, status_code=400)


async def catch_validation_error(request: Request, exception: ValidationError):
    logger.debug(exception, exc_info=True)
    data = parse_pydantic_errors(exception.errors())
    return JSONResponse(status_code=400, content=data)


async def catch_not_found_error(request: Request, exception: RepoObjectNotFound):
    logger.debug(exception, exc_info=True)
    return JSONResponse(content={"detail": [exception.message]}, status_code=404)


exc_handler_dict = {
    ServiceError: catch_service_error,
    ValidationError: catch_validation_error,
    RepoObjectNotFound: catch_not_found_error,
}


def attach_exception_handlers(app: FastAPI):
    for exc, handler in exc_handler_dict.items():
        app.add_exception_handler(exc, handler)


def parse_pydantic_errors(error_list):
    result = {"message": "invalid data", "detail": []}
    for error in error_list:
        loc, msg = error["loc"][-1], error["msg"]
        if loc == "__root__":
            result["detail"].append(error["msg"])
        elif loc not in result:
            result[loc] = [msg]
        elif loc in result and msg not in result[loc]:
            result[loc].append(msg)
    return result
