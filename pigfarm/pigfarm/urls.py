# pigfarm/urls.py
# pigfarm/urls.py
from django.contrib import admin
from django.urls import path, include  # Remove 'redirect' from here
from .views import *
from django.shortcuts import redirect  # Keep only this redirect import
from django.contrib.auth.views import LogoutView

# pigfarm/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('farm/', include('farm.urls')),
    path('', dashboard_view, name='dashboard'),
    path('health/', include('health.urls')),
    path('login/', login_view, name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

]