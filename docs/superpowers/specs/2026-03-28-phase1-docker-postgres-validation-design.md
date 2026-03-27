# Phase 1 設計: Docker + PostgreSQL + Pydanticバリデーション

## 概要

既存のjob-data-platformプロジェクトに、以下の3つを追加する:

1. **Docker化** — docker-composeでPostgreSQL + FastAPIをローカルで動かす
2. **PostgreSQLへの移行** — MongoDBからPostgreSQLに切り替え、SQLAlchemyで接続
3. **Pydanticバリデーション** — LLM出力をPostgreSQLに入れる前にスキーマ検証

本番（Azure）移行はPhase 1のスコープ外。ローカルで動作確認できることがゴール。

## 目的（習得スキル）

- SQL, PostgreSQL, スキーマ設計, 正規化
- Docker, docker-compose
- データバリデーション（Pydantic）
- SQLAlchemy（PythonのORM）
- データパイプラインの品質管理

## 全体アーキテクチャ

### 変更前

```
スクレイピング(01-04) → LLM変換(05) → MongoDB投入(06) → FastAPI(pymongo) → Azure
```

### 変更後

```
スクレイピング(01-04)
    ↓
LLM変換(05)
    ↓
Pydanticバリデーション(05.5)  ← 新規
    ↓
PostgreSQL投入(06)            ← 変更
    ↓
FastAPI(SQLAlchemy)           ← 変更
    ↓
ローカルで動作確認(docker-compose)
```

### 実行環境の分離

```
Mac上で直接実行:   01 → 02 → 03 → 04 → 05 → 05.5(検証) → 06
                                                           ↓
Docker内:                                          db(PostgreSQL) ← web(FastAPI)
```

パイプラインスクリプト（01〜06）はMac上で直接実行。PostgreSQLにはDocker外からポート5432で接続。

## Docker構成

### docker-compose.yml

```yaml
services:
  db:
    image: postgres:16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: job_data_platform
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - pgdata:/var/lib/postgresql/data

  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/job_data_platform

volumes:
  pgdata:
```

### Dockerfile (FastAPIアプリ用)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## PostgreSQLスキーマ設計

### jobsテーブル

| カラム | 型 | 制約 | 説明 |
|-------|---|------|------|
| id | SERIAL | PRIMARY KEY | 自動採番ID |
| url | TEXT | UNIQUE NOT NULL | upsertのキー |
| company_name | TEXT | | 会社名 |
| company_website_url | TEXT | | 企業サイトURL |
| job_title_raw | TEXT | | 元の求人タイトル |
| job_title_ja | TEXT | | 正規化された求人タイトル |
| job_summary_ja | TEXT | | 求人サマリー |
| job_description_ja | TEXT | | 求人詳細 |
| job_category | TEXT | | 職種カテゴリ |
| job_role | TEXT | | エンジニアロール |
| employment_type | TEXT | | 雇用形態 |
| remote_type | TEXT | | リモート勤務区分 |
| work_location_type | TEXT | | 勤務地タイプ |
| work_location_detail | TEXT | | 勤務地詳細 |
| salary_min | INTEGER | | 最低年収（万円） |
| salary_max | INTEGER | | 最高年収（万円） |
| salary_note | TEXT | | 給与補足 |
| original_language | TEXT | | 元の言語 |
| created_at | TIMESTAMP | DEFAULT NOW() | 作成日時 |
| updated_at | TIMESTAMP | DEFAULT NOW() | 更新日時 |

### job_technologiesテーブル（正規化）

| カラム | 型 | 制約 | 説明 |
|-------|---|------|------|
| id | SERIAL | PRIMARY KEY | 自動採番ID |
| job_id | INTEGER | REFERENCES jobs(id) | 外部キー |
| technology | TEXT | | 技術名 |
| | | UNIQUE(job_id, technology) | 重複防止 |

正規化の理由: technologiesは1求人に複数あるため（1対多の関係）、別テーブルに分離する。

## Pydanticバリデーション設計

### 配置

`validators/job_validator.py`

### バリデーションモデル

- `JobRecord` — LLM出力の全フィールドを検証
- `SalaryModel` — salary内のmin/max/noteを検証
- `WorkLocationModel` — work_location内のtype/detailを検証

### Enumによる許可リスト

- `JobCategory` — 13種類（エンジニア, データ分析活用, etc.）
- `EmploymentType` — 5種類（正社員, 契約社員, etc.）
- `RemoteType` — 3種類（フルリモート, 一部リモート, 出社）

### バリデーションフロー

```
LLM出力(JSON)
    ↓
JobRecord.model_validate(data)
    ↓ OK → PostgreSQLに保存
    ↓ NG → エラーログ(JSONL)に記録してスキップ
```

### 自動変換

- 文字列の数値 → 整数に自動変換（例: salary.min: "500" → 500）

### エラー処理

バリデーション失敗データは `05_validation_errors.jsonl` に記録:
- 元のURL
- エラー内容（どのフィールドが不正か）
- 元のデータ

## 変更対象ファイル一覧

| ファイル | 変更種別 | 内容 |
|---------|---------|------|
| `docker-compose.yml` | 新規 | PostgreSQL + FastAPIコンテナ定義 |
| `Dockerfile` | 新規 | FastAPIアプリ用コンテナ定義 |
| `.dockerignore` | 新規 | Docker不要ファイルの除外 |
| `app/models.py` | 新規 | SQLAlchemyテーブル定義 |
| `app/db.py` | 変更 | pymongo → SQLAlchemy + PostgreSQL |
| `app/main.py` | 変更 | MongoDBクエリ → SQLクエリ |
| `validators/job_validator.py` | 新規 | Pydanticバリデーションモデル |
| `06_import_to_postgres.py` | 新規 | バリデーション済みデータのPostgreSQLインポート |
| `06_migrate_from_mongo.py` | 新規 | MongoDB→PostgreSQL移行スクリプト |
| `requirements.txt` | 変更 | sqlalchemy, psycopg2-binary, pydantic追加 |
| `.env.example` | 新規 | 環境変数のテンプレート |

## データ移行

MongoDBの既存データ（LLM構造化済み）も移行する。求人ページの掲載が消えていても、データ自体は分析に活用できるため。

移行フロー:
1. MongoDBからデータをエクスポート
2. Pydanticバリデーションを通す
3. PostgreSQLにインポート

## スコープ外

- 本番（Azure App Service + Azure Database for PostgreSQL）への移行
- Green Japanスクレイピングの拡張
- Airflow等のワークフロー管理（Phase 2）
