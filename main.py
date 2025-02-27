from app.core.database.db import master_db_engine, get_read_session
from app.middlewares.userPermissions import PermissionMiddleware
from app.admin.ui.template_generator import generate_template
from app.utils.token_blacklist import cleanup_expired_tokens
from app.middlewares.http_bearer import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from app.core.permissions import load_permissions
from app.utils.base_path import path_conversion
from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Depends, Request
from app.core.database.base_model import Base
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.redis import redis_cache
from app.core.config import settings
from json import JSONDecodeError
from logs.logging import logger
from datetime import datetime
from app.api.models import *
from app.generator import *
from jose import JWTError
import uvicorn
import asyncio

from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError, OperationalError, ProgrammingError, InterfaceError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import RequestValidationError, HTTPException

# import expection handlers
from app.middlewares.exception_handler import (
    json_decode_error_handler,
    jwt_error_handler,
    validation_exception_handler,
    http_exception_handler,
    database_exception_handler,
    integrity_error_handler,
    data_error_handler,
    operational_error_handler,
    programming_error_handler,
    interface_error_handler,
    timeout_error_handler,
    permission_error_handler,
    authentication_error_handler,
    value_error_handler,
    type_error_handler,
    global_exception_handler
)

# admin route import
from app.admin.endpoints import router as super_admin_router

# modules route import
from app.api.modules.upload.routers import router as upload_router
from app.api.modules.auth.authentication.routers import router as authentication_router
from app.api.modules.root.routers import router as root_router


# Determine if running in production
ENV = settings.environment

# Disable documentation if in production
if ENV == "production":
    app = FastAPI(docs_url=None, redoc_url=None, root_path=settings.base_path)
else:
    app = FastAPI(title=settings.app_name, version="0.1.0",
                  swagger_ui_parameters={"persistAuthorization": True},
                  root_path=settings.base_path
                  )

# Include exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(DataError, data_error_handler)
app.add_exception_handler(OperationalError, operational_error_handler)
app.add_exception_handler(ProgrammingError, programming_error_handler)
app.add_exception_handler(InterfaceError, interface_error_handler)
app.add_exception_handler(asyncio.TimeoutError, timeout_error_handler)
app.add_exception_handler(PermissionError, permission_error_handler)
app.add_exception_handler(HTTPException, authentication_error_handler)
app.add_exception_handler(ValueError, value_error_handler)
app.add_exception_handler(TypeError, type_error_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(JWTError, jwt_error_handler)
app.add_exception_handler(JSONDecodeError, json_decode_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Middleware to enforce root_path
@app.middleware("http")
async def enforce_root_path(request: Request, call_next):
    if not request.url.path.startswith(settings.base_path):
        return RedirectResponse(url=path_conversion(request.url.path))
    return await call_next(request)

# Middleware to enforce permissions
app.add_middleware(PermissionMiddleware)

# Serve static files from the "static" directory
app.mount("/public", StaticFiles(directory="./public"), name="static")


# Include routers

# Admin routes
app.include_router(super_admin_router, prefix="/admin", tags=["Admin"], include_in_schema=False)

# API routes
app.include_router(root_router,tags=["Root"], dependencies=[Depends(get_current_user)])
app.include_router(upload_router,  prefix="/api/storage",tags=["Upload"], dependencies=[Depends(get_current_user)])
app.include_router(authentication_router, prefix="/api/auth", dependencies=[Depends(get_current_user)])


async def start_periodic_cleanup():
    while True:
        await asyncio.sleep(60)
        try:
            logger.info(
                f'[*] FastAPI startup: Cleaning expired Tokens {datetime.now()}')
            cleanup_expired_tokens()
        except Exception as e:
            logger.error(f'Error during token cleanup: {e}')


async def refresh_permissions():
    """Refresh permission cache in Redis periodically."""
    while True:
        async for session in get_read_session():
            logger.info('[*] FastAPI startup: Refreshing Role Permissions ✅')
            await load_permissions(session)
        await asyncio.sleep(600)  # Refresh every 10 minutes


@asynccontextmanager
async def lifespan(app: FastAPI):

    async with master_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info('[*] Postgresql Database connected ✅')

    await redis_cache.connect()
    logger.info("[*] Redis Database connected ✅")

    async for db in get_read_session():
        await load_permissions(db)
        logger.info('[*] FastAPI startup: Routers Role Permissions loaded')

    # Periodically refresh permissions in Redis every 10 minutes
    asyncio.create_task(refresh_permissions())

    # Dynamically generate and include routers for all models
    models = get_models()
    for model in models:
        model_name = model.__name__
        router = create_crud_routes(model)
        app.include_router(
            router, prefix=f"/api/{model.__tablename__}", dependencies=[Depends(get_current_user)])
        logger.info(f"[*] FastAPI startup: {model_name} router included")

        # Generate templates for model
        generate_template(model, models)
        logger.info(f"[*] FastAPI startup: {model_name} templates generated")

    loop = asyncio.get_event_loop()
    loop.create_task(start_periodic_cleanup())
    logger.info('[*] FastAPI startup: Token thread started')

    yield

    loop.stop()
    logger.info('[*] FastAPI shutdown: Token thread stopping')
    logger.info('[*] FastAPI shutdown: Database disconnected')


app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
