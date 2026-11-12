# DrainGuard Vercel Deployment Checklist

## ✅ Pre-Deployment (Completed)

- [x] Created `vercel.json` with multi-service configuration
- [x] Updated backend to remove SQLite dependency
- [x] Created in-memory data storage with sample data
- [x] Added `mangum` for serverless compatibility
- [x] Created `backend/index.py` entry point
- [x] Simplified `requirements.txt` for Vercel
- [x] Updated frontend API calls to use `/api` prefix
- [x] Created `.vercelignore` to exclude large files
- [x] Set Python version to 3.9

## 🚀 Deploy to Vercel

### Step 1: Commit and Push
```bash
git add .
git commit -m "Configure for Vercel deployment"
git push origin main
```

### Step 2: Import to Vercel
1. Go to https://vercel.com/new
2. Import your GitHub repository: `junxnor/DrainGuardSG`
3. **IMPORTANT**: Select **"Services"** as the Application Preset
4. Click Deploy

### Step 3: Wait for Build
- Vercel will build both services
- Backend: Installs Python dependencies
- Frontend: Runs `npm install && npm run build`
- Usually takes 2-5 minutes

### Step 4: Test
Visit these URLs (replace with your domain):
- https://your-project.vercel.app → Frontend
- https://your-project.vercel.app/api/health → API health
- https://your-project.vercel.app/api/docs → API docs
- https://your-project.vercel.app/api/stations → Stations data

## 🔧 If Build Fails

### Backend Issues
1. Check function logs in Vercel dashboard
2. Verify Python version: Should be 3.9
3. Check dependencies in `backend/requirements.txt`

### Frontend Issues
1. Check build logs in Vercel dashboard
2. Ensure `package.json` has all dependencies
3. Try building locally: `cd frontend && npm run build`

## 📝 Post-Deployment

### Optional: Custom Domain
1. Go to Project Settings → Domains
2. Add your domain
3. Update DNS records
4. Wait for SSL provisioning (~10 min)

### Optional: Environment Variables
If you need them later:
1. Go to Project Settings → Environment Variables
2. Add variables
3. Redeploy for changes to take effect

## 🎯 What to Expect

### Working Features
✅ Frontend loads and displays map
✅ API endpoints respond
✅ Stations and sensors data available
✅ Sample rainfall data (last 48 hours)
✅ Risk assessment calculations
✅ Recommendations endpoint

### Limitations (Demo Mode)
⚠️ Data resets on function cold starts
⚠️ No historical data persistence
⚠️ Sample data only (not real-time)

### For Production
To make this production-ready, you'll need:
1. Connect to a real database (Vercel Postgres, Supabase, etc.)
2. Integrate with Singapore's real-time weather APIs
3. Add data persistence layer
4. Set up scheduled tasks for data updates

## 🆘 Need Help?

- Vercel Docs: https://vercel.com/docs/services
- Check logs: Vercel Dashboard → Deployments → Function Logs
- Vercel Support: support@vercel.com

## 🎉 Success Indicators

- ✅ Build completes without errors
- ✅ Frontend loads at root URL
- ✅ API health check returns 200 OK
- ✅ API docs page loads
- ✅ No console errors in browser
