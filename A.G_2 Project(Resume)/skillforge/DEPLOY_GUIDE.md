# Deploying Skill Forge — step by step (Render, free tier)

I can't create accounts or push code to the internet on your behalf (this
environment has no internet access), but the project is now deploy-ready.
Here's exactly what to do — about 15 minutes.

## What I fixed in the code first
- `config/wsgi.py` was hardcoded to load **dev** settings (DEBUG=True, SQLite)
  even in production. It now defaults to `config.settings.prod`.
- Added `Procfile` (tells the host how to run migrations + start the app with gunicorn).
- Added `runtime.txt` pinned to Python 3.12.7 — your `__pycache__` files showed
  the project was run on Python 3.14 locally, which most hosts don't support yet.
- Added `CSRF_TRUSTED_ORIGINS` to `config/settings/prod.py` — without this,
  login/signup/admin forms return a 403 on any HTTPS host.
- Added `.gitignore` (was missing — `db.sqlite3` and `__pycache__` were about
  to get committed).
- Added `render.yaml` so Render can set up the web service + free Postgres
  database automatically.

## One thing to know before you launch
This app lets users upload course **videos**, thumbnails, avatars, and
certificates. Free hosting tiers (Render included) use **ephemeral disk** —
uploaded files disappear on every redeploy/restart. Fine for a demo, but if
you want uploads to persist, add free Cloudinary storage later (`pip install
django-cloudinary-storage`, ~10 min setup) — happy to wire that in if you want it.

## Step 1 — Push to GitHub
1. Create a new repo at https://github.com/new (public or private, either works).
2. In the project folder:
   ```
   git init
   git add .
   git commit -m "Skill Forge - ready for deployment"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git push -u origin main
   ```

## Step 2 — Deploy on Render
1. Go to https://render.com → sign up (free, GitHub login is fastest).
2. Click **New +** → **Blueprint**, and connect the GitHub repo you just pushed.
3. Render will detect `render.yaml` and set up two things automatically:
   - A free PostgreSQL database
   - A free web service running gunicorn
4. Click **Apply** — first deploy takes 3–5 minutes (installs deps, runs
   `collectstatic`, runs migrations, starts the server).
5. When it's live, Render gives you a public URL like
   `https://skillforge.onrender.com` — that's your shareable demo link.

## Step 3 — One required follow-up
Open the web service → **Environment**, and update `CSRF_TRUSTED_ORIGINS` to
your *actual* Render URL (it's a placeholder in render.yaml right now):
```
CSRF_TRUSTED_ORIGINS=https://<your-actual-subdomain>.onrender.com
```
Save → it auto-redeploys. Without this step, login and the Django admin will
throw a 403 Forbidden.

## Step 4 — Create an admin login (optional but useful for a demo)
In the Render dashboard, open your web service → **Shell**, then run:
```
python manage.py createsuperuser
```

## About the free tier
Render's free web services **sleep after 15 minutes of no traffic** and take
~30–50 seconds to wake up on the next visit — this matches "public can view
anytime by clicking a link," just with a short wait on the first click after
idle time. If you want zero cold-start delay, Render's paid Starter plan
($7/mo) keeps it always-on — or Railway (usage-based free credits, similar
setup) is a good alternative with less aggressive sleeping.

## Alternatives if you'd rather not use Render
| Host | Good for | Notes |
|---|---|---|
| **Render** (recommended) | Full Django + Postgres, easiest free setup | Sleeps when idle on free tier |
| **Railway** | Same as Render, nicer UI | Free tier is credit-based, not unlimited |
| **PythonAnywhere** | Simplest for beginners | Free tier has no Postgres (SQLite only), less suited to this app |
| **Fly.io** | More control, Docker-based | More setup steps, needs a Dockerfile |
