import logging
import time
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.api.auth.models import ApiKey, UsageLog
from app.core.config import settings
from tortoise.transactions import in_transaction

logger = logging.getLogger("supertonic-api")
security = HTTPBearer(auto_error=False)

def get_db_config():
    return {
        "connections": {"default": "sqlite://db.sqlite3"},
        "apps": {
            "models": {
                "models": ["app.api.auth.models"],
                "default_connection": "default",
            }
        },
    }

async def verify_api_key(creds: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verifies the Bearer token provided in the Authorization header.
    """
    if not creds:
         raise HTTPException(status_code=401, detail="Missing API Key. Provide 'Authorization: Bearer <key>'")
    
    token = creds.credentials
    
    api_key = await ApiKey.get_or_none(key=token, is_active=True)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API Key")
        
    return api_key

async def track_usage(api_key: ApiKey, chars_count: int, cost: float):
    # Log usage
    await UsageLog.create(
        api_key=api_key,
        characters=chars_count,
        cost=cost
    )
    # Deduct balance if prepaid, or just track. For now assuming credit limit check?
    # Simple implementation: just track.
    
    # Check limits if any
    # if api_key.balance < cost: raise ...
