# Render Deployment - Quick Start Guide

## 🚀 Fast Track to Deployment (5 Steps)

### Step 1: Push to Git (2 minutes)
```bash
cd /Users/gataremmanuel/Projects/Pigs
git add .
git commit -m "Prepare for Render deployment"
git push origin main
```

### Step 2: Create Render Account (1 minute)
- Go to https://render.com/
- Sign up with GitHub (recommended) or email
- Verify your email

### Step 3: Deploy with Blueprint (2 minutes)
1. Click **"New +"** → **"Blueprint"**
2. Connect your GitHub account
3. Select the `Pigs` repository
4. Click **"Apply"**

Render will automatically:
- Create PostgreSQL database
- Install dependencies
- Run migrations
- Start your app

### Step 4: Update ALLOWED_HOSTS (1 minute)
After deployment completes:
1. Copy your Render URL (e.g., `pigfarm-abc123.onrender.com`)
2. Go to **Environment** tab
3. Update `ALLOWED_HOSTS` variable:
   ```
   ALLOWED_HOSTS = pigfarm-abc123.onrender.com
   ```
4. Save (auto-redeploys)

### Step 5: Login & Change Password (1 minute)
1. Visit your Render URL
2. Login:
   - Username: `admin`
   - Password: `admin123`
3. **Change password immediately!**

## ✅ That's it! Your app is live!

---

## 📋 What Was Created

### Files Added:
- ✅ `render.yaml` - Deployment blueprint
- ✅ `build.sh` - Build script
- ✅ `.env.example` - Environment template
- ✅ `RENDER_DEPLOYMENT.md` - Full documentation
- ✅ `DEPLOYMENT_CHECKLIST.md` - Complete checklist
- ✅ This quick start guide

### Files Updated:
- ✅ `pigfarm/pigfarm/settings.py` - Added Render support
- ✅ `pigfarm/pigfarm/urls.py` - Added media file serving

---

## 🔧 Render Configuration Summary

### Services Created:
1. **Web Service**: `pigfarm`
   - Runtime: Python 3.13.0
   - Plan: Free
   - Build: `./build.sh`
   - Start: `cd pigfarm && gunicorn pigfarm.wsgi:application`

2. **PostgreSQL Database**: `pigfarm-db`
   - Plan: Free
   - Database: `pigfarm`
   - User: `pigfarm`

### Auto-Configured Environment Variables:
- `SECRET_KEY` - Auto-generated
- `DEBUG` - Set to `False`
- `DATABASE_URL` - Auto-linked to PostgreSQL
- `RENDER` - Set to `true`
- `PYTHON_VERSION` - `3.13.0`

### You Need to Set:
- `ALLOWED_HOSTS` - Your actual Render URL

---

## ⚠️ Important Notes

### Free Tier Behavior:
- **App sleeps after 15 min inactivity** (first request takes ~30 seconds to wake)
- **Files uploaded are ephemeral** (lost on restart)
- **No automatic backups**
- **750 hours/month** (enough for one always-on service)

### Default Credentials:
- Username: `admin`
- Password: `admin123`
- **CHANGE IMMEDIATELY AFTER FIRST LOGIN!**

### Static Files:
- ✅ Handled by WhiteNoise (no configuration needed)
- ✅ CSS, JavaScript, images work automatically

### PDF Generation:
- ✅ WeasyPrint configured
- ✅ System dependencies auto-installed
- ✅ Reports work out of the box

---

## 🆘 Common Issues

### Build Fails?
```bash
chmod +x build.sh
git add build.sh
git commit -m "Make build executable"
git push
```
Then trigger manual redeploy in Render.

### Can't Login?
Check logs in Render Dashboard → Logs tab

### Static Files Not Loading?
- Wait for deployment to fully complete
- Check build logs confirm `collectstatic` ran
- Hard refresh browser (Ctrl+F5 or Cmd+Shift+R)

### Database Errors?
- Verify PostgreSQL service is running
- Check `DATABASE_URL` is set
- Review migration logs in build output

---

## 📊 What Happens During Build?

1. ✅ Install system packages (Cairo, Pango for PDFs)
2. ✅ Install Python dependencies from `requirements.txt`
3. ✅ Collect static files
4. ✅ Run database migrations
5. ✅ Create default admin user
6. ✅ Start Gunicorn server

**Build time**: ~3-5 minutes

---

## 📱 Access Your App

### Main URLs:
- **Homepage/Dashboard**: `https://your-app.onrender.com/`
- **Login**: `https://your-app.onrender.com/login/`
- **Admin Panel**: `https://your-app.onrender.com/admin/`

### Test These Features:
- ✅ Login with admin credentials
- ✅ Create a room
- ✅ Register a sow
- ✅ Add feed stock
- ✅ Generate a report
- ✅ Export to PDF

---

## 💰 Cost Breakdown

### Current Setup (Free):
- Web Service: **Free**
- PostgreSQL: **Free**
- **Total: $0/month**

### Production Upgrade (~$15/month):
- Web Service Starter: $7
- PostgreSQL Starter: $7
- Render Disk (10GB): $1
- **Total: ~$15/month**

Benefits of upgrade:
- ✅ Always on (no sleeping)
- ✅ Automatic backups
- ✅ Persistent file storage
- ✅ Better performance

---

## 🔒 Security Checklist

After deployment:
- [ ] Changed admin password
- [ ] `DEBUG=False` in production
- [ ] HTTPS enabled (automatic)
- [ ] Strong `SECRET_KEY` (auto-generated)
- [ ] `ALLOWED_HOSTS` configured
- [ ] CSRF protection active

---

## 📚 Full Documentation

For detailed information, see:
- [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) - Complete deployment guide
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Step-by-step checklist
- [.env.example](.env.example) - Environment variables reference

---

## 🎯 Next Steps

1. **Test everything** - Go through all features
2. **Change admin password** - Security first!
3. **Create user accounts** - For farm staff
4. **Add initial data** - Rooms, feed stock, etc.
5. **Train users** - Show them how to use the system
6. **Monitor logs** - Watch for errors first few days

---

## 🆘 Need Help?

- **Render Docs**: https://render.com/docs
- **Django Docs**: https://docs.djangoproject.com/
- **Render Status**: https://status.render.com/
- **Render Support**: https://render.com/support

---

## 🎉 Congratulations!

Your Pig Farm Management System is now live on Render!

**Deployment takes ~5 minutes total** ⏱️

Questions? Check [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed help.

---

**Created**: 2026-01-02
**Version**: 1.0
**Platform**: Render.com
