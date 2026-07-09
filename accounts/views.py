from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponse
import os
import logging
from tiktok.services.authentication import get_auth_url, fetch_tokens

logger = logging.getLogger(__name__)

def home(request):
    auth_url = get_auth_url()
    return HttpResponse(f'''
    <h1>TikTok Scheduler PoC</h1>
    <p>Click below to log in and authorize the application:</p>
    <a href="{auth_url}">Login with TikTok</a>
    ''')

def login(request):
    auth_url = get_auth_url()
    return redirect(auth_url)

def callback(request):
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        return JsonResponse({"error": f"Error during authorization: {error}"}, status=400)
        
    if not code:
        return JsonResponse({"error": "No authorization code provided."}, status=400)
        
    try:
        token_data = fetch_tokens(code)
        return JsonResponse({
            "message": "Successfully authenticated with TikTok!",
            "note": "Tokens have been saved. You can now use the CLI to schedule posts."
        })
    except Exception as e:
        logger.error(f"Failed to fetch tokens: {str(e)}")
        return JsonResponse({"error": f"Failed to fetch tokens: {str(e)}"}, status=500)

def account(request):
    # Dummy endpoint for now
    return JsonResponse({"message": "Account info endpoint"})
