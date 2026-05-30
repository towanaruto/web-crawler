# Crawl Scheduler Worker

Cloudflare Cron Trigger that wakes the Render backend every 5 minutes and asks
it to enqueue due crawl targets.

## Deploy

```bash
cd cloudflare/scheduler-worker
npx wrangler secret put BACKEND_API_URL
npx wrangler secret put BACKEND_API_TOKEN
npx wrangler deploy
```

`BACKEND_API_URL` should be the Render FastAPI origin, for example
`https://your-service.onrender.com`. `BACKEND_API_TOKEN` must match the
backend/Vercel internal API token.
