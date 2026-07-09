from django.urls import path
from . import views

urlpatterns = [
    path('login', views.login, name='tiktok_login'),
    path('callback', views.callback, name='tiktok_callback'),
    path('account', views.account, name='tiktok_account'),
]
