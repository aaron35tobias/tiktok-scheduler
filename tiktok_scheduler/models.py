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
class Profile:
    """A connected TikTok account's public profile info."""
    open_id: str = ""
    avatar_url: str = ""
    display_name: str = ""
    username: str = ""
    follower_count: Optional[int] = None
    following_count: Optional[int] = None
    likes_count: Optional[int] = None
    video_count: Optional[int] = None
    is_verified: bool = False

    def to_dict(self):
        return {
            "open_id": self.open_id,
            "avatar_url": self.avatar_url,
            "display_name": self.display_name,
            "username": self.username,
            "follower_count": self.follower_count,
            "following_count": self.following_count,
            "likes_count": self.likes_count,
            "video_count": self.video_count,
            "is_verified": self.is_verified,
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            open_id=data.get("open_id", ""),
            avatar_url=data.get("avatar_url", ""),
            display_name=data.get("display_name", ""),
            username=data.get("username", ""),
            follower_count=data.get("follower_count"),
            following_count=data.get("following_count"),
            likes_count=data.get("likes_count"),
            video_count=data.get("video_count"),
            is_verified=data.get("is_verified", False),
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
    hashtags: str = ""
    privacy: str = "SELF_ONLY"          # PUBLIC_TO_EVERYONE, MUTUAL_FOLLOW_FRIENDS, SELF_ONLY
    allow_comments: bool = True
    allow_duet: bool = True
    allow_stitch: bool = True
    account_open_id: str = ""           # which connected account this post belongs to

    @property
    def media_filename(self) -> str:
        import os
        return os.path.basename(self.media) if self.media else ""

    @property
    def full_caption(self) -> str:
        """Caption plus hashtags, ready to publish."""
        tags = (self.hashtags or "").strip()
        if tags:
            return f"{self.caption} {tags}".strip()
        return self.caption

    @property
    def schedule_dt(self):
        """Parsed schedule datetime, or None if unparseable."""
        from datetime import datetime
        if not self.schedule:
            return None
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(self.schedule, fmt)
            except ValueError:
                continue
        return None

    def to_dict(self):
        return {
            "id": self.id,
            "media": self.media,
            "caption": self.caption,
            "schedule": self.schedule,
            "status": self.status,
            "publish_id": self.publish_id,
            "error_message": self.error_message,
            "hashtags": self.hashtags,
            "privacy": self.privacy,
            "allow_comments": self.allow_comments,
            "allow_duet": self.allow_duet,
            "allow_stitch": self.allow_stitch,
            "account_open_id": self.account_open_id,
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
            error_message=data.get("error_message"),
            hashtags=data.get("hashtags", ""),
            privacy=data.get("privacy", "SELF_ONLY"),
            allow_comments=data.get("allow_comments", True),
            allow_duet=data.get("allow_duet", True),
            allow_stitch=data.get("allow_stitch", True),
            account_open_id=data.get("account_open_id", ""),
        )
