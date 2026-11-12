# Deploy DrainGuard to Vercel

## Quick Start

1. **Push your code to GitHub** (if not already done):
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Go to Vercel**:
   - Visit [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository

3. **Configure the project**:
   - When prompted, select **"Services"** as the Application Preset
   - Vercel will auto-detect the configuration from `vercel.json`
   - Click "Deploy"

## What Was Changed

### Backend (FastAPI)
- Removed SQLite database dependency (not compatible with serverless)
- Embedded static station/sensor data directly in code
- Using in-memory storage for demo rainfall data
- Added `mangum` for AWS Lambda/Vercel compatibility
- Created `index.py` as the serverless entry point
- Simplified `requirements.txt` to essential packages only

### Frontend (React + Vite)
- Updated API calls to use `/api` prefix (handled by Vercel routing)
- No other changes needed

### Configuration
- `vercel.json` - Multi-service configuration
- `.vercelignore` - Excludes large data files and dev dependencies
- API routes: `/api/*` → backend service
- Frontend routes: `/*` → frontend service

## Testing Locally

Test the multi-service setup locally:

```bash
# Install Vercel CLI
npm i -g vercel

# Run locally
vercel dev
```

This starts both frontend and backend together.

## Production Notes

⚠️ **Database Limitation**: This setup uses in-memory data that resets on every function cold start. For production:

1. **Vercel Postgres** - Recommended for persistent data
2. **Supabase** - Free PostgreSQL with great DX
3. **PlanetScale** - Serverless MySQL
4. **MongoDB Atlas** - Free tier available

## Troubleshooting

### Build Fails
- Check Python version (Vercel uses Python 3.9)
- Verify `requirements.txt` has no conflicting versions
- Check build logs in Vercel dashboard

### API 500 Errors
- Check function logs in Vercel dashboard
- Verify CORS settings allow your domain
- Check cold start timeout (free tier: 10s)

### Frontend 404
- Ensure `vercel.json` rewrites are correct
- Check build output directory in Vercel settings

## Success! 🎉

Once deployed, your app will be available at:
- `https://your-project.vercel.app` - Frontend
- `https://your-project.vercel.app/api/health` - API health check
- `https://your-project.vercel.app/api/docs` - API documentation
