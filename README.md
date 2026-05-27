# Web Crawler + Blog CMS

Web 上の記事を自動収集して Next.js でブログ表示するシステム。
24/7 のサーバを持たず、無料枠のクラウドだけで動く構成。

## アーキテクチャ

```
            ┌────────────────────────────────────┐
            │  Vercel — Next.js                  │
            │  - Auth0 session                   │
            │  - Drizzle → Neon                  │
            │  - Server Actions → Render API     │
            └────┬──────────────────────┬────────┘
                 │ reads/writes         │ queues crawl
                 ▼                 ▼
              ┌──────┐         ┌────────────────┐
              │ Neon │◀───────│ Render FastAPI │
              │  PG  │ writes │ crawler worker │
              └──┬───┘        └───────┬────────┘
                 │ reads              │ writes raw_html/images
                 ▼                    ▼
              Browser           Cloudflare R2
```

| 層 | 採用 |
|---|---|
| Compute (crawler/API) | Render FastAPI |
| Database | Neon PostgreSQL(serverless、`sslmode=require`) |
| Storage | Cloudflare R2(`raw_html` と取得画像のバイナリ) |
| Frontend | Vercel 上の Next.js(Drizzle で Neon に直接アクセス) |
| Auth | Auth0 + access code invite |

## ディレクトリ

```
web_crawler/
├── backend/                FastAPI + Python crawler (run on Render/local)
│   ├── alembic/            schema migrations (source-of-truth)
│   └── src/
│       ├── crawler/        static / dynamic (Playwright)
│       ├── parser/         HTML → article + url canonicalization
│       ├── scheduler/      job_manager (BFS) + rate_limiter + robots
│       ├── storage/        R2 client + image fetcher
│       ├── db/             SQLAlchemy models + repository
│       ├── scripts/        one-shot maintenance (raw_html → R2 migration)
│       └── cli.py          add-target / list-targets / crawl / crawl-target
├── frontend/               Next.js (App Router, RSC + Server Actions)
│   └── src/
│       ├── app/            pages + Server Actions
│       ├── components/
│       └── db/             Drizzle schema + queries
├── auth0-actions/          Auth0 Action samples
└── tests/                  pytest coverage
```

## クラウド初期セットアップ(Phase 0)

実行は **1 度だけ**。各サービス側で行う作業のみ書く。

### 1. Neon

1. https://console.neon.tech で project 作成
2. Connection details からコピー:
   - **Pooled** connection → `DATABASE_URL`(末尾 `?sslmode=require` 必須)
   - **Direct** connection → `MIGRATION_DATABASE_URL`(同上)

### 2. Cloudflare R2

1. R2 で bucket を作成(例: `web-crawler`)
2. Settings → Public access を **Allow Access**(画像直リンク用)→ `R2_PUBLIC_URL` を控える
3. R2 → Manage API Tokens → Create API Token
   - Permissions: `Object Read & Write`
   - Specify bucket: 上記 bucket
   - → `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY`
4. Account ID(R2 ホーム画面右側)を控える → `R2_ACCOUNT_ID`

### 3. Auth0

1. Auth0 で Regular Web Application を作成
2. Callback URL に `https://<your-vercel-domain>/auth/callback` を追加
3. Logout URL / Web Origin に `https://<your-vercel-domain>` を追加
4. Database connection と Google social connection を有効化
5. `auth0-actions/` の 2 つの Action を設定し、`BACKEND_API_URL` と `BACKEND_API_TOKEN` を secrets に登録

### 4. Secrets / Env vars 登録

**Render Environment Variables**:
| Secret | 用途 |
|---|---|
| `DATABASE_URL` | Neon pooled |
| `MIGRATION_DATABASE_URL` | Neon direct |
| `BACKEND_API_TOKEN` | Vercel/Auth0 Actions からの内部 API 保護 |
| `INVITE_CODE_PEPPER` | access code hash 用 |
| `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET` / `R2_PUBLIC_URL` | R2 |

**Vercel Project Settings → Environment Variables**(Production / Preview):
| Variable | 用途 |
|---|---|
| `DATABASE_URL` | Neon pooled(Server Components / Server Actions) |
| `R2_PUBLIC_URL` | `next/image` の `remotePatterns` 用 |
| `BACKEND_API_URL` / `BACKEND_API_TOKEN` | Render API 呼び出し |
| `AUTH0_SECRET` / `APP_BASE_URL` / `AUTH0_DOMAIN` / `AUTH0_CLIENT_ID` / `AUTH0_CLIENT_SECRET` | Auth0 SDK |

> ⚠️ どれも **`NEXT_PUBLIC_` プレフィックスを付けないこと**。ブラウザに secret が漏れる。

### Auth0 + Access code

このアプリは Auth0 でログインし、Neon 側の `users.id` を使って
`articles` / `crawl_targets` / `crawl_jobs` をユーザーごとに分離する。
不特定多数の登録を避けるため、先に `/register` で email + access code を
検証したユーザーだけ Auth0 の signup / Google 初回ログインへ進める。
検証済み invite は 15 分以内に Auth0 側で消費される必要がある。

**Vercel env**:
| Variable | 用途 |
|---|---|
| `AUTH0_SECRET` | Auth0 SDK session cookie 暗号化用。`openssl rand -hex 32` 推奨 |
| `APP_BASE_URL` | Vercel app URL。local は `http://localhost:3000` |
| `AUTH0_DOMAIN` / `AUTH0_CLIENT_ID` / `AUTH0_CLIENT_SECRET` | Auth0 application credentials |
| `AUTH0_AUDIENCE` / `AUTH0_SCOPE` | API access token が必要な場合に指定 |
| `BACKEND_API_URL` | Render の FastAPI URL |
| `BACKEND_API_TOKEN` | Vercel -> Render と Auth0 Actions -> Render の共有 secret |

**Render env**:
| Variable | 用途 |
|---|---|
| `DATABASE_URL` / `MIGRATION_DATABASE_URL` | Neon 接続 |
| `BACKEND_API_TOKEN` | 内部 API token 検証 |
| `INVITE_CODE_PEPPER` | access code hash の pepper |
| `AUTH0_BOOTSTRAP_SUB` / `BOOTSTRAP_USER_EMAIL` | migration で既存データを割り当てる初期管理者 |

Auth0 dashboard では callback/logout URL に `/auth/callback` と app origin を
設定する。Auth0 Actions には `auth0-actions/pre-user-registration.js` と
`auth0-actions/post-login.js` を登録し、Action secrets に
`BACKEND_API_URL` と `BACKEND_API_TOKEN` を入れる。

access code は CLI で発行する。code は一度しか表示されず、DB には hash のみ保存される。

```bash
docker compose exec backend python -m src.cli create-invite user@example.com --days 7
```

### 5. 初回 schema 適用

```bash
cd backend
alembic upgrade head
```

`AUTH0_BOOTSTRAP_SUB` と `BOOTSTRAP_USER_EMAIL` を設定してから実行する。既存の articles / crawl_targets / crawl_jobs はこの初期管理者に割り当てられる。

### 6. Vercel デプロイ

repo を Vercel project に接続するだけ。`main` ブランチ push で auto-deploy。

## 運用

### クロールターゲットを追加

ローカルで CLI 経由(認証不要):
```bash
docker compose --profile local-db up -d db
docker compose run backend python -m src.cli add-target \
    "https://blog.example.com" \
    --mode static \
    --keywords "AI,LLM" \
    --schedule "0 */6 * * *"
```

または Vercel デプロイ後、フロントの `/targets` ページから追加。

### クロール起動

- **手動(全ターゲット)**: `/targets` ページの **Crawl Now** ボタン
- **手動(個別)**: `/targets` の各行にある **Crawl this** ボタン

どちらも Vercel Server Action から Render の FastAPI を呼び出す。
Render backend は `BACKEND_API_TOKEN` で保護され、ログインユーザーの
`user_id` に紐づく target だけをクロールする。

### スキーマ変更

1. `backend/alembic/versions/` に migration 追加
2. ローカルで動作確認: `docker compose run backend alembic upgrade head`(local Postgres)
3. `backend` で pytest、`frontend` で `npx tsc --noEmit` と `npm run build`
4. Render shell または CI/CD の migration step で `alembic upgrade head` を実行

## ローカル開発

```bash
cp .env.example .env
# .env で DATABASE_URL / R2_* を実値に書き換え (R2 は省略可、ただし raw_html は破棄される)

docker compose --profile local-db up -d db   # Local Postgres
docker compose up -d backend frontend         # Dev shell + hot-reload Next.js

# Crawler を 1 回実行
docker compose exec backend python -m src.cli crawl

# Tests
docker compose exec backend pytest -v

# Frontend
open http://localhost:3000
```

## CLI

```bash
docker compose exec backend python -m src.cli <command>

# add-target <url>           クロールターゲットを追加 / 再活性化
# list-targets               アクティブなターゲット一覧
# crawl                      全アクティブターゲットをクロール
# crawl-target <UUID>        特定ターゲット 1 件をクロール
# create-invite <email>      access code invite を作成
```

## 既存データを R2 に移行する(初回のみ)

`articles.raw_html` 列が DB に残っている既存環境でクラウドへ切り替える時:

```bash
# 1. R2 keys を環境変数にセット
# 2. dry-run で移行対象を確認
docker compose exec backend python -m src.scripts.migrate_raw_html_to_r2

# 3. 実行
docker compose exec backend python -m src.scripts.migrate_raw_html_to_r2 --apply

# 4. R2 への upload を確認したら、列削除 migration を適用
docker compose exec backend alembic upgrade head
```

スクリプトは冪等(`raw_html_r2_key IS NULL` の行のみ処理)。

## ライセンス / 注意

- robots.txt の `Disallow` は `src/scheduler/robots.py` で尊重
- `User-Agent: WebCrawlerBot/1.0` を送信
- レート制限: token bucket(default `1.0 req/s`、capacity 5)
- 商用利用やスクレイピング規約のある対象には別途利用可否を確認すること
