import uuid
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime

@dataclass
class Token:
    access_token: str
    refresh_token: str
    expires_at: Optional[float] = None
    
    def to_dict(self):
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at
        }
        
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            expires_at=data.get("expires_at")
        )

@dataclass
class Post:
    id: str
    media: str
    caption: str
    schedule: str  # e.g., "2026-07-11 09:00"
    status: str = "Pending"  # Pending, Uploading, Published, Failed
    publish_id: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def media_filename(self) -> str:
        import os
        return os.path.basename(self.media) if self.media else ""

    def to_dict(self):
        return {
            "id": self.id,
            "media": self.media,
            "caption": self.caption,
            "schedule": self.schedule,
            "status": self.status,
            "publish_id": self.publish_id,
            "error_message": self.error_message
        }
        
    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            media=data.get("media", ""),
            caption=data.get("caption", ""),
            schedule=data.get("schedule", ""),
            status=data.get("status", "Pending"),
            publish_id=data.get("publish_id"),
            error_message=data.get("error_message")
        )
