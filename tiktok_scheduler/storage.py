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

    # ---- Multi-account registry ----
    # tokens.json / profile.json hold the ACTIVE account (used by the API layer).
    # accounts.json is a registry of every connected account, keyed by open_id.
    @staticmethod
    def _load_registry() -> dict:
        if not os.path.exists(config.ACCOUNTS_FILE):
            return {}
        try:
            with open(config.ACCOUNTS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def _save_registry(reg: dict):
        with open(config.ACCOUNTS_FILE, 'w') as f:
            json.dump(reg, f, indent=4)

    @staticmethod
    def add_account(token: Token, profile: Profile):
        """Add or update a connected account in the registry."""
        if not profile or not profile.open_id:
            return
        reg = Storage._load_registry()
        reg[profile.open_id] = {"token": token.to_dict(), "profile": profile.to_dict()}
        Storage._save_registry(reg)

    @staticmethod
    def list_accounts() -> List[Profile]:
        reg = Storage._load_registry()
        return [Profile.from_dict(v.get("profile", {})) for v in reg.values()]

    @staticmethod
    def get_account_token(open_id: str) -> Optional[Token]:
        reg = Storage._load_registry()
        entry = reg.get(open_id)
        if entry:
            return Token.from_dict(entry["token"])
        return None

    @staticmethod
    def switch_account(open_id: str) -> bool:
        """Make a registered account the active one."""
        reg = Storage._load_registry()
        entry = reg.get(open_id)
        if not entry:
            return False
        Storage.save_tokens(Token.from_dict(entry["token"]))
        Storage.save_profile(Profile.from_dict(entry["profile"]))
        return True

    @staticmethod
    def remove_account(open_id: str) -> bool:
        reg = Storage._load_registry()
        if open_id in reg:
            del reg[open_id]
            Storage._save_registry(reg)
        # If the removed account was active, switch to another (or clear).
        active = Storage.load_profile()
        if active and active.open_id == open_id:
            if reg:
                first = next(iter(reg.values()))
                Storage.save_tokens(Token.from_dict(first["token"]))
                Storage.save_profile(Profile.from_dict(first["profile"]))
            else:
                Storage.clear_tokens()
                Storage.clear_profile()
        return True

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
