import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.seed import seed_dev_data
from app.database import SessionLocal

from app.config import get_settings
from app.models import enrollments
from app.routers import (
    schools,
    teachers,
    students,
    classes,
    enrollments,
    exams,
    exam_results,
    grading_schemas,
)

settings = get_settings()

ENABLE_DEV_SEED = os.getenv("ENABLE_DEV_SEED", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if ENABLE_DEV_SEED:
        db = SessionLocal()
        try:
            seed_dev_data(db)
        finally:
            db.close()

    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(schools.router)
app.include_router(teachers.router)
app.include_router(students.router)
app.include_router(classes.router)
app.include_router(enrollments.router)
app.include_router(exams.router)
app.include_router(exam_results.router)
app.include_router(grading_schemas.router)
