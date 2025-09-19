from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class UserRole(models.Model):
    ROLE_CHOICES = [
        ('farm_owner', 'Farm Owner/Admin'),
        ('farm_manager', 'Farm Manager'),
        ('feed_manager', 'Feed Manager'),
        ('accountant', 'Accountant/Finance'),
        ('viewer', 'Viewer/Inspector'),
    ]

    name = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    display_name = models.CharField(max_length=50)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.display_name

class Permission(models.Model):
    PERMISSION_TYPES = [
        ('view', 'View'),
        ('add', 'Add'),
        ('change', 'Change'),
        ('delete', 'Delete'),
        ('export', 'Export'),
        ('manage', 'Manage'),
    ]

    MODULE_CHOICES = [
        ('dashboard', 'Dashboard'),
        ('farm', 'Farm Management'),
        ('feeding', 'Feeding Management'),
        ('health', 'Health Management'),
        ('breeding', 'Breeding Management'),
        ('reports', 'Reports'),
        ('users', 'User Management'),
        ('financial', 'Financial Records'),
    ]

    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=50, unique=True)
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    permission_type = models.CharField(max_length=10, choices=PERMISSION_TYPES)
    description = models.TextField()

    def __str__(self):
        return f"{self.module}.{self.permission_type}"

class RolePermission(models.Model):
    role = models.ForeignKey(UserRole, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"

class CustomUser(AbstractUser):
    role = models.ForeignKey(UserRole, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    employee_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    department = models.CharField(max_length=50, blank=True, null=True)
    hire_date = models.DateField(blank=True, null=True)
    is_active_employee = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    emergency_contact = models.CharField(max_length=100, blank=True, null=True)
    emergency_phone = models.CharField(max_length=15, blank=True, null=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_full_name() or self.username})"

    def has_permission(self, permission_codename):
        """Check if user has specific permission"""
        if not self.role:
            return False
        return self.role.permissions.filter(permission__codename=permission_codename).exists()

    def has_module_access(self, module_name):
        """Check if user has any access to a module"""
        if not self.role:
            return False
        return self.role.permissions.filter(permission__module=module_name).exists()

    def get_role_display(self):
        return self.role.display_name if self.role else "No Role Assigned"

class UserSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.login_time.strftime('%Y-%m-%d %H:%M')}"

class UserActivity(models.Model):
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('view', 'View'),
        ('export', 'Export'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50, blank=True, null=True)
    object_repr = models.CharField(max_length=200, blank=True, null=True)
    ip_address = models.GenericIPAddressField()
    timestamp = models.DateTimeField(auto_now_add=True)
    additional_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.module} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        ordering = ['-timestamp']
