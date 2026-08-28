# Development Guide

## Quick Start from Scratch

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (Node 20+ recommended)
- Docker & Docker Compose (Optional for Postgres/Redis; local SQLite works out of the box)

---

### 2. Backend Setup
```bash
# 1. Navigate to API directory
cd apps/api

# 2. Create and activate virtual environment (.venv)
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

# 3. Install backend dependencies
pip install -e .

# 4. Run database migrations
alembic upgrade head

# 5. Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```
API Documentation will be available at `http://localhost:8000/docs`.

---

### 3. Frontend Setup
```bash
# 1. Navigate to Web directory
cd apps/web

# 2. Install dependencies
npm install

# 3. Start Next.js development server
npm run dev
```
Web application will be available at `http://localhost:3000`.

---

### 4. Running Infrastructure Services (Optional)
```bash
# From workspace root
docker compose up -d
```

---

### 5. Running Tests
```bash
# Backend tests
cd apps/api
pytest tests -v

# Frontend build & typecheck
cd apps/web
npm run build
```
