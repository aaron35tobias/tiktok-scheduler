import json
import os
from typing import List, Optional
from .models import Token, Post
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
