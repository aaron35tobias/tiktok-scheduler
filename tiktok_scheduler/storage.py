import json
import os
from datetime import datetime
from typing import List, Optional
from .models import Token, Post, Profile
from . import config

class Storage:
    @staticmethod
    def save_tokens(token: Token):
        with open(config.TOKENS_FILE, 'w') as f:
            json.dump(token.to_dict(), f, indent=4)
            
    @staticmethod
    def load_tokens() -> Optional[Token]:
        if not os.path.exists(config.TOKENS_FILE):
            return None
        try:
            with open(config.TOKENS_FILE, 'r') as f:
                data = json.load(f)
                if data and "access_token" in data:
                    return Token.from_dict(data)
        except json.JSONDecodeError:
            pass
        return None

    @staticmethod
    def load_schedule() -> List[Post]:
        if not os.path.exists(config.SCHEDULE_FILE):
            # Create an empty template
            with open(config.SCHEDULE_FILE, 'w') as f:
                json.dump([], f)
            return []
            
        try:
            with open(config.SCHEDULE_FILE, 'r') as f:
                data = json.load(f)
                return [Post.from_dict(item) for item in data]
        except Exception:
            return []

    @staticmethod
    def save_schedule(posts: List[Post]):
        with open(config.SCHEDULE_FILE, 'w') as f:
            json.dump([p.to_dict() for p in posts], f, indent=4)

    @staticmethod
    def delete_post(post_id: str) -> bool:
        posts = Storage.load_schedule()
        new_posts = [p for p in posts if p.id != post_id]
        if len(new_posts) == len(posts):
            return False
        Storage.save_schedule(new_posts)
        return True

    # ---- Profile ----
    @staticmethod
    def save_profile(profile: Profile):
        with open(config.PROFILE_FILE, 'w') as f:
            json.dump(profile.to_dict(), f, indent=4)

    @staticmethod
    def load_profile() -> Optional[Profile]:
        if not os.path.exists(config.PROFILE_FILE):
            return None
        try:
            with open(config.PROFILE_FILE, 'r') as f:
                data = json.load(f)
                if data:
                    return Profile.from_dict(data)
        except Exception:
            pass
        return None

    @staticmethod
    def clear_profile():
        if os.path.exists(config.PROFILE_FILE):
            os.remove(config.PROFILE_FILE)

    @staticmethod
    def clear_tokens():
        if os.path.exists(config.TOKENS_FILE):
            os.remove(config.TOKENS_FILE)

    # ---- Activity log ----
    @staticmethod
    def add_activity(icon: str, message: str):
        activity = Storage.load_activity()
        activity.insert(0, {
            "icon": icon,
            "message": message,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
        activity = activity[:20]  # keep the most recent 20
        with open(config.ACTIVITY_FILE, 'w') as f:
            json.dump(activity, f, indent=4)

    @staticmethod
    def load_activity() -> List[dict]:
        if not os.path.exists(config.ACTIVITY_FILE):
            return []
        try:
            with open(config.ACTIVITY_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []

    # ---- Settings ----
    DEFAULT_SETTINGS = {
        "timezone": "Asia/Dubai",
        "auto_refresh": True,
        "default_privacy": "SELF_ONLY",
        "default_hashtags": "",
        "notification_email": "",
    }

    @staticmethod
    def load_settings() -> dict:
        settings = dict(Storage.DEFAULT_SETTINGS)
        if os.path.exists(config.SETTINGS_FILE):
            try:
                with open(config.SETTINGS_FILE, 'r') as f:
                    settings.update(json.load(f))
            except Exception:
                pass
        return settings

    @staticmethod
    def save_settings(new_settings: dict):
        settings = Storage.load_settings()
        settings.update(new_settings)
        with open(config.SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=4)
