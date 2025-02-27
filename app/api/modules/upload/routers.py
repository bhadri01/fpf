import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Response, Request
from botocore.exceptions import ClientError
from sqlalchemy import select
from app.api.modules.auth.users.models import User
from app.core.config import settings
from app.core.database.db import get_read_session
from app.core.minio import s3_client
from jose import jwt


router = APIRouter()


# Bucket name should be set separately
MINIO_BUCKET_NAME = settings.minio_bucket

# Allowed file extensions and MIME types
ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png",
                      "webp", "pdf", "doc", "docx", "xlsx", "csv"}
ALLOWED_MIME_TYPES = {
    "image/jpeg", "image/png", "image/webp",
    "application/pdf", "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/csv"
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


# Ensure MinIO bucket exists


def ensure_bucket():
    try:
        s3_client.head_bucket(Bucket=MINIO_BUCKET_NAME)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "404":
            # Bucket does not exist, create it
            s3_client.create_bucket(Bucket=MINIO_BUCKET_NAME)
        elif error_code == "403":
            raise HTTPException(
                status_code=403, detail="Access denied to bucket.")
        else:
            raise HTTPException(
                status_code=500, detail=f"Failed to access bucket: {str(e)}")


ensure_bucket()


async def get_user_from_cookie(request: Request):
    minio_token = request.cookies.get("minioToken","")
    if minio_token:
        payload = jwt.decode(minio_token, settings.secret_key,
                             algorithms=[settings.algorithm])
        if payload.get("type") == "minio":
            # Retrieve user from database
            async for session in get_read_session():
                query = await session.execute(select(User).where(User.id == payload.get("id")))
                user = query.scalar_one_or_none()
                if not user:
                    raise HTTPException(status_code=401, detail="Unauthorized")
                return user

        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/object/{object_path:path}", name="Files")
async def serve_minio_file(object_path: str, ):
    # user=Depends(get_user_from_cookie)
    """
    Securely serve MinIO files using the MinIO token stored in an HttpOnly cookie.
    Example: GET /minio/files/uploads/example.png
    """
    try:
        # Fetch the file from MinIO
        response = s3_client.get_object(
            Bucket=MINIO_BUCKET_NAME, Key=object_path)

        # Stream the file back to the user
        return Response(
            content=response['Body'].read(),
            media_type=response['ContentType']  # Auto-detect file type
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving file: {str(e)}")


@router.post("/folders", name="Files")
async def create_folder(folder_path: str = Query(..., description="Folder path to create")):
    """
    Simulate folder creation in MinIO (MinIO does not support empty folders).
    """
    try:
        dummy_file_key = f"{folder_path}/.placeholder"
        s3_client.put_object(Bucket=MINIO_BUCKET_NAME,
                             Key=dummy_file_key, Body=b"")
        return {"message": "Folder created successfully", "folder": folder_path}
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create folder: {str(e)}")


async def save_file_to_minio(file: UploadFile, folder_path: str) -> str:
    """
    Upload file to MinIO inside the specified folder.
    """
    file_extension = file.filename.split(".")[-1].lower()
    # Validate file type and MIME type
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file type.")
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid MIME type.")
    # Validate file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, detail="File size exceeds 5MB limit.")
    # Generate a random filename
    random_filename = f"{uuid.uuid4().hex}.{file_extension}"
    file_key = f"{folder_path}/{random_filename}"
    # Upload to MinIO
    try:
        s3_client.upload_fileobj(
            file.file,
            MINIO_BUCKET_NAME,
            file_key,
            ExtraArgs={"ContentType": file.content_type}
        )
        file_url = f"/{MINIO_BUCKET_NAME}/{file_key}"
        return file_url
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.post("/upload", name="Files")
async def upload_file(
    file: UploadFile = File(...),
    folder_path: str = Query(..., description="Folder path to upload the file")
):
    """
    Upload file to MinIO inside a nested folder.
    """
    try:
        file_url = await save_file_to_minio(file, folder_path)
        return {"message": "File uploaded successfully", "file_url": file_url}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/files/{folder_path:path}", name="Files")
async def list_files(folder_path: str):
    """
    List files inside a folder in MinIO.
    """
    try:
        response = s3_client.list_objects_v2(
            Bucket=MINIO_BUCKET_NAME, Prefix=f"{folder_path}/", Delimiter="/")
        items = []
        if 'Contents' in response:
            for obj in response['Contents']:
                print(obj)
                if obj['Key'].endswith("/.placeholder"):
                    continue  # Ignore placeholder files
                item_type = "folder" if obj['Key'].endswith("/") else "file"
                items.append({
                    "name": obj['Key'].split("/")[-1],
                    "type": item_type,
                    "url": f"{MINIO_BUCKET_NAME}/{obj['Key']}",
                    "size": obj["Size"]
                })
        return {"current_folder": folder_path, "items": items}
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list files: {str(e)}")


@router.delete("/object/{file_path:path}", name="Files")
async def delete_file_or_folder(file_path: str):
    """
    Delete a file or folder from MinIO.
    """
    try:
        s3_client.delete_object(Bucket=MINIO_BUCKET_NAME, Key=file_path)
        return {"message": "File or folder deleted successfully"}
    except ClientError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to delete file or folder: {str(e)}")
