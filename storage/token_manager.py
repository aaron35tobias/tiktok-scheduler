from tiktok_scheduler.models import TikTokToken

def save_tokens(access_token: str, refresh_token: str, expires_in: int = None):
    """Save tokens securely in the database."""
    # We only keep one token record for the PoC
    TikTokToken.objects.all().delete()
    TikTokToken.objects.create(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in
    )

def get_tokens():
    """Retrieve tokens from the database."""
    token = TikTokToken.objects.first()
    if token:
        return {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_in": token.expires_in
        }
    
    # Fallback to env for poc
    from config import config
    return {
        "access_token": config.ACCESS_TOKEN,
        "refresh_token": config.REFRESH_TOKEN,
        "expires_in": None
    }

def update_tokens(access_token: str, refresh_token: str):
    token = TikTokToken.objects.first()
    if token:
        token.access_token = access_token
        token.refresh_token = refresh_token
        token.save()
    else:
        save_tokens(access_token, refresh_token)
