# Render Deployment Guide

This project is fully prepared and optimized for deployment on [Render](https://render.com).

---

## Architecture Overview & Key Adaptations for Render

1. **Supabase Database Connection**:
   Set `DATABASE_URL` in Render to your Supabase PostgreSQL connection string. The app converts `postgres://` or `postgresql://` to the async SQLAlchemy format and enables SSL for Supabase.
2. **Pre-Deploy Database Migrations**:
   Alembic migrations run safely during Render's `preDeployCommand` (`alembic upgrade head`) before traffic is routed to the new deployment, preventing race conditions.
3. **Health Check Endpoint**:
   The `/healthz` endpoint performs an async database ping (`SELECT 1`) and reports health status, satisfying Render's zero-downtime health check requirements.
4. **Configurable CORS**:
   `CORS_ORIGINS` can be set to `*` or a comma-separated list of allowed frontend domains (e.g. `https://my-frontend.vercel.app,https://my-frontend.onrender.com`).
5. **Clean Dependencies**:
   Heavy and unnecessary desktop packages (such as `PyQt6`) have been stripped from `requirements.txt` to guarantee fast, memory-safe builds within Render's build limits.

---

## Deployment Option 1: Render Blueprint (Recommended - 1-Click)

The repository includes a [`render.yaml`](render.yaml) Blueprint for the Web Service. It expects you to provide `DATABASE_URL` from Supabase; it does not create a separate Render database.

1. Push your repository to **GitHub** or **GitLab**.
2. Log in to your [Render Dashboard](https://dashboard.render.com).
3. Click **New +** and select **Blueprint**.
4. Connect your repository.
5. Render will detect `render.yaml` and configure:
   - The FastAPI web service (`inventory-management-api`).
   - An automatically generated `JWT_SECRET_KEY`.
   - A prompt for the Supabase `DATABASE_URL`.
   - The migration pre-deploy command and health check path (`/healthz`).
6. For `DATABASE_URL`, paste the Supabase PostgreSQL connection string. Prefer the **Direct connection** URL if Render can reach it. If using Supabase's **Session pooler**, use its connection string and port. Avoid the transaction pooler (port `6543`) for migrations; use a direct or session connection. Click **Apply**. Render will run `alembic upgrade head` against that Supabase database before deploying the API.

---

## Deployment Option 2: Manual Web Service Setup

If you prefer to configure the service manually in the Render dashboard:

### Step 1: Get the Supabase connection string
In Supabase, open **Project Settings -> Database -> Connection string** and copy a PostgreSQL URI. Use the direct connection when available, or the session pooler URI if required by your network. The app expects PostgreSQL credentials and requires SSL.

### Step 2: Create the Web Service
1. Go to **New +** -> **Web Service**.
2. Connect your Git repository.
3. Configure the following settings:
   - **Name**: `inventory-management-api`
   - **Region**: Choose the same region as your database (e.g., Oregon or Frankfurt).
   - **Branch**: `main`
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Pre-Deploy Command**: `alembic upgrade head`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path**: `/healthz`

### Step 3: Add Environment Variables
Under the **Environment** tab, add:
| Key | Value | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql://...` | Supabase PostgreSQL connection string |
| `JWT_SECRET_KEY` | `your-32-character-secret` | Random secret key for signing JWTs |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | Token expiration in minutes (e.g., 7 days) |
| `CORS_ORIGINS` | `*` or your frontend URLs | Comma-separated allowed origins |
| `AUTO_MIGRATE` | `false` | Migrations are executed via Pre-Deploy Command |
| `DATABASE_ECHO` | `false` | Keep query logging quiet in production |
| `ENVIRONMENT` | `production` | Environment name |

4. Click **Deploy Web Service**.

---

## Deployment Option 3: Docker Deployment

Render also natively supports deploying from the provided [`Dockerfile`](file:///Users/dev7/Desktop/iOne-intern-srunborath/fastapi/inventory_management/Dockerfile):

1. Go to **New +** -> **Web Service**.
2. Select your repository.
3. Select **Docker** as the Environment.
4. Add the same Environment Variables as in Option 2.
5. Click **Create Web Service**. Set **Pre-Deploy Command** to `alembic upgrade head` in the Render service settings; the Dockerfile itself only starts the API.

---

## File Uploads & Persistent Storage on Render

By default, Render web services have an **ephemeral disk** (uploaded images in `/app/uploads` will be wiped when the service restarts or redeploys).

To persist uploaded files:
1. In your Web Service settings on Render, navigate to **Disks**.
2. Click **Add Disk**:
   - **Name**: `uploads-storage`
   - **Mount Path**: `/app/uploads`
   - **Size**: `1 GB` (or desired size)
3. Save changes. Any files uploaded to `/uploads` will now be preserved permanently across deployments.

---

## Verifying Deployment

Once deployed, visit your Render URL:
- **Root endpoint**: `https://<your-service>.onrender.com/`
- **Interactive API Docs (Swagger UI)**: `https://<your-service>.onrender.com/docs`
- **Health Check**: `https://<your-service>.onrender.com/healthz`
