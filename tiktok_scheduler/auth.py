import logging
import urllib.parse
import webbrowser
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from . import config
from .storage import Storage
from .models import Token

logger = logging.getLogger(__name__)

# Temporary variable to store auth code during HTTP callback
_auth_code = None

class AuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        query_components = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        if 'code' in query_components:
            _auth_code = query_components['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authentication successful!</h1><p>You can close this window now and return to the terminal.</p></body></html>")
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authentication failed!</h1><p>No code parameter found.</p></body></html>")
            
    def log_message(self, format, *args):
        # Suppress standard HTTP server logging
        pass

def authenticate():
    """
    Runs a local HTTP server, opens the browser to authenticate, 
    and saves the resulting tokens.
    """
    global _auth_code
    _auth_code = None
    
    import base64
    import hashlib
    import os
    
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).decode('utf-8').rstrip('=')
    
    # Start local server to listen for the callback
    # Assuming redirect URI is http://localhost:8080/callback
    parsed_uri = urllib.parse.urlparse(config.REDIRECT_URI)
    port = parsed_uri.port or 8080
    server_address = ('', port)
    httpd = HTTPServer(server_address, AuthCallbackHandler)
    
    # Generate auth URL
    base_url = "https://www.tiktok.com/v2/auth/authorize/"
    scopes = ["user.info.basic", "video.upload", "video.publish"]
    params = {
        "client_key": config.TIKTOK_CLIENT_ID,
        "response_type": "code",
        "scope": ",".join(scopes),
        "redirect_uri": config.REDIRECT_URI,
        "state": "tiktok_scheduler_local",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    print("=" * 60)
    print("Opening browser for TikTok authentication...")
    print(f"If the browser doesn't open, visit: \n{auth_url}")
    print("=" * 60)
    
    webbrowser.open(auth_url)
    
    print(f"Listening on port {port} for callback. Waiting for authentication...")
    
    # Handle exactly one request but allow Ctrl+C to work
    httpd.timeout = 1
    try:
        while _auth_code is None:
            httpd.handle_request()
    except KeyboardInterrupt:
        print("\nAuthentication cancelled by user.")
        return
        
    print("Received auth code! Exchanging for tokens...")
    
    # Exchange code for tokens
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    data = {
        "client_key": config.TIKTOK_CLIENT_ID,
        "client_secret": config.TIKTOK_CLIENT_SECRET,
        "code": _auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": config.REDIRECT_URI,
        "code_verifier": code_verifier
    }
    
    response = requests.post(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    response.raise_for_status()
    
    resp_data = response.json()
    token_data = resp_data.get("data", resp_data)
    
    if "access_token" in token_data:
        token = Token(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", ""),
            expires_at=time.time() + token_data.get("expires_in", 86400)
        )
        Storage.save_tokens(token)
        print("Tokens successfully saved to tokens.json! You are ready to schedule posts.")
    else:
        logger.error(f"Failed to fetch tokens: {resp_data}")
        raise Exception("Failed to fetch tokens from TikTok.")
