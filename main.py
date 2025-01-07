from fastapi import FastAPI, status
from app.core.token_blacklist import cleanup_expired_tokens
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, db_engine
from fastapi.responses import PlainTextResponse
from app.generator import *
from app.api import *
import asyncio

# route import
from app.api.auth.routes import router as auth_router

app = FastAPI(title="FPF", version="0.1.0")

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Serve static files from the "static" directory
app.mount("/public", StaticFiles(directory="./public"), name="static")


@app.get("/", status_code=status.HTTP_200_OK, tags=["Root"])
async def root():
    return {"detail": "Welcome to the FPF Framework"}


@app.get("/health", tags=["Root"], response_model=bool)
async def health():
    return True


@app.get("/metrics", tags=["Root"], response_class=PlainTextResponse)
def metrics():
    return PlainTextResponse("Running")


app.include_router(auth_router, prefix="/api", tags=["Auth"])


async def start_periodic_cleanup():
    while True:
        await asyncio.sleep(3600)
        print(f'[*] FastAPI startup: Cleaning expired Tokens {datetime.now()}')
        await cleanup_expired_tokens()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print('[*] FastAPI startup: Database connected')

    loop = asyncio.get_event_loop()
    loop.create_task(start_periodic_cleanup())
    print('[*] FastAPI startup: Token thread started')

    yield

    loop.stop()
    print('[*] FastAPI shutdown: Token thread stopping')
    print('[*] FastAPI shutdown: Database disconnected')


app.router.lifespan_context = lifespan

# Dynamically generate and include routers for all models
models = get_models()
print(models)
for model in models:
    schemas = generate_schemas(model)
    model_name = model.__name__
    required_roles = model_configs.get(model_name, {})
    router = generate_crud_router(
        model, schemas, required_roles)
    app.include_router(router, prefix=f"/api/{model.__tablename__}")
    print(f"[*] FastAPI startup: {model_name} router included")
