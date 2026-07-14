from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('callback/', views.callback, name='callback'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('schedule/', views.schedule_post, name='schedule_post'),
    path('delete/<str:post_id>/', views.delete_post, name='delete_post'),
    path('refresh-account/', views.refresh_account, name='refresh_account'),
    path('disconnect/', views.disconnect, name='disconnect'),
    path('settings/', views.save_settings, name='save_settings'),
]
