import secrets
import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, Body, HTTPException

from app.api.auth.models import ApiKey
from app.api.deps import get_api_key
from tortoise.exceptions import IntegrityError

logger = logging.getLogger("supertonic-api")

router = APIRouter()


@router.post("/auth/create-key")
async def create_api_key(
    name: Optional[str] = Query(default=None, description="Client name"),
    price: float = Query(default=15.0, description="Price per million chars"),
    body: Optional[dict] = Body(default=None),
):
    """Admin endpoint to create keys (unprotected for demo, protect in prod!)"""
    try:
        # Support body as fallback (e.g. Swagger sends JSON)
        if not name and body and isinstance(body, dict) and body:
            name = body.get("name")
            if body.get("price") is not None:
                price = float(body["price"])
        if not name:
            raise HTTPException(status_code=400, detail="Name is required (query param or JSON body)")

        key_str = secrets.token_urlsafe(32)
        api_key = await ApiKey.create(
            key=key_str,
            name=name,
            price_per_million_chars=price,
        )
        return {
            "name": name,
            "api": key_str,
            "api_key": str(api_key.id),
            "rate": f"${price}/1M chars",
        }
    except IntegrityError as e:
        logger.error(f"Integrity Error creating API Key: {e}")
        raise HTTPException(
            status_code=400,
            detail="API Key creation failed due to data integrity issue.",
        )
    except Exception as e:
        logger.error(f"Unexpected error creating API Key: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.get("/auth/usage")
async def get_my_usage(api_key: ApiKey = Depends(get_api_key)):
    try:
        logs = await api_key.usage_logs.all()
        total_chars = sum(l.characters for l in logs)
        total_cost = sum(l.cost for l in logs)

        return {
            "client": api_key.name,
            "total_characters": total_chars,
            "total_cost": float(total_cost),
            "rate": api_key.price_per_million_chars,
        }
    except Exception as e:
        logger.error(f"Error retrieving usage stats: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
