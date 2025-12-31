import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8800
    MODEL_THREADS: int = 0
    FORCE_PROVIDERS: str = "metal" # auto, cuda, coreml, cpu, metal
    MAX_WORKERS: int = 8
    MAX_CHUNK_LENGTH: int = 300

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
