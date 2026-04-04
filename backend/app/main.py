from fastapi import FastAPI

from app.config import get_settings
from app.routers import schools, teachers

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(schools.router)
app.include_router(teachers.router)
