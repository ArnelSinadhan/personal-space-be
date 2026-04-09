from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from app.auth.firebase import init_firebase
from app.config import settings
from app.database import engine
from app.routers import (
    account,
    dashboard,
    profile,
    projects,
    public,
    reports,
    resume,
    uploads,
    vault,
    workspaces,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    init_firebase()
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Personal Space API",
    description="Backend API for Personal Space dashboard & portfolio",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url="/redoc",
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# -- CORS --------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- Routers -----------------------------------------------------------------

app.include_router(profile.router)
app.include_router(account.router)
app.include_router(vault.router)
app.include_router(projects.router)
app.include_router(uploads.router)
app.include_router(workspaces.router)
app.include_router(resume.router)
app.include_router(reports.router)
app.include_router(dashboard.router)
app.include_router(public.router)

# -- Health check ------------------------------------------------------------


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html(request: Request):
    openapi_url = app.openapi_url or "/openapi.json"
    return templates.TemplateResponse(
        request=request,
        name="swagger.html",
        context={
            "title": app.title,
            "openapi_url": openapi_url,
        },
    )


@app.get("/health", tags=["system"])
async def health_check():
    db_status = "disconnected"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_status = "connected"
    except Exception:
        pass
    return {"status": "ok", "db": db_status}


@app.get("/", tags=["system"])
async def root():
    return {"message": "Personal Space API", "docs": "/docs"}
