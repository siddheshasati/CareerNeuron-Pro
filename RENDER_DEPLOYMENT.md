# Render Deployment Guide for CareerNeuron-Pro

## Quick Start (Recommended)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Production ready for Render"
   git push origin main
   ```

2. **Connect to Render**
   - Go to https://render.com/
   - Click "New +" → "Web Service"
   - Select your GitHub repository
   - Render auto-detects `render.yaml`

3. **Set Environment Variables**
   - In Render Dashboard > Environment:
     - `DJANGO_SECRET_KEY`: Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
     - (Other variables are pre-configured in `render.yaml`)

4. **Deploy**
   - Click "Create Web Service"
   - Render will provision PostgreSQL database + web service
   - Migrations run automatically on first start

---

## If migrations don't run automatically

If you still see `no such table: auth_user` error:

### Option A: Manual migration via Render Shell
1. Go to Render Dashboard > Your Service > Shell
2. Run:
   ```bash
   python manage.py migrate
   ```

### Option B: Verify Database Connection
1. In Render Dashboard > Environment Variables, add:
   ```
   DATABASE_URL = (copy the PostgreSQL connection string from your DB service)
   ```
2. Redeploy

### Option C: Check if PostgreSQL was provisioned
1. Go to Render Dashboard > Databases
2. You should see `careerneuron_db`
3. If not, manually add a PostgreSQL database service

---

## Production Checklist

- [x] `DJANGO_DEBUG = False` in production
- [x] `DJANGO_SECRET_KEY` is strong
- [x] `DATABASE_URL` points to PostgreSQL (managed by Render or manually set)
- [x] Static files collected (happens in build)
- [x] Migrations run (happens in startCommand)
- [x] ALLOWED_HOSTS configured
- [x] Security headers enabled (HSTS, CSP, HTTPS)

---

## Troubleshooting

### "no such table: auth_user"
- Migrations have not run
- Solution: Run `python manage.py migrate` in Render Shell or redeploy

### "unable to connect to database"
- `DATABASE_URL` is not set or wrong
- Solution: Check environment variables, ensure PostgreSQL service exists

### "DisallowedHost"
- Hostname not in `ALLOWED_HOSTS`
- Solution: Already configured in `render.yaml` for `careerneuron-pro.onrender.com`

---

## Advanced: Manual PostgreSQL Setup on Render

If `render.yaml` database doesn't auto-provision:

1. In Render Dashboard > New > PostgreSQL Database
   - Name: `careerneuron_db`
   - Choose free tier
2. Copy the "Internal Database URL"
3. In your web service > Environment > add:
   - `DATABASE_URL = <paste-url-here>`
4. Redeploy

---

## Next Steps

After successful deployment:
- Create a superuser: `python manage.py createsuperuser` (via Render Shell)
- Visit https://careerneuron-pro.onrender.com/
- Set up email credentials for OTP verification
- Configure GROQ_API_KEY for AI features
