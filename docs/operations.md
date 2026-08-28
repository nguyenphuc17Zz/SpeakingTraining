# Operations & Deployment Guide

## 1. Quickstart Development Setup
```bash
# 1. Start Docker services (PostgreSQL & Redis)
docker-compose up -d

# 2. Backend Setup
cd apps/api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Run preflight verification
python scripts/preflight.py

# Start FastAPI backend
uvicorn app.main:app --reload --port 8000

# 3. Frontend Setup
cd ../web
npm install
npm run dev
```

---

## 2. Backup & Disaster Recovery
- **Database Backup**:
  ```bash
  pg_dump -U postgres speaking_training > backup_speaking_training.sql
  ```
- **Database Restore**:
  ```bash
  psql -U postgres -d speaking_training < backup_speaking_training.sql
  ```
- **Reconstruction Hierarchy**:
  - *Cache Lost* ➔ Automatically rebuilt from database records.
  - *Analytics Snapshots Lost* ➔ Recalculated from raw session turns and exercise attempts.
  - *Game Profile Desynchronized* ➔ Reconstructed from immutable `XPTransaction` ledger entries.
