"""
One-time setup views for creating admin user
"""
from django.http import HttpResponse
from users.models import CustomUser

def create_admin(request):
    """
    One-time endpoint to create admin user
    Access at: /setup-admin/
    """
    try:
        username = 'admin'
        email = 'admin@pigfarm.com'
        password = 'admin123'

        if CustomUser.objects.filter(username=username).exists():
            user = CustomUser.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            return HttpResponse(f"""
                <h1>✅ Admin User Updated</h1>
                <p><strong>Username:</strong> {username}</p>
                <p><strong>Password:</strong> {password}</p>
                <p><strong>⚠️ IMPORTANT:</strong> Change this password immediately after login!</p>
                <p><a href="/login/">Go to Login</a></p>
            """)
        else:
            user = CustomUser.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()
            return HttpResponse(f"""
                <h1>✅ Admin User Created Successfully!</h1>
                <p><strong>Username:</strong> {username}</p>
                <p><strong>Password:</strong> {password}</p>
                <p><strong>⚠️ IMPORTANT:</strong> Change this password immediately after login!</p>
                <p><a href="/login/">Go to Login</a></p>
            """)
    except Exception as e:
        return HttpResponse(f"""
            <h1>❌ Error Creating Admin User</h1>
            <p><strong>Error:</strong> {str(e)}</p>
            <pre>{repr(e)}</pre>
        """, status=500)
