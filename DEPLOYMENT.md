# 🚀 DrainGuard Deployment Guide

## Quick Deploy (Recommended)

### Option 1: Frontend Only on Vercel (Fastest - 5 mins)

1. Go to https://vercel.com/new
2. Import your GitHub repo: `junxnor/DrainGuard`
3. **Framework Preset:** Vite
4. **Root Directory:** `frontend`
5. **Build Command:** `npm run build`
6. **Output Directory:** `dist`
7. Click **Deploy**

**Note:** Backend will need to run locally. For demo purposes, this is acceptable.

---

## Option 2: Full Deployment (Frontend + Backend)

### Step 1: Deploy Backend to Render

#### Method A: Using render.yaml (Automatic)

1. Go to https://render.com
2. Sign in with GitHub
3. Click **"New +"** → **"Blueprint"**
4. Connect repository: `junxnor/DrainGuard`
5. Render will automatically detect `render.yaml`
6. Click **"Apply"**
7. Wait for deployment (5-10 mins)
8. **Copy the backend URL** (e.g., `https://drainguard-api.onrender.com`)

#### Method B: Manual Setup

1. Go to https://render.com
2. Click **"New +"** → **"Web Service"**
3. Connect repository: `junxnor/DrainGuard`
4. Configure:
   - **Name:** `drainguard-api`
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Python Version:** `3.11.6`
   - **Build Command:** `pip install -r requirements-deploy.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Click **"Create Web Service"**
6. **Copy the backend URL**

### Step 2: Deploy Frontend to Vercel

1. Go to https://vercel.com/new
2. Import: `junxnor/DrainGuard`
3. **Framework Preset:** Vite
4. **Root Directory:** `frontend`
5. **Build Command:** `npm run build`
6. **Output Directory:** `dist`
7. **Environment Variables:**
   - `VITE_API_URL` = `https://drainguard-api.onrender.com` (from Step 1)
8. Click **Deploy**

---

## Alternative: Deploy to Railway

### Backend on Railway

1. Go to https://railway.app
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Select: `junxnor/DrainGuard`
4. Add these settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements-deploy.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Copy the generated URL

### Frontend on Vercel

Same as above, use Railway URL for `VITE_API_URL`

---

## 🔧 Troubleshooting

### Backend Deployment Issues

**Error: "scikit-learn build failed"**
- Make sure you're using `requirements-deploy.txt` NOT `requirements.txt`
- `requirements-deploy.txt` excludes scikit-learn (only needed for local ML training)

**Error: "Database not found"**
- The database is created automatically on first run
- If issues persist, check logs for database initialization errors

**Error: "Port binding failed"**
- Make sure start command uses `$PORT` environment variable
- Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Frontend Deployment Issues

**Error: "Build failed"**
- Check Node.js version (should be 18+)
- Verify `package.json` is in `frontend` directory
- Ensure Root Directory is set to `frontend`

**Error: "Cannot connect to API"**
- Check `VITE_API_URL` environment variable
- Make sure backend URL is correct and accessible
- Check browser console for CORS errors (CORS is set to allow all origins)

---

## 📊 Verify Deployment

### Check Backend
Visit: `https://your-backend-url.onrender.com/api/health`

Should return:
```json
{
  "status": "ok",
  "timestamp": "...",
  "service": "DrainGuard Singapore API",
  "version": "1.0.0"
}
```

### Check API Docs
Visit: `https://your-backend-url.onrender.com/api/docs`

### Check Frontend
Visit your Vercel URL and verify:
- Map loads
- Risk cards display
- No console errors

---

## 💡 Tips for Hackathon Demo

1. **Free Tier Limits:**
   - Render: Backend may sleep after 15 mins of inactivity (takes 30s to wake up)
   - Vercel: 100 GB bandwidth/month (more than enough)

2. **Quick Demo Setup:**
   - Have both URLs ready
   - Test before submitting
   - Take screenshots in case site goes down during judging

3. **Fallback Plan:**
   - Keep video demo ready
   - Local setup instructions in README
   - Screenshots of working dashboard

---

## 🎯 Deployment URLs Template

For your hackathon submission form:

**Backend API:**
```
https://drainguard-api.onrender.com
```

**Frontend Demo:**
```
https://drainguard.vercel.app
```

**GitHub Repo:**
```
https://github.com/junxnor/DrainGuard
```

---

**Good luck with your deployment! 🚀**
