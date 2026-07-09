from django.http import JsonResponse

def create_post(request):
    return JsonResponse({"message": "Create post endpoint"})

def schedule_post(request):
    return JsonResponse({"message": "Schedule post endpoint"})

def list_posts(request):
    return JsonResponse({"message": "List posts endpoint"})

def cancel_post(request, post_id):
    return JsonResponse({"message": f"Cancel post {post_id} endpoint"})
