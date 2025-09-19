from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserRole, Permission, RolePermission, UserActivity, UserSession

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_active_employee', 'date_joined')
    list_filter = ('role', 'is_active', 'is_active_employee', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'employee_id')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Farm Profile', {
            'fields': ('role', 'employee_id', 'phone_number', 'department', 'hire_date',
                      'is_active_employee', 'profile_picture', 'address', 'emergency_contact',
                      'emergency_phone', 'created_by', 'last_login_ip')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Farm Profile', {
            'fields': ('role', 'employee_id', 'phone_number', 'department', 'hire_date')
        }),
    )

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'display_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'display_name')

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'module', 'permission_type')
    list_filter = ('module', 'permission_type')
    search_fields = ('name', 'codename')

@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission', 'granted_at')
    list_filter = ('role', 'permission__module', 'granted_at')

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'module', 'object_repr', 'ip_address', 'timestamp')
    list_filter = ('action', 'module', 'timestamp')
    search_fields = ('user__username', 'object_repr', 'ip_address')
    readonly_fields = ('user', 'action', 'module', 'object_id', 'object_repr', 'ip_address', 'timestamp', 'additional_data')

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'login_time', 'last_activity', 'is_active')
    list_filter = ('is_active', 'login_time', 'last_activity')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('user', 'session_key', 'ip_address', 'user_agent', 'login_time', 'last_activity')
