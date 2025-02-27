from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse
from app.core.config import settings
from fastapi import HTTPException

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK,name="Root")
async def root():
    return {"detail": f"Welcome to the {settings.app_name}"}


@router.get("/health", response_model=bool,name="Root")
async def health():
    return True


@router.get("/metrics", response_class=PlainTextResponse,name="Root")
def metrics():
    return PlainTextResponse("Running")
