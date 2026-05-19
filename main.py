"""
Mazaya Facility Manager — FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # --- Startup ---
    logger.info("Starting Mazaya FM backend...")

    # Create DB tables and seed sample data
    from migrations.init_db import init_db, seed_sample_vendors
    init_db()
    seed_sample_vendors()

    # Start APScheduler
    from agent.scheduler import start_scheduler
    start_scheduler()

    logger.info("Mazaya FM backend ready.")
    yield

    # --- Shutdown ---
    from agent.scheduler import stop_scheduler
    stop_scheduler()
    logger.info("Mazaya FM backend stopped.")


app = FastAPI(
    title="Mazaya Facility Manager API",
    description="Agentic Facility Manager for Al-Mazaya Healthcare Real Estate",
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

from routers.auth import router as auth_router
from routers.chat import router as chat_router
from routers.leads import router as leads_router
from routers.tickets import router as tickets_router
from routers.work_orders import router as work_orders_router
from routers.vendors import router as vendors_router
from routers.dashboard import router as dashboard_router
from routers.briefing import router as briefing_router

app.include_router(auth_router)
app.include_router(chat_router)   # /api/chat, /api/chat/stream (SSE), /api/chat/sessions/{id}
app.include_router(leads_router)
app.include_router(tickets_router)
app.include_router(work_orders_router)
app.include_router(vendors_router)
app.include_router(dashboard_router)
app.include_router(briefing_router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "mazaya-fm-backend"}


@app.get("/")
async def root():
    return {
        "service": "Mazaya Facility Manager API",
        "version": "1.0.0",
        "docs": "/docs",
    }
