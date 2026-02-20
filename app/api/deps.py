"""FastAPI dependencies for auth and common logic."""

from fastapi import Depends, Request
from app.api.auth.models import ApiKey
from app.core.database import verify_api_key, AuthError


async def get_api_key(request: Request) -> ApiKey:
    """FastAPI dependency that verifies the Bearer token and returns the ApiKey."""
    return await verify_api_key(request)
