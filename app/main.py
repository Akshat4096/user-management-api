import logging
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import get_settings
from app.database import Base, engine
from app.routers.users import router as users_router

settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# For a small take-home assignment. For larger deployments, use Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="REST API for user management with best-effort Slack event notifications.",
    version="1.0.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
def root():
    return {"message": "User Management API is running. Visit /docs for API documentation."}


app.include_router(users_router)


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    # The assignment explicitly expects 400 for invalid request fields.
    errors = exc.errors()
    message = errors[0].get("msg", "Invalid request.") if errors else "Invalid request."
    return JSONResponse(status_code=400, content={"error": message})


@app.exception_handler(Exception)
async def unexpected_exception_handler(request, exc):
    logging.getLogger(__name__).exception("Unhandled application error.", exc_info=exc)
    return JSONResponse(status_code=500, content={"error": "Internal server error."})
