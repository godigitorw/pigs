# pigfarm/urls.py
from django.contrib import admin
from django.urls import path, include
from .views import *
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('farm/', include('farm.urls')),
    path('', dashboard_view, name='dashboard'),
    path('health/', include('health.urls')),
    path('reports/', include('reports.urls')),
    path('users/', include('users.urls')),
    path('login/', login_view, name='login'),
    path('logout/', custom_logout, name='logout'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)