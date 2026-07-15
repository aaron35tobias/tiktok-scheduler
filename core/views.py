import os
import time
import base64
import hashlib
import urllib.parse
import calendar as pycal
import logging
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import FileSystemStorage

from tiktok_scheduler import config
from tiktok_scheduler.models import Token, Post, Profile
from tiktok_scheduler.storage import Storage
from tiktok_scheduler.api import api_client
from .tasks import upload_post_task

logger = logging.getLogger(__name__)

# Common timezones offered in the Settings dropdown.
COMMON_TIMEZONES = [
    "UTC",
    "Asia/Dubai", "Asia/Kolkata", "Asia/Karachi", "Asia/Riyadh",
    "Asia/Singapore", "Asia/Tokyo", "Asia/Shanghai",
    "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Istanbul",
    "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
    "America/Sao_Paulo", "Australia/Sydney", "Pacific/Auckland",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _fetch_and_save_profile():
    """Fetch the connected account's profile from TikTok and cache it."""
    try:
        user = api_client.get_user_info()
        profile = Profile(
            open_id=user.get("open_id", ""),
            avatar_url=user.get("avatar_url", ""),
            display_name=user.get("display_name", ""),
            username=user.get("username", ""),
            follower_count=user.get("follower_count"),
            following_count=user.get("following_count"),
            likes_count=user.get("likes_count"),
            video_count=user.get("video_count"),
            is_verified=user.get("is_verified", False),
        )
        Storage.save_profile(profile)
        return profile
    except Exception as e:
        logger.warning(f"Could not fetch TikTok profile: {e}")
        return None


def _build_stats(posts):
    today = datetime.now().date()
    published_today = 0
    pending = 0
    failed = 0
    for p in posts:
        if p.status == "Failed":
            failed += 1
        elif p.status in ("Pending", "Uploading"):
            pending += 1
        if p.status == "Published":
            dt = p.schedule_dt
            if dt and dt.date() == today:
                published_today += 1
    return {
        "scheduled": len(posts),
        "published_today": published_today,
        "pending": pending,
        "failed": failed,
    }


def _build_calendar(posts):
    today = datetime.now()
    year, month = today.year, today.month
    day_posts = {}
    for p in posts:
        dt = p.schedule_dt
        if dt and dt.year == year and dt.month == month:
            day_posts.setdefault(dt.day, []).append(p)

    cal = pycal.Calendar(firstweekday=0)  # Monday first
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        row = []
        for d in week:
            in_month = d.month == month
            row.append({
                "day": d.day,
                "in_month": in_month,
                "is_today": d == today.date(),
                "posts": day_posts.get(d.day, []) if in_month else [],
            })
        weeks.append(row)
    return {
        "month_name": today.strftime("%B %Y"),
        "weekday_names": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "weeks": weeks,
    }


def _build_notifications(posts, token):
    notes = []
    if not token:
        notes.append({"type": "error", "message": "TikTok account disconnected."})
    else:
        if token.expires_at:
            days = int((token.expires_at - time.time()) / 86400)
            if days <= 5:
                notes.append({"type": "warning", "message": f"OAuth token expires in {max(days, 0)} day(s)."})
    for p in posts:
        if p.status == "Failed":
            notes.append({"type": "error", "message": f"Upload failed: {p.caption or p.media_filename}"})
        elif p.status == "Published":
            notes.append({"type": "success", "message": f"Video published successfully: {p.caption or p.media_filename}"})
    return notes[:6]


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
def index(request):
    """Simple Landing Page to Login."""
    return render(request, 'core/index.html')


def dashboard(request):
    """The full Scheduler Dashboard."""
    all_posts = Storage.load_schedule()
    token = Storage.load_tokens()
    profile = Storage.load_profile()
    active_oid = profile.open_id if profile else ""

    # Keep the active account present in the registry (so it always lists).
    if token and profile and profile.open_id:
        Storage.add_account(token, profile)

    # Scope posts to the active account (each post is tagged with its owner
    # when scheduled). Posts with no owner aren't shown under any account.
    if active_oid:
        posts = [p for p in all_posts if p.account_open_id == active_oid]
    else:
        posts = all_posts

    last_connected = "Never"
    if token and os.path.exists(config.TOKENS_FILE):
        last_connected = datetime.fromtimestamp(
            os.path.getmtime(config.TOKENS_FILE)
        ).strftime("%d %b %Y, %I:%M %p")

    # Recent activity: reformat the stored time to 12-hour AM/PM.
    activity = Storage.load_activity()
    for a in activity:
        try:
            a["time"] = datetime.strptime(a.get("time", ""), "%Y-%m-%d %H:%M").strftime("%d %b %Y, %I:%M %p")
        except Exception:
            pass

    context = {
        'posts': posts,
        'profile': profile,
        'connected': bool(token and token.access_token),
        'last_connected': last_connected,
        'accounts': Storage.list_accounts(),
        'active_open_id': profile.open_id if profile else '',
        'stats': _build_stats(posts),
        'calendar': _build_calendar(posts),
        'activity': activity,
        'notifications': _build_notifications(posts, token),
        'settings': Storage.load_settings(),
    }
    # Timezone dropdown options (ensure the saved one is always present).
    tz_list = list(COMMON_TIMEZONES)
    current_tz = context['settings'].get('timezone')
    if current_tz and current_tz not in tz_list:
        tz_list.insert(0, current_tz)
    context['timezones'] = tz_list
    return render(request, 'core/dashboard.html', context)


def login(request):
    """Generates TikTok Auth URL and redirects the user."""
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    # NOTE: TikTok requires the HEX encoding of SHA256 (not base64url). Method stays S256.
    code_challenge = hashlib.sha256(code_verifier.encode('utf-8')).hexdigest()

    request.session['code_verifier'] = code_verifier

    base_url = "https://www.tiktok.com/v2/auth/authorize/"
    # Extra scopes let us fetch follower/following/video counts and username.
    scopes = ["user.info.basic", "user.info.profile", "user.info.stats",
              "video.upload", "video.publish"]
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
    """Handles the TikTok callback, exchanges code for tokens, fetches profile."""
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
            prof = _fetch_and_save_profile()
            if prof:
                Storage.add_account(token, prof)   # register for multi-account
            Storage.add_activity("🔗", "Connected TikTok account")
            return redirect('dashboard')
        else:
            return HttpResponse(f"Failed to fetch tokens: {resp_data}", status=400)
    except Exception as e:
        return HttpResponse(f"Error exchanging tokens: {str(e)}", status=500)


@csrf_exempt
def schedule_post(request):
    """Schedules a new post via Celery ETA."""
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    media_file = request.FILES.get('media_file')
    caption = request.POST.get('caption', '')
    hashtags = request.POST.get('hashtags', '')
    privacy = request.POST.get('privacy', 'SELF_ONLY')
    schedule_time_str = request.POST.get('schedule')
    allow_comments = request.POST.get('allow_comments') == 'on'
    allow_duet = request.POST.get('allow_duet') == 'on'
    allow_stitch = request.POST.get('allow_stitch') == 'on'

    if not all([media_file, schedule_time_str]):
        return JsonResponse({'error': 'Missing required fields (file or schedule time)'}, status=400)

    fs = FileSystemStorage()
    filename = fs.save(media_file.name, media_file)
    media_absolute_path = fs.path(filename)

    # Interpret the entered time in the user's chosen timezone (Settings).
    tz_name = Storage.load_settings().get('timezone') or 'Asia/Dubai'
    try:
        tzinfo = ZoneInfo(tz_name)
    except Exception:
        tzinfo = ZoneInfo('Asia/Dubai')
    try:
        run_date = datetime.fromisoformat(schedule_time_str).replace(tzinfo=tzinfo)
    except ValueError:
        return JsonResponse({'error': 'Invalid schedule format. Use ISO format.'}, status=400)

    active_profile = Storage.load_profile()
    owner_open_id = active_profile.open_id if active_profile else ""

    post = Post(
        id=str(uuid.uuid4()),
        media=media_absolute_path,
        caption=caption,
        schedule=schedule_time_str,
        hashtags=hashtags,
        privacy=privacy,
        allow_comments=allow_comments,
        allow_duet=allow_duet,
        allow_stitch=allow_stitch,
        account_open_id=owner_open_id,
    )

    posts = Storage.load_schedule()
    posts.append(post)
    Storage.save_schedule(posts)

    upload_post_task.apply_async((post.id,), eta=run_date)
    Storage.add_activity("📅", f"Scheduled post: {caption or media_file.name}")

    return redirect('dashboard')


def delete_post(request, post_id):
    if request.method == 'POST':
        deleted = Storage.delete_post(post_id)
        if deleted:
            Storage.add_activity("🗑️", "Deleted a scheduled post")
    return redirect('dashboard')


def refresh_account(request):
    profile = _fetch_and_save_profile()
    if profile:
        Storage.add_activity("🔄", "Refreshed account info")
    return redirect('dashboard')


def switch_account(request):
    if request.method == 'POST':
        open_id = request.POST.get('open_id')
        if open_id and Storage.switch_account(open_id):
            Storage.add_activity("🔀", "Switched active account")
    return redirect('dashboard')


def remove_account(request):
    if request.method == 'POST':
        open_id = request.POST.get('open_id')
        if open_id:
            Storage.remove_account(open_id)
            Storage.add_activity("🗑️", "Removed a connected account")
    return redirect('dashboard')


def disconnect(request):
    Storage.clear_tokens()
    Storage.clear_profile()
    Storage.add_activity("🔌", "Disconnected TikTok account")
    return redirect('index')


def save_settings(request):
    if request.method == 'POST':
        Storage.save_settings({
            "timezone": request.POST.get('timezone', 'UTC'),
            "auto_refresh": request.POST.get('auto_refresh') == 'on',
            "default_privacy": request.POST.get('default_privacy', 'SELF_ONLY'),
            "default_hashtags": request.POST.get('default_hashtags', ''),
            "notification_email": request.POST.get('notification_email', ''),
        })
        Storage.add_activity("⚙️", "Updated settings")
    return redirect('dashboard')
