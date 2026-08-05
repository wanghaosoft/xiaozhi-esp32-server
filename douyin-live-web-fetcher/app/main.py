from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.config import settings
from app.database import Base, engine, get_db
from app.db_models import SettingsRecord
from app.schemas import BrainSettings, LiveEventIn, ManualCommandIn
from app.services.brain import LiveBrainService
from app.services.settings_service import SettingsService


app = FastAPI(title=settings.app_name)
settings_service = SettingsService()
brain_service = LiveBrainService()

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine, tables=[SettingsRecord.__table__])
    brain_service.start()


@app.on_event("shutdown")
def on_shutdown() -> None:
    brain_service.stop()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "env": settings.env}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/api/settings", response_model=BrainSettings)
def get_settings(db: Session = Depends(get_db)) -> BrainSettings:
    return settings_service.load(db)


@app.put("/api/settings", response_model=BrainSettings)
def update_settings(payload: BrainSettings, db: Session = Depends(get_db)) -> BrainSettings:
    return settings_service.save(db, payload)


@app.get("/api/dashboard")
def get_dashboard():
    return brain_service.get_snapshot()


@app.get("/api/events")
def list_events(limit: int = 100):
    return brain_service.list_events(limit)


@app.get("/api/commands")
def list_commands(limit: int = 100):
    return brain_service.list_commands(limit)


@app.post("/api/events/ingest")
def ingest_event(payload: LiveEventIn):
    return brain_service.ingest(payload)


@app.post("/api/commands/manual")
def enqueue_manual(payload: ManualCommandIn):
    brain_service.enqueue_manual(payload.text, payload.command_type, payload.priority, payload.interrupt)
    return {"status": "queued"}
