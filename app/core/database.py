import logging
import time
from app.api.auth.models import ApiKey, UsageLog
from app.core.config import settings
from tortoise.transactions import in_transaction

logger = logging.getLogger("supertonic-api")

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

class AuthError(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail

async def verify_api_key(request):
    """
    Verifies the Bearer token provided in the Authorization header.
    """
    headers = request.headers
    # Robyn headers are often a specialized dict-like object
    auth_header = headers.get("Authorization") or headers.get("authorization")
    
    if not auth_header:
         raise AuthError(status_code=401, detail="Missing API Key. Provide 'Authorization: Bearer <key>'")
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthError(status_code=401, detail="Invalid Authorization header format. Expected 'Bearer <key>'")

    token = parts[1]
    
    api_key = await ApiKey.get_or_none(key=token, is_active=True)
    if not api_key:
        raise AuthError(status_code=401, detail="Invalid or inactive API Key")
        
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
