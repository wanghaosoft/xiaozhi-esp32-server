from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import settings as app_settings
from app.db_models import SettingsRecord
from app.schemas import BrainSettings


class SettingsService:
    def load(self, db: Session) -> BrainSettings:
        record = db.get(SettingsRecord, app_settings.settings_key)
        if record is None or not isinstance(record.payload, dict):
            defaults = BrainSettings(
                xiaozhi_target={
                    "base_url": app_settings.xiaozhi_base_url,
                    "secret": app_settings.xiaozhi_secret,
                }
            )
            self.save(db, defaults)
            return defaults
        return BrainSettings.model_validate(record.payload)

    def save(self, db: Session, value: BrainSettings) -> BrainSettings:
        record = db.get(SettingsRecord, app_settings.settings_key)
        payload = value.model_dump(mode="json")
        if record is None:
            record = SettingsRecord(key=app_settings.settings_key, payload=payload)
            db.add(record)
        else:
            record.payload = payload
        db.commit()
        db.refresh(record)
        return BrainSettings.model_validate(record.payload)
