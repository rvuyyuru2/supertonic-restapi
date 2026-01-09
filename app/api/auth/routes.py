from robyn import SubRouter, jsonify, Request, Response
from app.api.auth.models import ApiKey
from app.core.database import verify_api_key, AuthError
import secrets
from tortoise.exceptions import IntegrityError
import logging
import json

logger = logging.getLogger("supertonic-api")

router = SubRouter(__name__, prefix="")

def error_response(status_code: int, detail: str):
    return Response(
        status_code=status_code,
        headers={"Content-Type": "application/json"},
        description=json.dumps({"detail": detail})
    )

@router.post("/auth/create-key")
async def create_api_key(request: Request):
    """Admin endpoint to create keys (unprotected for demo, protect in prod!)"""
    try:
        # Check query params first (Swagger/Browser mostly sends params for this endpoint type)
        queries = request.query_params
        print(queries)
        name = queries.get("name", None)
        
        price_str = queries.get("price", "15.0") 
        price = float(price_str) if price_str else 15.0
        
        # Fallback to body if name not in query
        if not name:
            body_content = request.body
            if body_content:
                if isinstance(body_content, bytes):
                    body_content = body_content.decode("utf-8")
                
                # Check if body is not empty JSON "{}"
                if body_content.strip() and body_content.strip() != "{}":
                    try:
                        body = json.loads(body_content)
                        name = body.get("name")
                        price = float(body.get("price", 15.0))
                    except json.JSONDecodeError:
                        pass # Body was not valid JSON, ignore

        if not name:
             return error_response(400, "Name is required (query param or JSON body)")

        # Generate a random key
        key_str = secrets.token_urlsafe(32)
        api_key = await ApiKey.create(
            key=key_str, 
            name=name,
            price_per_million_chars=price
        )
        return jsonify({"name": name, "api": key_str, "api_key": str(api_key.id), "rate": f"${price}/1M chars"})
    except IntegrityError as e:
        logger.error(f"Integrity Error creating API Key: {e}")
        return error_response(400, "API Key creation failed due to data integrity issue.")
    except Exception as e:
        logger.error(f"Unexpected error creating API Key: {e}")
        return error_response(500, "Internal Server Error")

@router.get("/auth/usage")
async def get_my_usage(request: Request):
    try:
        api_key = await verify_api_key(request)
        
        # Calculate usage
        logs = await api_key.usage_logs.all()
        total_chars = sum(l.characters for l in logs)
        total_cost = sum(l.cost for l in logs)
        
        return jsonify({
            "client": api_key.name,
            "total_characters": total_chars,
            "total_cost": float(total_cost),
            "rate": api_key.price_per_million_chars
        })
    except AuthError as e:
        return error_response(e.status_code, e.detail)
    except Exception as e:
        logger.error(f"Error retrieving usage stats: {e}")
        return error_response(500, "Internal Server Error")
