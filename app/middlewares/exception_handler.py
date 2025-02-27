from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError, OperationalError, ProgrammingError, InterfaceError
from app.middlewares.middleware_response import json_response_with_cors
from fastapi.exceptions import RequestValidationError
from fastapi import Request, HTTPException
from jose.exceptions import JWTError
from json import JSONDecodeError
from logs.logging import logger
import asyncio
import re


# Handles Pydantic validation errors (Invalid request body)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        f"Validation error: {exc.errors()} on request {request.url}")
    return json_response_with_cors(
        status_code=422,
        content={"detail": "Invalid request format", "errors": exc.errors()}
    )

# Handles generic HTTP exceptions


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTP Exception {exc.status_code}: {exc.detail} - {request.url}")
    return json_response_with_cors(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Handles database-related errors


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logger.error(f"Database error on request {request.url}: {exc}")
    return json_response_with_cors(
        status_code=500,
        content={"detail": "A database error occurred. Please try again later."}
    )

# Handles unique constraint violations (e.g., duplicate key)


async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning(f"Database Integrity Error on {request.url}: {exc}")

    # Default error message
    error_message = "This record may already exist."

    # Extract details from the error message
    match = re.search(r'Key \((.*?)\)=\((.*?)\)(.*)', str(exc.orig))
    if match:
        field_name = match.group(1)  # Column that caused the error
        value = match.group(2)  # Duplicated value
        additional_info = match.group(3).strip()  # Additional information after the key-value pair
        error_message = f"{field_name} '{value}' {additional_info}"

    return json_response_with_cors(
        status_code=409,
        content={"detail": error_message}
    )

# Handles invalid data type or value size errors


async def data_error_handler(request: Request, exc: DataError):
    logger.warning(f"Database Data Error on {request.url}: {exc}")
    return json_response_with_cors(
        status_code=422,
        content={"detail": "Invalid data format. Please check your input values."}
    )

# Handles operational database errors (e.g., connection issues, deadlocks)


async def operational_error_handler(request: Request, exc: OperationalError):
    logger.error(f"Operational Database Error on {request.url}: {exc}")
    return json_response_with_cors(
        status_code=500,
        content={
            "detail": "A database connection issue occurred. Please try again later."}
    )

# Handles programming errors (e.g., invalid queries, syntax errors)


async def programming_error_handler(request: Request, exc: ProgrammingError):
    logger.error(f"Database Programming Error on {request.url}: {exc}")
    return json_response_with_cors(
        status_code=500,
        content={
            "detail": "A database query error occurred. Please check your query syntax."}
    )

# Handles interface-related errors (e.g., invalid database connection settings)


async def interface_error_handler(request: Request, exc: InterfaceError):
    logger.error(f"Database Interface Error on {request.url}: {exc}")
    return json_response_with_cors(
        status_code=500,
        content={
            "detail": "A database interface error occurred. Please check database connectivity."}
    )

# Handles timeout errors (e.g., long-running queries or external requests)


async def timeout_error_handler(request: Request, exc: asyncio.TimeoutError):
    logger.error(f"Timeout Error on {request.url}: {exc}")
    return json_response_with_cors(
        status_code=504,
        content={"detail": "The request timed out. Please try again later."}
    )

# Handles permission errors (e.g., user lacks required access)


async def permission_error_handler(request: Request, exc: PermissionError):
    logger.warning(f"Permission Denied on {request.url}: {exc}")
    return json_response_with_cors(
        status_code=403,
        content={"detail": "You do not have permission to perform this action."}
    )

# Handles authentication errors (e.g., invalid credentials)


async def authentication_error_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        logger.warning(f"Authentication Failed on {request.url}: {exc.detail}")
        return json_response_with_cors(
            status_code=401,
            content={
                "detail": exc.detail}
        )
    return await http_exception_handler(request, exc)

# Handles value errors (e.g., incorrect input data)


async def value_error_handler(request: Request, exc: ValueError):
    logger.warning(f"Value Error on {request.url}: {exc}")
    return json_response_with_cors(
        status_code=400,
        content={"detail": str(exc)}
    )

# Handles type errors (e.g., incorrect data type provided)


async def type_error_handler(request: Request, exc: TypeError):
    logger.warning(f"Type Error on {request.url}: {exc}")
    return json_response_with_cors(
        status_code=400,
        content={
            "detail": "Invalid data type provided. Please check your input format."}
    )

# Handles unexpected server errors


async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error: {exc}")
    return json_response_with_cors(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please contact support."}
    )

# Handles JWT errors (e.g., invalid token, expired token)


async def jwt_error_handler(request: Request, exc: JWTError):
    logger.warning(f"JWT Error on {request.url}: {exc}")
    return json_response_with_cors(
        status_code=401,
        content={"detail": "Invalid or expired token. Please provide a valid token."}
    )

# Handles json decode error


async def json_decode_error_handler(request: Request, exc: JSONDecodeError):
    logger.warning(f"JSON Decode Error on {request.url}: {exc}")
    return json_response_with_cors(
        status_code=400,
        content={"detail": "Invalid JSON format. Please check your input data."}
    )
