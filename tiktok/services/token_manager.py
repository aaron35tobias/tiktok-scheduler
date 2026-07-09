from scheduler.models import TikTokToken

def get_tokens():
    token = TikTokToken.objects.first()
    if token:
        return {
            "access_token": token.access_token,
            "refresh_token": token.refresh_token,
            "expires_in": token.expires_in
        }
    return {}

def save_tokens(access_token, refresh_token, expires_in=None):
    token = TikTokToken.objects.first()
    if token:
        token.access_token = access_token
        token.refresh_token = refresh_token
        if expires_in is not None:
            token.expires_in = expires_in
        token.save()
    else:
        TikTokToken.objects.create(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )

def update_tokens(access_token, refresh_token):
    save_tokens(access_token, refresh_token)
