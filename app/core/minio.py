import boto3
from app.core.config import settings

# MinIO Configuration (Ensure this is just protocol, hostname, and port)
MINIO_ENDPOINT = settings.minio_endpoint
MINIO_ACCESS_KEY = settings.minio_access_key
MINIO_SECRET_KEY = settings.minio_secret_key
MINIO_SECURE = settings.minio_secure

# Initialize Boto3 S3 Client
s3_client = boto3.client(
    's3',
    endpoint_url=f"{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name="us-east-1"  # MinIO doesn't care about the region
)