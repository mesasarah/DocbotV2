"""
DOCBOT 2.0 -- FastAPI application entrypoint.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import ai_features, analytics, auth, chat, documents, health, knowledge_graph
from app.core.config import settings
from app.core.logging_config import configure_logging, logger
from app.db.session import Base, engine

# Import models so they're registered on Base.metadata before create_all runs.
from app.models import chat as _chat_models  # noqa: F401
from app.models import document as _document_models  # noqa: F401
from app.models import entity as _entity_models  # noqa: F401
from app.models import query_log as _query_log_models  # noqa: F401
from app.models import user as _user_models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("Starting {} in {} mode", settings.APP_NAME, settings.APP_ENV)
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down {}", settings.APP_NAME)


app = FastAPI(
    title=settings.APP_NAME,
    description="Offline, privacy-first document intelligence assistant.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on {} {}", request.method, request.url)
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again."},
    )
    # Belt-and-suspenders: make sure a crash never presents to the browser as
    # a confusing "blocked by CORS" error on top of the real problem.
    origin = request.headers.get("origin")
    if origin and origin in settings.CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(knowledge_graph.router)
app.include_router(ai_features.router)
app.include_router(analytics.router)
