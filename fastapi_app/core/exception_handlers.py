from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException, RequestValidationError


async def handle_httpexception(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'status': 'Failed',
            'message': str(exc.detail)
        }
    )


async def handle_validation_exception(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            'status': 'Failed',
            'message': 'Invalid user input'
        }
    )
