# 🚀 100% Free Production Deployment Guide

Deploy your English Learning Agent full-stack application for **$0/month** using:
- **Frontend:** [Vercel](https://vercel.com) (Free Hobby Tier — Global Edge CDN, Free SSL)
- **Backend API & Celery Worker:** [Render](https://render.com) (Free Web Service Tier — 750 free hours/month)
- **Cloud Redis for Celery:** [Upstash](https://upstash.com) (Free Tier — 10,000 commands/day, No credit card needed)
- **PostgreSQL Database:** [Render Database](https://render.com) or [Neon.tech](https://neon.tech) (Free Tier)
- **AI Processing:** [Google AI Studio](https://aistudio.google.com) (Free Tier Gemini API)

---

## Step 1: Get Free Redis (Upstash) — 1 Minute

1. Go to [Upstash.com](https://upstash.com/) and create a free account (no credit card required).
2. Click **Create Database**:
   - **Name:** `english-coach-redis`
   - **Type:** Regional (select region closest to you or closest to your Render server, e.g., `us-east-1` or `frankfurt`)
3. Once created, scroll down to the **Connect / Details** section and copy the **`rediss://...`** URL.
   *(Example: `rediss://default:AbCdEf...==@us1-quick-slug-12345.upstash.io:6379`)*

---

## Step 2: Deploy the Backend (Render) — 3 Minutes

### Option A: Using Render Blueprint (`render.yaml`) — 1 Click
1. Push your latest code to your GitHub repository.
2. In [Render Dashboard](https://dashboard.render.com/), click **New** $\rightarrow$ **Blueprint**.
3. Select your repository. Render will automatically detect [`render.yaml`](file:///c:/Users/hp/OneDrive%20-%20Higher%20Education%20Commission/Documents/EnglishLearningAgent/render.yaml).
4. Fill in the prompted secret variables:
   - `GEMINI_API_KEY`: Your Gemini API key from [Google AI Studio](https://aistudio.google.com/)
   - `CELERY_BROKER_URL`: The Upstash `rediss://...` URL from Step 1
   - `CELERY_RESULT_BACKEND`: Same Upstash `rediss://...` URL
5. Click **Apply**. Render will automatically provision:
   - The PostgreSQL Database
   - The Django API web server
   - The background Celery worker (running concurrently inside the same container via `start.sh`)

### Option B: Manual Web Service Setup on Render
1. In [Render Dashboard](https://dashboard.render.com/), click **New** $\rightarrow$ **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name:** `english-coach-backend`
   - **Language:** `Python`
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `bash start.sh`
   - **Instance Type:** `Free`
4. Add the following **Environment Variables**:
   ```env
   DEBUG=False
   SECRET_KEY=generate-any-random-50-character-secret-string
   DATABASE_URL=your-postgres-connection-string
   CELERY_TASK_ALWAYS_EAGER=False
   CELERY_BROKER_URL=rediss://default:...@your-upstash-endpoint.upstash.io:6379
   CELERY_RESULT_BACKEND=rediss://default:...@your-upstash-endpoint.upstash.io:6379
   GEMINI_API_KEY=your-gemini-key
   AUTH_COOKIE_SAMESITE=None
   AUTH_COOKIE_SECURE=True
   ```
5. Click **Deploy Web Service**.
6. Copy your public backend URL once live (e.g., `https://english-coach-backend.onrender.com`).

---

## Step 3: Deploy Frontend to Vercel — 2 Minutes

1. Go to [Vercel.com](https://vercel.com/) and click **Add New** $\rightarrow$ **Project**.
2. Import your GitHub repository.
3. In the project configuration:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click *Edit* $\rightarrow$ select `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Expand **Environment Variables** and add:
   ```env
   VITE_API_BASE_URL=https://your-backend-url.onrender.com/api
   ```
   *(Replace with your actual Render URL from Step 2, making sure to append `/api`)*
5. Click **Deploy**.

---

## Step 4: Final Connection (CORS Update)

Once your Vercel deployment completes:
1. Copy your Vercel URL (e.g., `https://english-learning-agent.vercel.app`).
2. Go to your backend service on **Render** $\rightarrow$ **Environment**.
3. Add or update:
   ```env
   CORS_ALLOWED_ORIGINS=https://english-learning-agent.vercel.app
   ```
4. Save changes (Render will automatically redeploy with the new allowed origin).

---

## Optional: Keep Backend Awake 24/7 for Free

On Render's free tier, the backend spins down after 15 minutes of inactivity. To prevent a 30-second cold start when you open the app:
1. Go to [UptimeRobot.com](https://uptimerobot.com) (100% Free).
2. Click **Add New Monitor**:
   - **Monitor Type:** `HTTP(s)`
   - **Friendly Name:** `English Coach Backend`
   - **URL:** `https://your-backend-url.onrender.com/api/exercises/`
   - **Monitoring Interval:** Every `10 minutes`
3. Click **Create Monitor**.

Now your backend will stay warm and active 24/7 at **$0 cost**!
