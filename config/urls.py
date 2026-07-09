from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import accounts.views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', accounts.views.home, name='home'),
    path('', include('accounts.urls')),
    path('posts/', include('tiktok.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
