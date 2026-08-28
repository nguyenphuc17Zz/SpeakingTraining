# Environment Configuration

This project manages configuration via environment variables declared in `.env` (derived from `.env.example`).

| Variable | Description | Default | Example |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | Runtime environment (`development`, `production`, `test`) | `development` | `development` |
| `APP_NAME` | Name of the application | `"Japanese Speaking AI Training OS"` | `"Japanese Speaking AI Training OS"` |
| `DEBUG` | Enable debug logs & reloaders | `true` | `true` |
| `API_HOST` | API bind address | `127.0.0.1` | `0.0.0.0` |
| `API_PORT` | API bind port | `8000` | `8000` |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | `http://localhost:3000,http://127.0.0.1:3000` | `http://localhost:3000` |
| `DATABASE_URL` | Async database connection URL | `sqlite+aiosqlite:///./speaking_training.db` | `postgresql+asyncpg://postgres:pass@localhost:5432/speaking_training` |
| `DATABASE_SYNC_URL` | Sync database connection URL (for Alembic migrations) | `sqlite:///./speaking_training.db` | `postgresql://postgres:pass@localhost:5432/speaking_training` |
| `REDIS_URL` | Redis server connection URL | `redis://localhost:6379/0` | `redis://localhost:6379/0` |
| `ENCRYPTION_KEY` | 32-byte urlsafe base64 key for encrypting secrets at rest | (Required) | `dGhpc19pc19hXzMyX2J5dGVfZmZXcm5ldF9rZXkxMjM0NTY=` |
| `NEXT_PUBLIC_API_URL` | Frontend public API base URL | `http://127.0.0.1:8000/api/v1` | `http://127.0.0.1:8000/api/v1` |

> [!WARNING]
> Never commit `.env` containing production credentials to version control.
