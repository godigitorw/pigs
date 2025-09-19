from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # User Management
    path('', views.user_management, name='user_management'),
    path('create/', views.create_user, name='create_user'),
    path('edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('delete/<int:user_id>/', views.delete_user, name='delete_user'),

    # Role & Permissions
    path('roles/', views.role_permissions, name='role_permissions'),

    # User Profile
    path('profile/', views.profile, name='profile'),

    # Activity & Sessions
    path('activities/', views.activity_logs, name='activity_logs'),
    path('sessions/', views.user_sessions, name='user_sessions'),
    path('sessions/revoke/<int:session_id>/', views.revoke_session, name='revoke_session'),

    # AJAX endpoints
    path('ajax/check-username/', views.ajax_check_username, name='ajax_check_username'),
    path('ajax/check-email/', views.ajax_check_email, name='ajax_check_email'),
]