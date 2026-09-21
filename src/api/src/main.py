from fastapi import FastAPI

from src.controllers.health import router as health_router


app = FastAPI(title="AI Fines API")
app.include_router(health_router)

