# LinkForge Deployment Guide

LinkForge supports local, Dockerised, and cloud deployment (specifically optimized for Render).

## 1. Local Setup

### Prerequisites
* Python 3.13+
* Redis running locally (optional, falls back to memory caches)
* PostgreSQL running locally (optional, falls back to SQLite)

### Installation
1. Clone the repository and navigate to the folder.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate # On Windows PowerShell
   # source venv/bin/activate # On Unix
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment variables example:
   ```bash
   cp .env.example .env
   ```
5. Apply database migrations:
   ```bash
   python manage.py migrate
   ```
6. Run the local development server:
   ```bash
   python manage.py runserver
   ```
7. Start Celery worker in a separate terminal:
   ```bash
   celery -A config worker --loglevel=info
   ```

---

## 2. Docker Setup

Ensure you have Docker and Docker Compose installed.

1. Build and boot all services (PostgreSQL, Redis, Web App, Celery Worker):
   ```bash
   docker-compose up --build
   ```
2. The web application will boot and be accessible at `http://localhost:8000`.
3. Migrations are automatically run, and static files are collected.

---

## 3. Render Deployment

LinkForge is preconfigured with a [render.yaml](file:///d:/Code/django_projects/linkforge/render.yaml) blueprint specification.

### Automatic Blueprint Deployment
1. Push this project code to your GitHub/GitLab repository.
2. In the Render Dashboard, click **New** -> **Blueprint**.
3. Link your Git repository.
4. Render will parse [render.yaml](file:///d:/Code/django_projects/linkforge/render.yaml) and automatically spin up:
   * A PostgreSQL database.
   * A Redis cache.
   * A Python web service running Gunicorn (served via [render_build.sh](file:///d:/Code/django_projects/linkforge/render_build.sh)).
   * A Celery background worker service.
5. All environment variables, database linkings, and worker processes are automatically provisioned.
