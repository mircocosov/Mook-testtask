# Wishlist Monorepo

## Stack
- `apps/web`: Next.js 14 (Pages Router) + TypeScript + SCSS modules.
- `apps/api`: FastAPI + SQLAlchemy 2 + Alembic.
- PostgreSQL via Docker Compose.
- Realtime: per-wishlist WebSocket channel.

## Product decisions
1. **Сюрприз-конфиденциальность:** owner API возвращает только агрегаты `reserved: bool` и `contributed_amount`, без guest identifiers.
2. **Soft delete:** item архивируется (`status=archived`) вместо hard delete.
3. **Guest identity:** подписанный `guest_token` cookie, без обязательной регистрации.
4. **Анти-абьюз:** простой sliding-window rate limit для unfurl/reserve/contribute.
5. **Складчина:** вклад минимум 1 EUR/USD (100 cents); превышение цели запрещено.
6. **Realtime:** WS `/ws/wishlists/{public_id}` + fallback polling в web-клиенте.

## Local run
```bash
# 1) DB
docker compose up -d

# 2) API
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
uvicorn app.main:app --reload --app-dir src

# 3) Web (new terminal)
cd apps/web
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Env vars
### apps/api/.env
- `SECRET_KEY`
- `GUEST_TOKEN_SECRET`
- `DATABASE_URL`
- `FRONTEND_URL`

### apps/web/.env.local
- `NEXT_PUBLIC_API_URL`

## Deploy guide (repeatable)
- DB: Neon Postgres
- API: Render Web Service (`uvicorn app.main:app --app-dir src --host 0.0.0.0 --port $PORT`)
- Web: Vercel (env: `NEXT_PUBLIC_API_URL=https://<api-domain>`)
- Run Alembic migrations on deploy: `alembic upgrade head`

## Seed demo (optional)
Create owner + wishlist + items by using API endpoints from `/docs`.
