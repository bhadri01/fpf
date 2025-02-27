from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader

http_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
    api_key: str = Security(api_key_header),
):
    # Add your logic to validate the credentials and api_key here
    pass