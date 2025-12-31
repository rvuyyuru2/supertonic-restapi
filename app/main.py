from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from tortoise.contrib.fastapi import register_tortoise
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.tts import tts_service
from app.api import routes as tts_routes
from app.api.auth import routes as auth_routes
from app.core.database import get_db_config

setup_logging()

app = FastAPI(title="Supertonic TTS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database
register_tortoise(
    app,
    config=get_db_config(),
    generate_schemas=True,
    add_exception_handlers=True,
)

@app.on_event("startup")
async def startup_event():
    tts_service.initialize()

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")

@app.get("/health")
async def health_check():
    status = "healthy" if tts_service.model else "initializing"
    return {"status": status}

app.include_router(tts_routes.router)
app.include_router(auth_routes.router)
