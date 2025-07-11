# Frontend Deployment Guide

## Environment Configuration

To connect the frontend to your deployed backend, you need to set the `VITE_API_BASE_URL` environment variable.

### For Vercel Deployment:

1. **Set Environment Variable:**
   - Go to your Vercel project settings
   - Navigate to "Environment Variables"
   - Add: `VITE_API_BASE_URL` = `https://your-render-backend-url.onrender.com`

2. **Redeploy:**
   - After setting the environment variable, redeploy your frontend

### For Local Development:

Create a `.env` file in the frontend directory:
```
VITE_API_BASE_URL=http://localhost:8000
```

### For Other Platforms:

Set the environment variable `VITE_API_BASE_URL` to your Render backend URL:
```
VITE_API_BASE_URL=https://your-app-name.onrender.com
```

## Backend URL Format

Your Render backend URL will be in this format:
- `https://your-app-name.onrender.com`

Replace `your-app-name` with your actual Render app name.

## Testing the Connection

After deployment, you can test if the frontend is connecting to the backend by:
1. Opening the browser developer tools
2. Looking for any network errors in the Console tab
3. Checking if API calls are being made to your Render URL 