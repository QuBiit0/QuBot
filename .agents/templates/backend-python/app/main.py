from fastapi import FastAPI
from app.core.config import settings
from app.routers import health
# from app.routers.v1 import users  # Uncomment when created

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(health.router, tags=["health"])
# app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])

@app.on_event("startup")
def on_startup():
    from app.core.database import init_db
    init_db()
