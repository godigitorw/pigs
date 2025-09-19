from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserRole, Permission, RolePermission

User = get_user_model()

class Command(BaseCommand):
    help = 'Setup initial user roles and permissions for the pig farm system'

    def handle(self, *args, **options):
        self.stdout.write('Setting up user roles and permissions...')

        # Create roles
        roles_data = [
            {
                'name': 'farm_owner',
                'display_name': 'Farm Owner/Admin',
                'description': 'Full access to all farm operations and system administration'
            },
            {
                'name': 'farm_manager',
                'display_name': 'Farm Manager',
                'description': 'Manage daily operations, view reports, manage staff'
            },
            {
                'name': 'feed_manager',
                'display_name': 'Feed Manager',
                'description': 'Feeding schedules, stock management, feeding records'
            },
            {
                'name': 'accountant',
                'display_name': 'Accountant/Finance',
                'description': 'Financial records, sales, expenses, reports'
            },
            {
                'name': 'viewer',
                'display_name': 'Viewer/Inspector',
                'description': 'Read-only access for inspectors, auditors'
            },
        ]

        for role_data in roles_data:
            role, created = UserRole.objects.get_or_create(
                name=role_data['name'],
                defaults=role_data
            )
            if created:
                self.stdout.write(f'Created role: {role.display_name}')
            else:
                self.stdout.write(f'Role already exists: {role.display_name}')

        # Create permissions
        permissions_data = [
            # Dashboard permissions
            {'name': 'View Dashboard', 'codename': 'dashboard.view', 'module': 'dashboard', 'permission_type': 'view', 'description': 'View main dashboard'},

            # Farm Management permissions
            {'name': 'View Farm', 'codename': 'farm.view', 'module': 'farm', 'permission_type': 'view', 'description': 'View farm animals and basic info'},
            {'name': 'Add Farm Animals', 'codename': 'farm.add', 'module': 'farm', 'permission_type': 'add', 'description': 'Add new sows and piglets'},
            {'name': 'Edit Farm Animals', 'codename': 'farm.change', 'module': 'farm', 'permission_type': 'change', 'description': 'Edit farm animal information'},
            {'name': 'Delete Farm Animals', 'codename': 'farm.delete', 'module': 'farm', 'permission_type': 'delete', 'description': 'Delete or deactivate farm animals'},
            {'name': 'Manage Farm', 'codename': 'farm.manage', 'module': 'farm', 'permission_type': 'manage', 'description': 'Full farm management access'},

            # Feeding Management permissions
            {'name': 'View Feeding', 'codename': 'feeding.view', 'module': 'feeding', 'permission_type': 'view', 'description': 'View feeding records and schedules'},
            {'name': 'Add Feeding Records', 'codename': 'feeding.add', 'module': 'feeding', 'permission_type': 'add', 'description': 'Add feeding records'},
            {'name': 'Edit Feeding Records', 'codename': 'feeding.change', 'module': 'feeding', 'permission_type': 'change', 'description': 'Edit feeding records'},
            {'name': 'Delete Feeding Records', 'codename': 'feeding.delete', 'module': 'feeding', 'permission_type': 'delete', 'description': 'Delete feeding records'},
            {'name': 'Manage Feed Stock', 'codename': 'feeding.manage', 'module': 'feeding', 'permission_type': 'manage', 'description': 'Manage feed inventory and stock'},

            # Health Management permissions
            {'name': 'View Health Records', 'codename': 'health.view', 'module': 'health', 'permission_type': 'view', 'description': 'View health and vaccination records'},
            {'name': 'Add Health Records', 'codename': 'health.add', 'module': 'health', 'permission_type': 'add', 'description': 'Add health and vaccination records'},
            {'name': 'Edit Health Records', 'codename': 'health.change', 'module': 'health', 'permission_type': 'change', 'description': 'Edit health records'},
            {'name': 'Delete Health Records', 'codename': 'health.delete', 'module': 'health', 'permission_type': 'delete', 'description': 'Delete health records'},

            # Breeding Management permissions
            {'name': 'View Breeding Records', 'codename': 'breeding.view', 'module': 'breeding', 'permission_type': 'view', 'description': 'View breeding and insemination records'},
            {'name': 'Add Breeding Records', 'codename': 'breeding.add', 'module': 'breeding', 'permission_type': 'add', 'description': 'Add breeding records'},
            {'name': 'Edit Breeding Records', 'codename': 'breeding.change', 'module': 'breeding', 'permission_type': 'change', 'description': 'Edit breeding records'},
            {'name': 'Delete Breeding Records', 'codename': 'breeding.delete', 'module': 'breeding', 'permission_type': 'delete', 'description': 'Delete breeding records'},

            # Reports permissions
            {'name': 'View Reports', 'codename': 'reports.view', 'module': 'reports', 'permission_type': 'view', 'description': 'View all reports'},
            {'name': 'Export Reports', 'codename': 'reports.export', 'module': 'reports', 'permission_type': 'export', 'description': 'Export reports to PDF/Excel'},

            # Financial permissions
            {'name': 'View Financial Records', 'codename': 'financial.view', 'module': 'financial', 'permission_type': 'view', 'description': 'View financial records and transactions'},
            {'name': 'Add Financial Records', 'codename': 'financial.add', 'module': 'financial', 'permission_type': 'add', 'description': 'Add income and expense records'},
            {'name': 'Edit Financial Records', 'codename': 'financial.change', 'module': 'financial', 'permission_type': 'change', 'description': 'Edit financial records'},
            {'name': 'Delete Financial Records', 'codename': 'financial.delete', 'module': 'financial', 'permission_type': 'delete', 'description': 'Delete financial records'},

            # User Management permissions
            {'name': 'View Users', 'codename': 'users.view', 'module': 'users', 'permission_type': 'view', 'description': 'View user accounts and profiles'},
            {'name': 'Add Users', 'codename': 'users.add', 'module': 'users', 'permission_type': 'add', 'description': 'Create new user accounts'},
            {'name': 'Edit Users', 'codename': 'users.change', 'module': 'users', 'permission_type': 'change', 'description': 'Edit user accounts and roles'},
            {'name': 'Delete Users', 'codename': 'users.delete', 'module': 'users', 'permission_type': 'delete', 'description': 'Deactivate user accounts'},
            {'name': 'Manage Users', 'codename': 'users.manage', 'module': 'users', 'permission_type': 'manage', 'description': 'Full user management access'},
        ]

        for perm_data in permissions_data:
            permission, created = Permission.objects.get_or_create(
                codename=perm_data['codename'],
                defaults=perm_data
            )
            if created:
                self.stdout.write(f'Created permission: {permission.name}')

        # Assign permissions to roles
        role_permissions = {
            'farm_owner': [
                # Farm Owner has ALL permissions
                'dashboard.view', 'farm.view', 'farm.add', 'farm.change', 'farm.delete', 'farm.manage',
                'feeding.view', 'feeding.add', 'feeding.change', 'feeding.delete', 'feeding.manage',
                'health.view', 'health.add', 'health.change', 'health.delete',
                'breeding.view', 'breeding.add', 'breeding.change', 'breeding.delete',
                'reports.view', 'reports.export',
                'financial.view', 'financial.add', 'financial.change', 'financial.delete',
                'users.view', 'users.add', 'users.change', 'users.delete', 'users.manage'
            ],
            'farm_manager': [
                # Farm Manager has most permissions except user management
                'dashboard.view', 'farm.view', 'farm.add', 'farm.change', 'farm.manage',
                'feeding.view', 'feeding.add', 'feeding.change', 'feeding.manage',
                'health.view', 'health.add', 'health.change',
                'breeding.view', 'breeding.add', 'breeding.change',
                'reports.view', 'reports.export',
                'financial.view', 'users.view'
            ],
            'feed_manager': [
                # Feed Manager focuses on feeding and basic farm viewing
                'dashboard.view', 'farm.view',
                'feeding.view', 'feeding.add', 'feeding.change', 'feeding.delete', 'feeding.manage',
                'reports.view'
            ],
            'accountant': [
                # Accountant focuses on financial records and reports
                'dashboard.view', 'farm.view',
                'financial.view', 'financial.add', 'financial.change', 'financial.delete',
                'reports.view', 'reports.export'
            ],
            'viewer': [
                # Viewer has read-only access
                'dashboard.view', 'farm.view', 'feeding.view', 'health.view',
                'breeding.view', 'reports.view', 'financial.view'
            ]
        }

        for role_name, permission_codes in role_permissions.items():
            try:
                role = UserRole.objects.get(name=role_name)
                for perm_code in permission_codes:
                    try:
                        permission = Permission.objects.get(codename=perm_code)
                        role_permission, created = RolePermission.objects.get_or_create(
                            role=role,
                            permission=permission
                        )
                        if created:
                            self.stdout.write(f'Assigned {permission.name} to {role.display_name}')
                    except Permission.DoesNotExist:
                        self.stdout.write(f'Permission {perm_code} not found')
            except UserRole.DoesNotExist:
                self.stdout.write(f'Role {role_name} not found')

        self.stdout.write(self.style.SUCCESS('User system setup completed successfully!'))

        # Create a default admin user if none exists
        if not User.objects.filter(is_superuser=True).exists():
            farm_owner_role = UserRole.objects.get(name='farm_owner')
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@pigfarm.com',
                password='admin123',
                role=farm_owner_role,
                first_name='System',
                last_name='Administrator'
            )
            self.stdout.write(self.style.SUCCESS('Created default admin user: admin/admin123'))
        else:
            self.stdout.write('Admin user already exists')