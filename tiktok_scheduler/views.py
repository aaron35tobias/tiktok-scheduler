import logging
from django.http import HttpResponse, JsonResponse
from api.auth import get_auth_url, fetch_tokens

logger = logging.getLogger(__name__)

def home(request):
    auth_url = get_auth_url()
    html = f'''
    <h1>TikTok Scheduler PoC (Django)</h1>
    <p>Click below to log in and authorize the application:</p>
    <a href="{auth_url}">Login with TikTok</a>
    '''
    return HttpResponse(html)

def callback(request):
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        return HttpResponse(f"Error during authorization: {error}", status=400)
        
    if not code:
        return HttpResponse("No authorization code provided.", status=400)
        
    try:
        fetch_tokens(code)
        return JsonResponse({
            "message": "Successfully authenticated with TikTok!",
            "note": "Tokens have been saved to the Django database. You can now use the management commands to schedule posts."
        })
    except Exception as e:
        logger.error(f"Callback error: {str(e)}")
        return HttpResponse(f"Failed to fetch tokens: {str(e)}", status=500)
