from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import router as api_router
from app.config import settings
from app.dependencies import init_services, shutdown_services
from app.middleware.logging_middleware import (
    RequestLoggingMiddleware,
    configure_structlog,
)
from app.middleware.rate_limit_middleware import RateLimitMiddleware

BACKEND_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_structlog(settings.environment)
    init_services()
    yield
    shutdown_services()


app = FastAPI(
    title="AI Tree Tutor",
    description="Neuro-Symbolic Agentic AI for learning advanced tree data structures",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(api_router)

# Serve built frontend so the app works at http://localhost:8000
if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend_assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str):
        if full_path and (full_path.startswith("api/") or full_path == "api" or full_path.startswith("docs") or full_path.startswith("openapi")):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        from fastapi.responses import FileResponse
        return FileResponse(str(FRONTEND_DIST / "index.html"))

    print(f"  ▶ Frontend served from {FRONTEND_DIST}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
