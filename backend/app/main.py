"""FastAPI Application entrypoint with security headers, CORS, and lifespan."""

import logging
from contextlib import asynccontextmanager

from app.api.endpoints import (
    admin_router,
    apps_router,
    audit_router,
    auth_router,
    docs_router,
    obligations_router,
    routes_router,
)
from app.core.clock import clock
from app.core.database import Base, SessionLocal, engine
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; object-src 'none';"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-initialize database tables and deterministic seed if empty
    try:
        from app.models.entities import User
        from app.services.seed import run_seed
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            user_count = db.query(User).count()
            if user_count == 0:
                logger.info("Empty database detected on startup. Auto-seeding initial AICTE dataset...")
                run_seed()
    except Exception as e:
        logger.error("Auto-schema/seed error on startup: %s", e)

    # Initialize virtual clock offset from DB on startup
    with SessionLocal() as db:
        try:
            clock.initialize(db)
        except Exception as e:
            logger.warning("Could not initialize clock from DB: %s", e)
    yield


app = FastAPI(
    title="AICTE Approval & Obligation Engine API",
    version="1.0.0",
    description="Deterministic workflow and compliance monitoring platform for AICTE approval process (SIH PS 26262)",
    lifespan=lifespan,
)

# Security Middlewares
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(apps_router, prefix="/api")
app.include_router(obligations_router, prefix="/api")
app.include_router(audit_router, prefix="/api")
app.include_router(docs_router, prefix="/api")
app.include_router(routes_router, prefix="/api")



@app.get("/health")
def health_check():
    return {"status": "ok", "system_time": clock.now().isoformat()}
