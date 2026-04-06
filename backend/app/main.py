from fastapi import FastAPI

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
)

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
app.include_router(students.router)
app.include_router(classes.router)
app.include_router(enrollments.router)
app.include_router(exams.router)
app.include_router(exam_results.router)
