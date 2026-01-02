# Render Deployment Guide for Pig Farm Management System

This guide will help you deploy the Pig Farm Management System to Render.com.

## Prerequisites

1. A [Render account](https://render.com/) (free tier available)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. Git installed on your local machine

## Files Required for Deployment

The following files have been created/configured for Render deployment:

- ✅ `render.yaml` - Render Blueprint configuration
- ✅ `build.sh` - Build script for installing dependencies and running migrations
- ✅ `requirements.txt` - Python dependencies
- ✅ `runtime.txt` - Python version specification
- ✅ `.env.example` - Environment variables template

## Deployment Methods

### Method 1: Blueprint Deployment (Recommended)

This method uses the `render.yaml` file to automatically provision all services.

#### Steps:

1. **Push your code to GitHub/GitLab/Bitbucket**
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click **"New +"** → **"Blueprint"**

3. **Connect Repository**
   - Select your Git provider
   - Authorize Render to access your repositories
   - Select the `Pigs` repository

4. **Configure Blueprint**
   - Render will automatically detect `render.yaml`
   - Review the services that will be created:
     - **Web Service**: `pigfarm` (Python web app)
     - **PostgreSQL Database**: `pigfarm-db`

5. **Set Environment Variables**
   - Render will auto-generate `SECRET_KEY`
   - Update `ALLOWED_HOSTS` with your Render URL:
     - Go to the web service settings
     - Add environment variable: `ALLOWED_HOSTS` = `your-app-name.onrender.com`
   - All other variables are set automatically

6. **Deploy**
   - Click **"Apply"**
   - Render will:
     - Create PostgreSQL database
     - Install system dependencies (Cairo, Pango for PDF generation)
     - Install Python packages
     - Run migrations
     - Collect static files
     - Create default admin user
     - Start the application

7. **Access Your Application**
   - Once deployment completes, click the URL (e.g., `https://pigfarm.onrender.com`)
   - Default admin credentials:
     - Username: `admin`
     - Password: `admin123`
   - **IMPORTANT**: Change the admin password immediately after first login!

---

### Method 2: Manual Deployment

If you prefer manual setup without Blueprint:

#### Step 1: Create PostgreSQL Database

1. In Render Dashboard, click **"New +"** → **"PostgreSQL"**
2. Configure:
   - **Name**: `pigfarm-db`
   - **Database**: `pigfarm`
   - **User**: `pigfarm`
   - **Region**: Choose closest to your users
   - **Plan**: Free
3. Click **"Create Database"**
4. Copy the **Internal Database URL** (starts with `postgresql://`)

#### Step 2: Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your Git repository
3. Configure:
   - **Name**: `pigfarm`
   - **Region**: Same as database
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: `Python 3`
   - **Build Command**: `./build.sh`
   - **Start Command**: `cd pigfarm && gunicorn pigfarm.wsgi:application`
   - **Plan**: Free

4. **Environment Variables**:
   Click **"Advanced"** → **"Add Environment Variable"**

   Add these variables:
   ```
   SECRET_KEY = [Click "Generate" to auto-generate]
   DEBUG = False
   ALLOWED_HOSTS = your-app-name.onrender.com
   DATABASE_URL = [Paste Internal Database URL from Step 1]
   RENDER = true
   PYTHON_VERSION = 3.13.0
   ```

5. Click **"Create Web Service"**

---

## Post-Deployment Configuration

### 1. Update ALLOWED_HOSTS

After deployment, get your actual Render URL and update:

1. Go to your web service in Render Dashboard
2. Click **"Environment"**
3. Edit `ALLOWED_HOSTS` variable
4. Set value to your actual URL: `your-actual-app-name.onrender.com`
5. Save changes (service will auto-redeploy)

### 2. Change Default Admin Password

1. Login at `https://your-app-name.onrender.com/login/`
2. Username: `admin`, Password: `admin123`
3. Go to user settings and change password immediately

### 3. Set Up Admin Email (Optional)

If you want password reset functionality:

1. Configure email settings in `pigfarm/settings.py`
2. Add email environment variables in Render

### 4. Configure CSRF Settings (If Needed)

The app is pre-configured to accept `*.onrender.com` domains. If using a custom domain:

1. Update `CSRF_TRUSTED_ORIGINS` in [settings.py](pigfarm/pigfarm/settings.py)
2. Redeploy

---

## Database Migrations

Migrations run automatically during build via `build.sh`. To run migrations manually:

1. Go to Render Dashboard → Your Web Service
2. Click **"Shell"** tab
3. Run:
   ```bash
   cd pigfarm
   python manage.py migrate
   ```

---

## Troubleshooting

### Build Failures

**Issue**: Build fails with WeasyPrint errors

**Solution**: The `build.sh` script installs required system packages. If it still fails:
- Check Render build logs for specific error
- Ensure `build.sh` has execute permissions:
  ```bash
  chmod +x build.sh
  git add build.sh
  git commit -m "Make build.sh executable"
  git push
  ```

### Database Connection Errors

**Issue**: `OperationalError: could not connect to server`

**Solution**:
- Verify `DATABASE_URL` environment variable is set correctly
- Ensure PostgreSQL database is in the same region as web service
- Check database is active in Render Dashboard

### Static Files Not Loading

**Issue**: CSS/JS files return 404 errors

**Solution**:
- Verify `collectstatic` ran during build (check logs)
- Ensure `STATIC_ROOT` and `STATIC_URL` are set in [settings.py](pigfarm/pigfarm/settings.py:176)
- WhiteNoise middleware should be enabled (already configured)

### 500 Internal Server Error

**Issue**: Application shows 500 error

**Solution**:
1. Check Render logs: Dashboard → Service → Logs tab
2. Temporarily enable DEBUG:
   - Set `DEBUG=True` in environment variables
   - Check detailed error page
   - **Remember to set DEBUG=False after fixing!**

### App Sleeps on Free Tier

**Issue**: First request takes 30+ seconds

**Explanation**:
- Render free tier apps spin down after 15 minutes of inactivity
- First request after sleep takes time to wake up
- Subsequent requests are fast

**Solutions**:
- Upgrade to paid plan for 24/7 uptime
- Use external monitoring service to ping your app every 10 minutes (Note: This may violate Render's terms of service on free tier)

---

## File Uploads (Profile Pictures)

File uploads are stored in the `media/` directory. On Render's free tier:

⚠️ **Warning**: Files uploaded to Render's ephemeral filesystem will be deleted when the service restarts.

**Solutions for Production**:
1. Use Render Disk (paid feature) - persistent storage
2. Use cloud storage (AWS S3, Cloudinary, etc.) - recommended for production
3. For testing: Upload files will work but may be lost on restart

To add persistent storage (paid):
1. Go to service settings → Disks
2. Add disk mounted at `/opt/render/project/src/pigfarm/media`

---

## Monitoring and Logs

### View Logs
1. Render Dashboard → Your Service
2. Click **"Logs"** tab
3. Real-time logs show all application activity

### Health Checks
Render automatically monitors your app health. If it becomes unresponsive:
- Automatic restart attempts
- Email notifications (if configured)

---

## Scaling and Performance

### Free Tier Limitations
- 512 MB RAM
- Shared CPU
- Sleeps after 15 min inactivity
- 750 hours/month
- 100 GB bandwidth/month

### Upgrade Options
For production use, consider:
- **Starter Plan** ($7/month): 512 MB RAM, always on
- **Standard Plan** ($25/month): 2 GB RAM, better performance
- **PostgreSQL Paid Plan**: Automated backups, more storage

---

## Custom Domain (Optional)

To use your own domain:

1. Go to Service Settings → Custom Domains
2. Add your domain (e.g., `farm.yourdomain.com`)
3. Update DNS records as instructed by Render
4. Update `ALLOWED_HOSTS` environment variable to include your domain
5. Update `CSRF_TRUSTED_ORIGINS` in [settings.py](pigfarm/pigfarm/settings.py:35) if needed

---

## Security Checklist

Before going live:

- ✅ `DEBUG=False` in production
- ✅ Strong `SECRET_KEY` (auto-generated by Render)
- ✅ Changed default admin password
- ✅ `ALLOWED_HOSTS` set to your actual domain
- ✅ HTTPS enabled (automatic on Render)
- ✅ Database password is strong (auto-generated)
- ✅ CSRF protection enabled
- ⚠️ Consider setting up email for password resets
- ⚠️ Review user permissions and roles
- ⚠️ Set up regular database backups (paid feature)

---

## Backup and Recovery

### Database Backups

**Free Tier**: No automatic backups

**Paid PostgreSQL**:
- Automatic daily backups
- Point-in-time recovery
- Manual backup snapshots

**Manual Backup** (Free tier):
```bash
# In Render Shell
cd pigfarm
python manage.py dumpdata > backup.json
```

Download via SFTP or store in external service.

---

## Cost Estimate

### Free Tier (Development/Testing)
- Web Service: Free
- PostgreSQL: Free
- Total: **$0/month**
- Limitations: Apps sleep, no backups, ephemeral storage

### Production Setup
- Web Service Starter: $7/month
- PostgreSQL Starter: $7/month
- Render Disk (10GB): $1/month
- Total: **~$15/month**

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | Auto-generated | Django secret key |
| `DEBUG` | Yes | `False` | Debug mode (always False in production) |
| `ALLOWED_HOSTS` | Yes | - | Comma-separated allowed domains |
| `DATABASE_URL` | Yes | Auto-set | PostgreSQL connection string |
| `RENDER` | Yes | `true` | Platform indicator |
| `PYTHON_VERSION` | No | `3.13.0` | Python runtime version |

---

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/)
- [Render Python Guide](https://render.com/docs/deploy-django)
- [PostgreSQL on Render](https://render.com/docs/databases)

---

## Support

If you encounter issues:

1. Check Render logs for error details
2. Review this documentation
3. Check Render status page: https://status.render.com/
4. Contact Render support: https://render.com/support

---

## Next Steps

After successful deployment:

1. ✅ Test all functionality (login, CRUD operations, reports)
2. ✅ Create additional user accounts with appropriate roles
3. ✅ Set up farm rooms, feed stock, and initial data
4. ✅ Train users on the system
5. ✅ Monitor application performance and logs
6. ✅ Plan for regular backups (if using paid tier)

---

**Deployment Date**: 2026-01-02
**Django Version**: 5.1.6
**Python Version**: 3.13.0
**Render Blueprint Version**: 1.0
