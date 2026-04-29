# Web Crawler + Blog CMS

Web 上の記事を自動収集して Next.js でブログ表示するシステム。
24/7 のサーバを持たず、無料枠のクラウドだけで動く構成。

## アーキテクチャ

```
            ┌────────────────────────────────────┐
            │  GitHub Actions                    │
            │  - crawl.yml   (cron 6h + manual)  │
            │  - migrate.yml (manual)            │
            │  - test.yml    (PR / push)         │
            └────┬─────────────────┬─────────────┘
                 │ writes          │ writes (raw_html, images)
                 ▼                 ▼
              ┌──────┐         ┌────────────────┐
              │ Neon │         │ Cloudflare R2  │
              │  PG  │         │ (S3-compat)    │
              └──┬───┘         └────────┬───────┘
                 │ reads                │ public GET
                 ▼                      │
              ┌────────────────────────────────┐
              │ Vercel — Next.js               │
              │ - RSC: Drizzle → Neon          │
              │ - Server Actions:              │
              │   triggerCrawl(target?)        │
              │   → workflow_dispatch          │
              └────────────┬───────────────────┘
                           ▼ Browser
```

| 層 | 採用 |
|---|---|
| Compute (crawler) | GitHub Actions(cron + workflow_dispatch) |
| Database | Neon PostgreSQL(serverless、`sslmode=require`) |
| Storage | Cloudflare R2(`raw_html` と取得画像のバイナリ) |
| Frontend & API | Vercel 上の Next.js(Drizzle で Neon に直接アクセス) |

## ディレクトリ

```
web_crawler/
├── backend/                Python crawler (run on GH Actions)
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
└── .github/workflows/      crawl.yml / migrate.yml / test.yml
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

### 3. GitHub PAT

1. GitHub → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new
2. Repository access: this repo only
3. Permissions: `Actions: Read and write`(これだけ)
4. Expiration: 90 days
5. 生成された token を `GH_DISPATCH_TOKEN` として控える

### 4. Secrets / Env vars 登録

**GitHub repo Settings → Secrets and variables → Actions**:
| Secret | 用途 |
|---|---|
| `DATABASE_URL` | Neon pooled (`crawl.yml`) |
| `MIGRATION_DATABASE_URL` | Neon direct (`migrate.yml`) |
| `R2_ACCOUNT_ID` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET` / `R2_PUBLIC_URL` | R2 (`crawl.yml`) |

**Vercel Project Settings → Environment Variables**(Production / Preview):
| Variable | 用途 |
|---|---|
| `DATABASE_URL` | Neon pooled(Server Components / Server Actions) |
| `R2_PUBLIC_URL` | `next/image` の `remotePatterns` 用 |
| `GH_OWNER` / `GH_REPO` | GitHub `workflow_dispatch` API |
| `GH_DISPATCH_TOKEN` | 同上 |

> ⚠️ どれも **`NEXT_PUBLIC_` プレフィックスを付けないこと**。ブラウザに secret が漏れる。

### 5. 初回 schema 適用

```bash
gh workflow run migrate.yml
```

または GitHub UI: Actions タブ → migrate → Run workflow。`alembic upgrade head` が走り、Neon に articles / authors / categories / tags / article_tags / crawl_targets / crawl_jobs が出来る。

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

- **自動**: `.github/workflows/crawl.yml` の `schedule: 0 */6 * * *` で 6 時間ごと
- **手動(全ターゲット)**: `/targets` ページの **Crawl Now** ボタン
- **手動(個別)**: `/targets` の各行にある **Crawl this** ボタン

どちらも内部的に `workflow_dispatch` で `crawl.yml` を起動する。進捗は GitHub Actions タブで確認。

### スキーマ変更

1. `backend/alembic/versions/` に migration 追加
2. ローカルで動作確認: `docker compose run backend alembic upgrade head`(local Postgres)
3. PR を作成 → `test.yml` が pytest + tsc + next build を回す
4. main にマージ後、Actions UI から `migrate.yml` を `workflow_dispatch` で実行

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
