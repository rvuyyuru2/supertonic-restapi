from robyn import Robyn, jsonify, Response
from tortoise import Tortoise
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.tts import tts_service
from app.api import routes as tts_routes
from app.api.auth import routes as auth_routes
from app.core.database import get_db_config

setup_logging()

app = Robyn(__file__)

# CORS - Manual configuration for Robyn
app.add_response_header("Access-Control-Allow-Origin", "*")
app.add_response_header("Access-Control-Allow-Credentials", "true")
app.add_response_header("Access-Control-Allow-Methods", "*")
app.add_response_header("Access-Control-Allow-Headers", "*")

@app.options("*")
async def cors_preflight(request):
    return ""  # Robyn will attach the global headers above

@app.startup_handler
async def startup():
    # Initialize Tortoise
    db_config = get_db_config()
    await Tortoise.init(config=db_config)
    await Tortoise.generate_schemas()
    
    # Initialize Service
    tts_service.initialize()

@app.shutdown_handler
async def shutdown():
    await Tortoise.close_connections()

@app.get("/")
async def root(request):
    try:
        with open("app/static/index.html", "r") as f:
            return Response(
                status_code=200,
                headers={"Content-Type": "text/html"},
                description=f.read()
            )
    except FileNotFoundError:
        return jsonify({"message": "Go to /docs or API usage"})

@app.get("/robots.txt")
async def robots(request):
    try:
        with open("app/static/robots.txt", "r") as f:
            return Response(
                status_code=200,
                headers={"Content-Type": "text/plain"},
                description=f.read()
            )
    except FileNotFoundError:
        return Response(status_code=404, headers={}, description="Not Found")

@app.get("/sitemap.xml")
async def sitemap(request):
    try:
        with open("app/static/sitemap.xml", "r") as f:
            return Response(
                status_code=200,
                headers={"Content-Type": "application/xml"},
                description=f.read()
            )
    except FileNotFoundError:
        return Response(status_code=404, headers={}, description="Not Found")

@app.get("/health")
async def health_check(request):
    status = "healthy" if tts_service.model else "initializing"
    return jsonify({"status": status})

app.include_router(tts_routes.router)
app.include_router(auth_routes.router)


if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8800))
    host = os.getenv("HOST", "0.0.0.0")
    app.start(host=host, port=port)
