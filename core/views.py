import os
import time
import base64
import hashlib
import urllib.parse
import requests
from datetime import datetime
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage
import uuid

from tiktok_scheduler import config
from tiktok_scheduler.models import Token, Post
from tiktok_scheduler.storage import Storage
from .tasks import upload_post_task

def index(request):
    """Simple Landing Page to Login."""
    return render(request, 'core/index.html')

def dashboard(request):
    """The new Scheduler Dashboard."""
    posts = Storage.load_schedule()
    return render(request, 'core/dashboard.html', {'posts': posts})

def login(request):
    """Generates TikTok Auth URL and redirects the user."""
    # Generate PKCE verifier and challenge.
    # NOTE: TikTok is non-standard — it requires the HEX encoding of SHA256
    # (not the usual base64url). code_challenge_method stays "S256".
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).hexdigest()
    
    # We store code_verifier in session for the callback
    request.session['code_verifier'] = code_verifier
    
    base_url = "https://www.tiktok.com/v2/auth/authorize/"
    scopes = ["user.info.basic", "video.upload", "video.publish"]
    params = {
        "client_key": config.TIKTOK_CLIENT_ID,
        "response_type": "code",
        "scope": ",".join(scopes),
        "redirect_uri": config.REDIRECT_URI,
        "state": "tiktok_scheduler_django",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    auth_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

def callback(request):
    """Handles the TikTok callback from Ngrok, exchanges code for tokens."""
    auth_code = request.GET.get('code')
    if not auth_code:
        return HttpResponse("Authentication failed! No code found.", status=400)
        
    code_verifier = request.session.get('code_verifier')
    if not code_verifier:
        return HttpResponse("Session expired or missing code_verifier.", status=400)
        
    url = "https://open.tiktokapis.com/v2/oauth/token/"
    data = {
        "client_key": config.TIKTOK_CLIENT_ID,
        "client_secret": config.TIKTOK_CLIENT_SECRET,
        "code": auth_code,
        "grant_type": "authorization_code",
        "redirect_uri": config.REDIRECT_URI,
        "code_verifier": code_verifier
    }
    
    try:
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
            return render(request, 'core/success.html')
        else:
            return HttpResponse(f"Failed to fetch tokens: {resp_data}", status=400)
    except Exception as e:
        return HttpResponse(f"Error exchanging tokens: {str(e)}", status=500)

@csrf_exempt
def schedule_post(request):
    """Schedules a new post via Celery ETA."""
    if request.method == 'POST':
        media_file = request.FILES.get('media_file')
        caption = request.POST.get('caption')
        schedule_time_str = request.POST.get('schedule')  # e.g. "2026-07-11T09:00"
        
        if not all([media_file, schedule_time_str]):
            return JsonResponse({'error': 'Missing required fields (file or schedule time)'}, status=400)
            
        fs = FileSystemStorage()
        filename = fs.save(media_file.name, media_file)
        media_absolute_path = fs.path(filename)
            
        try:
            run_date = datetime.fromisoformat(schedule_time_str)
            run_date = timezone.make_aware(run_date)
        except ValueError:
            return JsonResponse({'error': 'Invalid schedule format. Use ISO format.'}, status=400)
            
        post = Post(
            id=str(uuid.uuid4()),
            media=media_absolute_path,
            caption=caption,
            schedule=schedule_time_str
        )
        
        # Save to JSON database
        posts = Storage.load_schedule()
        posts.append(post)
        Storage.save_schedule(posts)
        
        # Schedule the Celery task (using ETA)
        upload_post_task.apply_async((post.id,), eta=run_date)
        
        return redirect('dashboard')
        
    return HttpResponse("Method not allowed", status=405)
