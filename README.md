# Web Crawler + Blog CMS

ブログ記事データを自動収集し、CMS として配信するシステム。

## 技術スタック

- **Frontend**: Next.js (React / TypeScript)
- **Backend**: Python (FastAPI + Crawler)
- **Database**: PostgreSQL 16
- **インフラ**: Docker Compose (3コンテナ)

## セットアップ

```bash
# 環境変数を設定
cp .env.example .env

# Docker Compose で起動
docker compose up --build
```

## アクセス

| サービス | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

## CLI コマンド

```bash
# クロールターゲットを追加
docker compose exec backend python -m src.cli add-target "https://blog.example.com" --mode static

# SPA サイトを動的クロール
docker compose exec backend python -m src.cli add-target "https://spa-site.io" --mode dynamic

# ターゲット一覧を表示
docker compose exec backend python -m src.cli list-targets

# 全ターゲットをクロール
docker compose exec backend python -m src.cli crawl
```

## API エンドポイント

| Method | Path | 説明 |
|---|---|---|
| GET | /health | ヘルスチェック |
| GET | /api/articles | 記事一覧（ページネーション） |
| GET | /api/articles/{slug} | 記事詳細 |
| GET | /api/categories | カテゴリ一覧 |
| GET | /api/articles?category={slug} | カテゴリ別記事 |
| POST | /api/crawl | クロール実行トリガー |

## テスト

```bash
cd backend
pip install -r requirements.txt
pytest ../tests -v
```

## AWS RDS への移行

`.env` の DB 接続情報を変更するだけ:

```dotenv
DB_HOST=my-crawler.xxxxxxxxxxxx.us-east-1.rds.amazonaws.com
DB_PASSWORD=<rds-password>
```
