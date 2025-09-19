from django.core.management.base import BaseCommand
from users.models import UserRole, Permission, RolePermission, CustomUser

class Command(BaseCommand):
    help = 'Update roles to new 3-role system'

    def handle(self, *args, **options):
        self.stdout.write('Updating to 3-role system...')

        # Delete old roles
        UserRole.objects.all().delete()
        Permission.objects.all().delete()
        RolePermission.objects.all().delete()

        # Create new roles
        owner_role = UserRole.objects.create(
            name='farm_owner',
            display_name='Farm Owner/Admin',
            description='Full access to all platform features including financial management, user management, and all farm operations.',
            is_active=True
        )

        manager_role = UserRole.objects.create(
            name='farm_manager',
            display_name='Farm Manager',
            description='Read-only access to pig management (rooms, sows, piglets, insemination). Can view but cannot edit or delete.',
            is_active=True
        )

        worker_role = UserRole.objects.create(
            name='farm_worker',
            display_name='Farm Worker',
            description='Access to feeding and health management only. Can manage feeding records and health data.',
            is_active=True
        )

        # Create permissions for farm owner (full access)
        permissions = [
            # Farm management
            ('farm', 'view', 'View farm data'),
            ('farm', 'add', 'Add farm data'),
            ('farm', 'change', 'Edit farm data'),
            ('farm', 'delete', 'Delete farm data'),

            # Financial management
            ('financial', 'view', 'View financial data'),
            ('financial', 'add', 'Add financial records'),
            ('financial', 'change', 'Edit financial records'),
            ('financial', 'delete', 'Delete financial records'),

            # User management
            ('users', 'view', 'View users'),
            ('users', 'add', 'Add users'),
            ('users', 'change', 'Edit users'),
            ('users', 'delete', 'Delete users'),

            # Reports
            ('reports', 'view', 'View reports'),
            ('reports', 'generate', 'Generate reports'),

            # Feeding management
            ('feeding', 'view', 'View feeding data'),
            ('feeding', 'add', 'Add feeding records'),
            ('feeding', 'change', 'Edit feeding records'),
            ('feeding', 'delete', 'Delete feeding records'),

            # Health management
            ('health', 'view', 'View health data'),
            ('health', 'add', 'Add health records'),
            ('health', 'change', 'Edit health records'),
            ('health', 'delete', 'Delete health records'),
        ]

        # Create all permissions
        permission_objects = []
        for module, perm_type, description in permissions:
            permission = Permission.objects.create(
                name=f'{module}.{perm_type}',
                module=module,
                permission_type=perm_type,
                codename=f'{module}.{perm_type}',
                description=description
            )
            permission_objects.append(permission)

        # Assign all permissions to farm owner
        for permission in permission_objects:
            RolePermission.objects.create(
                role=owner_role,
                permission=permission
            )

        # Assign limited permissions to farm manager (only view for farm)
        farm_view_permissions = [p for p in permission_objects if p.module == 'farm' and p.permission_type == 'view']
        for permission in farm_view_permissions:
            RolePermission.objects.create(
                role=manager_role,
                permission=permission
            )

        # Assign feeding and health permissions to farm worker
        worker_permissions = [p for p in permission_objects if p.module in ['feeding', 'health']]
        for permission in worker_permissions:
            RolePermission.objects.create(
                role=worker_role,
                permission=permission
            )

        # Update existing users
        # Set all existing users to farm_owner temporarily (admin can reassign later)
        CustomUser.objects.all().update(role=owner_role)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated to 3-role system:\n'
                f'- {owner_role.display_name}: {owner_role.permissions.count()} permissions\n'
                f'- {manager_role.display_name}: {manager_role.permissions.count()} permissions\n'
                f'- {worker_role.display_name}: {worker_role.permissions.count()} permissions\n'
                f'All existing users have been assigned to Farm Owner role.'
            )
        )