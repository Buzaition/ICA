from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: list[Any] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.errors = errors or []


def error_response(message: str, errors: list[Any] | None = None) -> dict[str, Any]:
    return {"success": False, "message": message, "errors": errors or []}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(_: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(exc.message, exc.errors),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_response("Validation failed", jsonable_encoder(exc.errors())),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = str(exc.detail) if exc.detail else "Request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response(message),
        )
