from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_post, name='create_post'),
    path('schedule/', views.schedule_post, name='schedule_post'),
    path('list/', views.list_posts, name='list_posts'),
    path('cancel/<int:post_id>/', views.cancel_post, name='cancel_post'),
]
