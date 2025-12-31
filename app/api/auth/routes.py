from fastapi import APIRouter, Depends, HTTPException
from app.api.auth.models import ApiKey
from app.core.database import verify_api_key
import secrets

from tortoise.exceptions import IntegrityError
import logging

logger = logging.getLogger("supertonic-api")

router = APIRouter()

@router.post("/auth/create-key")
async def create_api_key(name: str, price: float = 15.0):
    """Admin endpoint to create keys (unprotected for demo, protect in prod!)"""
    try:
        # Generate a random key
        key_str = secrets.token_urlsafe(32)
        api_key = await ApiKey.create(
            key=key_str, 
            name=name,
            price_per_million_chars=price
        )
        return {"name": name, "api": key_str, "api_key": api_key, "rate": f"${price}/1M chars"}
    except IntegrityError as e:
        logger.error(f"Integrity Error creating API Key: {e}")
        raise HTTPException(status_code=400, detail="API Key creation failed due to data integrity issue.")
    except Exception as e:
        logger.error(f"Unexpected error creating API Key: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/auth/usage")
async def get_my_usage(api_key: ApiKey = Depends(verify_api_key)):
    try:
        # Calculate usage
        # This is heavy for high throughput, optimize with aggregation queries later
        logs = await api_key.usage_logs.all()
        total_chars = sum(l.characters for l in logs)
        total_cost = sum(l.cost for l in logs)
        
        return {
            "client": api_key.name,
            "total_characters": total_chars,
            "total_cost": float(total_cost),
            "rate": api_key.price_per_million_chars
        }
    except Exception as e:
        logger.error(f"Error retrieving usage stats: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
