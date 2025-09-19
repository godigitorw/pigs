from django import template
from django.contrib.auth import get_user_model

register = template.Library()
User = get_user_model()

@register.filter
def has_role(user, role_name):
    """
    Check if user has a specific role
    Usage: {% if user|has_role:'farm_owner' %}
    """
    if not user or not user.role:
        return False
    return user.role.name == role_name

@register.filter
def has_any_role(user, role_names):
    """
    Check if user has any of the specified roles
    Usage: {% if user|has_any_role:'farm_owner,farm_manager' %}
    """
    if not user or not user.role:
        return False
    role_list = role_names.split(',')
    return user.role.name in role_list

@register.filter
def has_module_access(user, module_name):
    """
    Check if user has access to a module
    Usage: {% if user|has_module_access:'reports' %}
    """
    if not user or not user.role:
        return False
    return user.role.permissions.filter(permission__module=module_name).exists()

@register.filter
def has_permission(user, permission_codename):
    """
    Check if user has a specific permission
    Usage: {% if user|has_permission:'farm.add' %}
    """
    if not user or not user.role:
        return False
    return user.role.permissions.filter(permission__codename=permission_codename).exists()

@register.simple_tag
def can_manage_users(user):
    """
    Check if user can manage other users
    Usage: {% can_manage_users user as can_manage %}
    """
    if not user or not user.role:
        return False
    return user.role.name in ['farm_owner', 'farm_manager']

@register.simple_tag
def can_view_financials(user):
    """
    Check if user can view financial data
    Usage: {% can_view_financials user as can_view %}
    """
    if not user or not user.role:
        return False
    return user.role.name in ['farm_owner', 'accountant']

@register.simple_tag
def can_manage_feeding(user):
    """
    Check if user can manage feeding
    Usage: {% can_manage_feeding user as can_manage %}
    """
    if not user or not user.role:
        return False
    return user.role.name in ['farm_owner', 'farm_manager', 'feed_manager']