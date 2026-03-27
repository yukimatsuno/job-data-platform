# Phase 1: Docker + PostgreSQL + Pydanticバリデーション 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** MongoDBをPostgreSQLに置き換え、Docker環境でローカル動作させ、Pydanticバリデーションをパイプラインに追加する

**Architecture:** docker-composeでPostgreSQL + FastAPIの2コンテナ構成。パイプラインスクリプト（01〜06）はMac上で直接実行し、Dockerコンテナ内のPostgreSQLにポート5432経由で接続。LLM出力はPydanticで検証してからPostgreSQLに投入。

**Tech Stack:** Python 3.11, PostgreSQL 16, Docker/docker-compose, SQLAlchemy, Pydantic v2, FastAPI

---

## ファイル構成

### 新規作成
| ファイル | 役割 |
|---------|------|
| `docker-compose.yml` | PostgreSQL + FastAPIコンテナ定義 |
| `Dockerfile` | FastAPIアプリ用コンテナ |
| `.dockerignore` | Dockerビルドから除外するファイル |
| `.env.example` | 環境変数テンプレート（Git管理用） |
| `app/models.py` | SQLAlchemyテーブル定義（jobs, job_technologies） |
| `validators/job_validator.py` | Pydanticバリデーションモデル |
| `validators/__init__.py` | パッケージ初期化 |
| `06_import_to_postgres.py` | LLM出力 → バリデーション → PostgreSQLインポート |
| `06_migrate_from_mongo.py` | MongoDB既存データ → PostgreSQL移行 |
| `tests/test_validator.py` | バリデーションのテスト |
| `tests/__init__.py` | パッケージ初期化 |

### 変更
| ファイル | 変更内容 |
|---------|---------|
| `requirements.txt` | sqlalchemy, psycopg2-binary, pydantic, alembic追加 |
| `app/db.py` | pymongo → SQLAlchemy + PostgreSQL |
| `app/main.py` | MongoDBクエリ → SQLAlchemyクエリ |
| `templates/jobs.html` | `job._id` → `job.id`, `job.work_location.type` → `job.work_location_type` 等 |
| `templates/job_detail.html` | 同上 |
| `.gitignore` | `__pycache__/`, `.pytest_cache/` 追加 |

---

## Task 1: Docker環境の構築

**Files:**
- Create: `docker-compose.yml`
- Create: `Dockerfile`
- Create: `.dockerignore`
- Create: `.env.example`
- Modify: `.gitignore`

- [ ] **Step 1: .env.exampleを作成する**

`.env.example` はGitに入れて、プロジェクトに必要な環境変数を他の開発者（や将来の自分）に伝えるテンプレートです。実際の値は `.env`（Gitに入れない）に書きます。

```
# PostgreSQL（docker-compose用）
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/job_data_platform

# MongoDB（移行スクリプト用。移行後は不要）
MONGO_URI=mongodb+srv://...
DB_NAME=job_data_platform
COLLECTION_NAME=herp
```

- [ ] **Step 2: docker-compose.ymlを作成する**

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
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://postgres:postgres@db:5432/job_data_platform

volumes:
  pgdata:
```

`healthcheck`は「PostgreSQLが本当に起動完了したか」を確認する仕組みです。`depends_on`だけだとコンテナが起動しただけでDBがまだ準備中のことがあり、FastAPIが接続エラーになります。

- [ ] **Step 3: Dockerfileを作成する**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY templates/ ./templates/
COPY static/ ./static/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

プロジェクト全体（`COPY . .`）ではなく、必要なディレクトリだけをコピーしています。CSVやJSONなどの大きなデータファイルをコンテナに入れないためです。

- [ ] **Step 4: .dockerignoreを作成する**

```
.venv/
__pycache__/
*.csv
*.json
*.jsonl
data/
.git/
.env
*.ipynb
firebase-debug.log
docs/
```

`.dockerignore`は`.gitignore`のDocker版です。`docker build`時にこれらのファイルをコンテナに送らないようにします。

- [ ] **Step 5: .gitignoreにDocker・Python関連を追加する**

`.gitignore`の末尾に以下を追加:

```
# Python
__pycache__/
.pytest_cache/

# Docker
pgdata/
```

- [ ] **Step 6: PostgreSQLコンテナの起動を確認する**

Run:
```bash
docker-compose up db -d
```

PostgreSQLコンテナだけを起動。`-d`はバックグラウンド実行。

Expected: コンテナが起動し、ポート5432でPostgreSQLが利用可能になる。

確認:
```bash
docker-compose ps
```

Expected: `db`コンテナが`running (healthy)`と表示される。

- [ ] **Step 7: PostgreSQLに接続できることを確認する**

Run:
```bash
docker-compose exec db psql -U postgres -d job_data_platform -c "SELECT 1;"
```

Expected:
```
 ?column?
----------
        1
(1 row)
```

`psql`はPostgreSQLのコマンドラインツールです。`SELECT 1`はDBが動いているかの最もシンプルな確認方法です。

- [ ] **Step 8: コミット**

```bash
git add docker-compose.yml Dockerfile .dockerignore .env.example .gitignore
git commit -m "feat: add Docker environment with PostgreSQL and FastAPI containers"
```

---

## Task 2: requirements.txtの更新とPython依存関係インストール

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: requirements.txtを更新する**

```
fastapi
uvicorn
jinja2
python-dotenv
sqlalchemy
psycopg2-binary
pydantic
pytest
```

削除: `pymongo`, `dnspython`（PostgreSQL移行後は不要）
追加: `sqlalchemy`, `psycopg2-binary`, `pydantic`, `pytest`

注意: `pymongo`は移行スクリプト（`06_migrate_from_mongo.py`）で使うので、ローカルの`.venv`には残しておきます。ただし`requirements.txt`（= 本番依存）からは削除します。

- [ ] **Step 2: ローカル環境にインストール**

Run:
```bash
source .venv/bin/activate && pip install sqlalchemy psycopg2-binary pydantic pytest pymongo dnspython
```

ローカルには`pymongo`もインストール（移行スクリプト用）。`requirements.txt`には本番に必要なものだけ記載。

- [ ] **Step 3: コミット**

```bash
git add requirements.txt
git commit -m "feat: update dependencies for PostgreSQL + Pydantic stack"
```

---

## Task 3: Pydanticバリデーションモデルの作成

**Files:**
- Create: `validators/__init__.py`
- Create: `validators/job_validator.py`
- Create: `tests/__init__.py`
- Create: `tests/test_validator.py`

- [ ] **Step 1: validators/__init__.pyを作成する**

空ファイルを作成。Pythonにこのディレクトリがパッケージであることを伝えます。

```python
```

（空ファイル）

- [ ] **Step 2: テストファイルの準備**

`tests/__init__.py`を空ファイルで作成。

```python
```

`tests/test_validator.py`に失敗するテストを書く:

```python
import pytest
from validators.job_validator import JobRecord


class TestJobRecordValidation:
    """正常なデータがバリデーションを通過するテスト"""

    def test_valid_full_record(self):
        """全フィールドが正しいデータ → バリデーション通過"""
        data = {
            "url": "https://herp.careers/careers/companies/test/jobs/001",
            "company_name": "株式会社テスト",
            "company_website_url": "https://test.co.jp",
            "job_title_raw": "バックエンドエンジニア",
            "job_title_ja": "バックエンドエンジニア",
            "job_summary_ja": "バックエンド開発をリードするポジションです",
            "job_description_ja": "Go言語を用いたAPIの設計・開発を担当していただきます。",
            "job_category": "エンジニア",
            "job_role": "バックエンドエンジニア",
            "employment_type": "正社員",
            "remote_type": "フルリモート",
            "work_location": {"type": "フルリモート", "detail": None},
            "salary": {"min": 500, "max": 800, "note": None},
            "technologies": ["Go", "PostgreSQL", "Docker"],
            "original_language": "ja",
        }
        record = JobRecord.model_validate(data)
        assert record.url == data["url"]
        assert record.company_name == "株式会社テスト"
        assert record.salary.min == 500
        assert record.salary.max == 800
        assert record.technologies == ["Go", "PostgreSQL", "Docker"]

    def test_minimal_record(self):
        """URLだけ（必須フィールドのみ）→ バリデーション通過"""
        data = {"url": "https://herp.careers/careers/companies/test/jobs/002"}
        record = JobRecord.model_validate(data)
        assert record.url == data["url"]
        assert record.company_name is None
        assert record.technologies == []

    def test_salary_string_coercion(self):
        """salary.minが文字列 "500" → 整数500に自動変換"""
        data = {
            "url": "https://herp.careers/careers/companies/test/jobs/003",
            "salary": {"min": "500", "max": "800"},
        }
        record = JobRecord.model_validate(data)
        assert record.salary.min == 500
        assert record.salary.max == 800

    def test_invalid_job_category(self):
        """許可リスト外のjob_category → バリデーションエラー"""
        data = {
            "url": "https://herp.careers/careers/companies/test/jobs/004",
            "job_category": "エンジニアリング",  # 許可リストにない
        }
        with pytest.raises(Exception):
            JobRecord.model_validate(data)

    def test_invalid_employment_type(self):
        """許可リスト外のemployment_type → バリデーションエラー"""
        data = {
            "url": "https://herp.careers/careers/companies/test/jobs/005",
            "employment_type": "派遣社員",  # 許可リストにない
        }
        with pytest.raises(Exception):
            JobRecord.model_validate(data)

    def test_invalid_remote_type(self):
        """許可リスト外のremote_type → バリデーションエラー"""
        data = {
            "url": "https://herp.careers/careers/companies/test/jobs/006",
            "remote_type": "ハイブリッド",  # 許可リストにない
        }
        with pytest.raises(Exception):
            JobRecord.model_validate(data)

    def test_missing_url(self):
        """URLなし → バリデーションエラー（必須フィールド）"""
        data = {"company_name": "株式会社テスト"}
        with pytest.raises(Exception):
            JobRecord.model_validate(data)

    def test_technologies_empty_list(self):
        """technologiesが空リスト → OK"""
        data = {
            "url": "https://herp.careers/careers/companies/test/jobs/007",
            "technologies": [],
        }
        record = JobRecord.model_validate(data)
        assert record.technologies == []

    def test_null_optional_fields(self):
        """Optionalフィールドがnull → OK"""
        data = {
            "url": "https://herp.careers/careers/companies/test/jobs/008",
            "company_name": None,
            "job_category": None,
            "salary": None,
            "work_location": None,
        }
        record = JobRecord.model_validate(data)
        assert record.company_name is None
        assert record.job_category is None
        assert record.salary is None
```

- [ ] **Step 3: テストを実行して失敗を確認する**

Run:
```bash
cd /Users/matsunoyuki/code/yukimatsuno/job-data-platform && python -m pytest tests/test_validator.py -v
```

Expected: `ModuleNotFoundError: No module named 'validators.job_validator'` で全テスト失敗。

- [ ] **Step 4: validators/job_validator.pyを実装する**

```python
from pydantic import BaseModel
from typing import Optional
from enum import Enum


class JobCategory(str, Enum):
    ENGINEER = "エンジニア"
    DATA = "データ分析活用"
    QA = "QA・品質保証"
    DESIGN = "デザイン"
    PM = "PM・ディレクション"
    MARKETING = "マーケティング・商品開発"
    SALES = "セールス・事業開発"
    CS = "カスタマーサクセス・サポート"
    CXO = "経営・CXO"
    CORPORATE = "コーポレート"
    CONSULTING = "コンサルティング"
    OPEN = "オープンポジション"
    OTHER = "その他"


class EmploymentType(str, Enum):
    FULL_TIME = "正社員"
    CONTRACT = "契約社員"
    FREELANCE = "業務委託"
    PART_TIME = "アルバイト"
    INTERN = "インターン"


class RemoteType(str, Enum):
    FULL_REMOTE = "フルリモート"
    PARTIAL = "一部リモート"
    ONSITE = "出社"


class SalaryModel(BaseModel):
    min: Optional[int] = None
    max: Optional[int] = None
    note: Optional[str] = None


class WorkLocationModel(BaseModel):
    type: Optional[str] = None
    detail: Optional[str] = None


class JobRecord(BaseModel):
    url: str
    company_name: Optional[str] = None
    company_website_url: Optional[str] = None
    job_title_raw: Optional[str] = None
    job_title_ja: Optional[str] = None
    job_summary_ja: Optional[str] = None
    job_description_ja: Optional[str] = None
    job_category: Optional[JobCategory] = None
    job_role: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    remote_type: Optional[RemoteType] = None
    work_location: Optional[WorkLocationModel] = None
    salary: Optional[SalaryModel] = None
    technologies: list[str] = []
    original_language: Optional[str] = None
```

- [ ] **Step 5: テストを実行して全て通過を確認する**

Run:
```bash
cd /Users/matsunoyuki/code/yukimatsuno/job-data-platform && python -m pytest tests/test_validator.py -v
```

Expected: 9 tests passed.

- [ ] **Step 6: コミット**

```bash
git add validators/ tests/
git commit -m "feat: add Pydantic validation models with tests for job data"
```

---

## Task 4: SQLAlchemyモデルとDB接続の構築

**Files:**
- Create: `app/models.py`
- Modify: `app/db.py`

- [ ] **Step 1: app/models.pyを作成する**

```python
from sqlalchemy import (
    Column, Integer, Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime, timezone


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    url = Column(Text, unique=True, nullable=False)
    company_name = Column(Text)
    company_website_url = Column(Text)
    job_title_raw = Column(Text)
    job_title_ja = Column(Text)
    job_summary_ja = Column(Text)
    job_description_ja = Column(Text)
    job_category = Column(Text)
    job_role = Column(Text)
    employment_type = Column(Text)
    remote_type = Column(Text)
    work_location_type = Column(Text)
    work_location_detail = Column(Text)
    salary_min = Column(Integer)
    salary_max = Column(Integer)
    salary_note = Column(Text)
    original_language = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    technologies = relationship("JobTechnology", back_populates="job",
                                cascade="all, delete-orphan")


class JobTechnology(Base):
    __tablename__ = "job_technologies"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    technology = Column(Text, nullable=False)

    job = relationship("Job", back_populates="technologies")

    __table_args__ = (
        UniqueConstraint("job_id", "technology"),
    )
```

- [ ] **Step 2: app/db.pyを書き換える**

既存の`app/db.py`（pymongo）を完全に書き換えます:

```python
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/job_data_platform",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """FastAPIのDependency Injection用。リクエストごとにセッションを作成・終了する。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: テーブル作成を確認する**

PostgreSQLコンテナが起動していることを確認してから:

Run:
```bash
cd /Users/matsunoyuki/code/yukimatsuno/job-data-platform && python -c "
from app.models import Base
from app.db import engine
Base.metadata.create_all(engine)
print('Tables created successfully')
"
```

Expected: `Tables created successfully`

確認:
```bash
docker-compose exec db psql -U postgres -d job_data_platform -c "\dt"
```

Expected:
```
              List of relations
 Schema |       Name        | Type  |  Owner
--------+-------------------+-------+----------
 public | job_technologies  | table | postgres
 public | jobs              | table | postgres
(2 rows)
```

- [ ] **Step 4: jobsテーブルの構造を確認する**

Run:
```bash
docker-compose exec db psql -U postgres -d job_data_platform -c "\d jobs"
```

Expected: 全カラム（id, url, company_name, ... , updated_at）が表示される。

- [ ] **Step 5: コミット**

```bash
git add app/models.py app/db.py
git commit -m "feat: add SQLAlchemy models and PostgreSQL connection"
```

---

## Task 5: LLM出力をPostgreSQLにインポートするスクリプト

**Files:**
- Create: `06_import_to_postgres.py`

- [ ] **Step 1: 06_import_to_postgres.pyを作成する**

```python
import json
import sys
from validators.job_validator import JobRecord
from app.models import Base, Job, JobTechnology
from app.db import engine, SessionLocal


def import_llm_outputs(input_file: str):
    """LLM出力(JSONL)をバリデーション → PostgreSQLにインポート"""

    # テーブル作成（存在しなければ）
    Base.metadata.create_all(engine)

    db = SessionLocal()

    success_count = 0
    skip_count = 0
    error_count = 0
    errors = []

    with open(input_file, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[{i}] JSON parse error: {e}")
                error_count += 1
                continue

            # Pydanticバリデーション
            try:
                record = JobRecord.model_validate(raw)
            except Exception as e:
                print(f"[{i}] Validation error: {e}")
                errors.append({
                    "line": i,
                    "url": raw.get("url", "unknown"),
                    "error": str(e),
                    "data": raw,
                })
                error_count += 1
                continue

            # 既存チェック（URLでupsert）
            existing = db.query(Job).filter(Job.url == record.url).first()
            if existing:
                # 既存レコードを更新
                existing.company_name = record.company_name
                existing.company_website_url = record.company_website_url
                existing.job_title_raw = record.job_title_raw
                existing.job_title_ja = record.job_title_ja
                existing.job_summary_ja = record.job_summary_ja
                existing.job_description_ja = record.job_description_ja
                existing.job_category = record.job_category.value if record.job_category else None
                existing.job_role = record.job_role
                existing.employment_type = record.employment_type.value if record.employment_type else None
                existing.remote_type = record.remote_type.value if record.remote_type else None
                existing.work_location_type = record.work_location.type if record.work_location else None
                existing.work_location_detail = record.work_location.detail if record.work_location else None
                existing.salary_min = record.salary.min if record.salary else None
                existing.salary_max = record.salary.max if record.salary else None
                existing.salary_note = record.salary.note if record.salary else None
                existing.original_language = record.original_language

                # technologies: 既存を削除して再作成
                existing.technologies.clear()
                for tech in record.technologies:
                    existing.technologies.append(JobTechnology(technology=tech))

                skip_count += 1
                print(f"[{i}] UPDATE: {record.url}")
            else:
                # 新規レコード作成
                job = Job(
                    url=record.url,
                    company_name=record.company_name,
                    company_website_url=record.company_website_url,
                    job_title_raw=record.job_title_raw,
                    job_title_ja=record.job_title_ja,
                    job_summary_ja=record.job_summary_ja,
                    job_description_ja=record.job_description_ja,
                    job_category=record.job_category.value if record.job_category else None,
                    job_role=record.job_role,
                    employment_type=record.employment_type.value if record.employment_type else None,
                    remote_type=record.remote_type.value if record.remote_type else None,
                    work_location_type=record.work_location.type if record.work_location else None,
                    work_location_detail=record.work_location.detail if record.work_location else None,
                    salary_min=record.salary.min if record.salary else None,
                    salary_max=record.salary.max if record.salary else None,
                    salary_note=record.salary.note if record.salary else None,
                    original_language=record.original_language,
                )
                for tech in record.technologies:
                    job.technologies.append(JobTechnology(technology=tech))
                db.add(job)
                success_count += 1
                print(f"[{i}] INSERT: {record.url}")

            # 10件ごとにコミット（大量データ時のメモリ対策）
            if i % 10 == 0:
                db.commit()

    db.commit()
    db.close()

    # エラーログ出力
    if errors:
        error_file = "05_validation_errors.jsonl"
        with open(error_file, "w", encoding="utf-8") as f:
            for err in errors:
                f.write(json.dumps(err, ensure_ascii=False) + "\n")
        print(f"\nValidation errors saved to {error_file}")

    print(f"\nImport completed: {success_count} inserted, {skip_count} updated, {error_count} errors")


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "05_llm_outputs.jsonl"
    import_llm_outputs(input_file)
```

- [ ] **Step 2: インポートを実行する**

Run:
```bash
cd /Users/matsunoyuki/code/yukimatsuno/job-data-platform && python 06_import_to_postgres.py
```

Expected: 50件（`05_llm_outputs.jsonl`の件数）がINSERTされ、`Import completed: 50 inserted, 0 updated, 0 errors` のような出力が表示される。

- [ ] **Step 3: PostgreSQLでデータを確認する**

Run:
```bash
docker-compose exec db psql -U postgres -d job_data_platform -c "SELECT COUNT(*) FROM jobs;"
```

Expected: 50（またはJSONLファイルの行数）

```bash
docker-compose exec db psql -U postgres -d job_data_platform -c "SELECT j.job_title_raw, jt.technology FROM jobs j JOIN job_technologies jt ON j.id = jt.job_id LIMIT 10;"
```

Expected: 求人タイトルと技術名がJOINで表示される。

- [ ] **Step 4: コミット**

```bash
git add 06_import_to_postgres.py
git commit -m "feat: add PostgreSQL import script with Pydantic validation"
```

---

## Task 6: FastAPI（app/main.py）をPostgreSQLに移行

**Files:**
- Modify: `app/main.py`

- [ ] **Step 1: app/main.pyを書き換える**

MongoDBクエリをSQLAlchemyクエリに完全書き換え:

```python
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import Optional
from urllib.parse import urlencode
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Base, Job, JobTechnology
from app.db import engine

# アプリ起動時にテーブルを作成（なければ）
Base.metadata.create_all(engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/hello")
def hello():
    return {"message": "Hello FastAPI"}


@app.get("/about", response_class=HTMLResponse)
def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})


@app.get("/", response_class=HTMLResponse)
def show_jobs(
    request: Request,
    limit: int = 20,
    q: Optional[str] = None,
    job_category: Optional[str] = None,
    employment_type: Optional[str] = None,
    remote_type: Optional[str] = None,
    work_location: Optional[str] = None,
    salary_min: Optional[str] = None,
    salary_max: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Job)

    if q:
        like_pattern = f"%{q}%"
        query = query.filter(
            (Job.job_title_raw.ilike(like_pattern))
            | (Job.company_name.ilike(like_pattern))
            | (Job.job_category.ilike(like_pattern))
            | (Job.job_role.ilike(like_pattern))
        )
    if job_category:
        query = query.filter(Job.job_category == job_category)
    if employment_type:
        query = query.filter(Job.employment_type == employment_type)
    if remote_type:
        if remote_type == "未設定":
            query = query.filter(
                (Job.remote_type.is_(None)) | (Job.remote_type == "")
            )
        else:
            query = query.filter(Job.remote_type == remote_type)
    if work_location:
        query = query.filter(
            (Job.work_location_type == work_location)
            | (Job.work_location_detail.ilike(f"%{work_location}%"))
        )
    if salary_min and salary_min != "":
        try:
            query = query.filter(Job.salary_min >= int(salary_min))
        except ValueError:
            pass
    if salary_max and salary_max != "":
        try:
            query = query.filter(Job.salary_max <= int(salary_max))
        except ValueError:
            pass

    skip = int(request.query_params.get("skip", 0))
    total_count = query.count()
    jobs = query.order_by(Job.id.desc()).offset(skip).limit(limit).all()

    prev_skip = max(skip - limit, 0)
    next_skip = skip + limit if (skip + limit) < total_count else None

    base_params = dict(request.query_params)
    base_params.pop("skip", None)
    base_query = urlencode(base_params)
    prev_query = base_query + ("&" if base_query else "") + f"skip={prev_skip}"
    next_query = (
        base_query + ("&" if base_query else "") + f"skip={next_skip}"
        if next_skip is not None
        else None
    )

    return templates.TemplateResponse(
        "jobs.html",
        {
            "request": request,
            "jobs": jobs,
            "skip": skip,
            "limit": limit,
            "total_count": total_count,
            "prev_skip": prev_skip,
            "next_skip": next_skip,
            "prev_query": prev_query,
            "next_query": next_query,
        },
    )


@app.get("/job/{job_id}", response_class=HTMLResponse)
def show_job_detail(request: Request, job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return HTMLResponse("Job not found", status_code=404)

    return templates.TemplateResponse(
        "job_detail.html",
        {"request": request, "job": job},
    )
```

主な変更点:
- `from bson import ObjectId` → 削除（PostgreSQLはinteger IDを使う）
- `collection.find()` → `db.query(Job).filter(...)`
- MongoDB固有の`$regex`, `$and`, `$or` → SQLAlchemyの`ilike()`, `|`, `&`
- `job_id: str` → `job_id: int`（MongoDBのObjectID → PostgreSQLのinteger ID）
- `Depends(get_db)` でリクエストごとにDBセッションを注入

- [ ] **Step 2: コミット**

```bash
git add app/main.py
git commit -m "feat: migrate FastAPI app from MongoDB to SQLAlchemy/PostgreSQL"
```

---

## Task 7: テンプレートの修正

**Files:**
- Modify: `templates/jobs.html`
- Modify: `templates/job_detail.html`

- [ ] **Step 1: templates/jobs.htmlを修正する**

以下の置換を行う:

| 変更前 | 変更後 | 理由 |
|--------|--------|------|
| `job._id` | `job.id` | MongoDBのObjectID → PostgreSQLのinteger ID |
| `job.work_location.type` | `job.work_location_type` | ネストJSON → フラットカラム |
| `job.salary.min` | `job.salary_min` | 同上 |
| `job.salary.max` | `job.salary_max` | 同上 |
| `job.salary and job.salary.min` | `job.salary_min` | 同上 |
| `job.salary and job.salary.max` | `job.salary_max` | 同上 |

具体的な変更箇所:

行123: `{{ job._id }}` → `{{ job.id }}`（2箇所）
行127: `{{ job.work_location.type or '勤務地未設定' }}` → `{{ job.work_location_type or '勤務地未設定' }}`
行130: `{{ job.salary.min if job.salary and job.salary.min else '未設定' }}〜{{ job.salary.max if job.salary and job.salary.max else '未設定' }}万円` → `{{ job.salary_min if job.salary_min else '未設定' }}〜{{ job.salary_max if job.salary_max else '未設定' }}万円`
行136: `{{ job._id }}` → `{{ job.id }}`

- [ ] **Step 2: templates/job_detail.htmlを修正する**

| 変更前 | 変更後 |
|--------|--------|
| `job.salary.min if job.salary and job.salary.min` | `job.salary_min if job.salary_min` |
| `job.salary.max if job.salary and job.salary.max` | `job.salary_max if job.salary_max` |
| `job.salary.note` | `job.salary_note` |
| `job.salary and job.salary.note` | `job.salary_note` |
| `job.work_location.type` | `job.work_location_type` |
| `job.work_location.detail` | `job.work_location_detail` |
| `job.technologies` | `job.technologies` |

`job.technologies`のループは変更が必要:

変更前:
```html
{% for tech in job.technologies %}
    <li>{{ tech }}</li>
{% endfor %}
```

変更後（SQLAlchemyのリレーションシップオブジェクトを使う）:
```html
{% for tech in job.technologies %}
    <li>{{ tech.technology }}</li>
{% endfor %}
```

- [ ] **Step 3: コミット**

```bash
git add templates/jobs.html templates/job_detail.html
git commit -m "feat: update templates for PostgreSQL flat column structure"
```

---

## Task 8: docker-compose upで全体の動作確認

**Files:** なし（既存ファイルのテスト）

- [ ] **Step 1: 既存コンテナを停止する**

Run:
```bash
docker-compose down
```

- [ ] **Step 2: 全コンテナをビルド・起動する**

Run:
```bash
docker-compose up --build -d
```

`--build`は「Dockerfileからイメージを再ビルドする」。コードを変更した後は必ずつける。

Expected: `db`と`web`の2コンテナが起動。

- [ ] **Step 3: コンテナの状態を確認する**

Run:
```bash
docker-compose ps
```

Expected: 両方のコンテナが`running`。

- [ ] **Step 4: FastAPIにアクセスしてテーブル自動作成を確認する**

Run:
```bash
docker-compose exec db psql -U postgres -d job_data_platform -c "\dt"
```

Expected: `jobs`と`job_technologies`テーブルが存在する。

- [ ] **Step 5: データをインポートする（Mac側から）**

Run:
```bash
cd /Users/matsunoyuki/code/yukimatsuno/job-data-platform && python 06_import_to_postgres.py
```

Expected: データがINSERTされる。

- [ ] **Step 6: ブラウザで動作確認する**

ブラウザで `http://localhost:8000` にアクセス。

確認項目:
- 求人一覧が表示される
- 検索フィルター（キーワード、カテゴリ、雇用形態等）が動作する
- 求人詳細ページ（`/job/1`等）が表示される
- 技術スタックが表示される
- ページネーションが動作する

- [ ] **Step 7: docker-compose logsでエラーがないか確認する**

Run:
```bash
docker-compose logs web --tail 20
```

Expected: エラーなし。

---

## Task 9: MongoDB移行スクリプト

**Files:**
- Create: `06_migrate_from_mongo.py`

- [ ] **Step 1: 06_migrate_from_mongo.pyを作成する**

```python
import json
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from validators.job_validator import JobRecord
from app.models import Base, Job, JobTechnology
from app.db import engine, SessionLocal

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "job_data_platform")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "herp")

if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set in .env")


def migrate():
    """MongoDBの全データをPydanticバリデーション経由でPostgreSQLに移行"""

    # MongoDB接続
    mongo_client = MongoClient(MONGO_URI)
    mongo_collection = mongo_client[DB_NAME][COLLECTION_NAME]
    mongo_client.admin.command("ping")
    print("MongoDB connected")

    # PostgreSQLテーブル作成
    Base.metadata.create_all(engine)
    db = SessionLocal()

    cursor = mongo_collection.find({})
    total = mongo_collection.count_documents({})
    print(f"Total documents in MongoDB: {total}")

    success_count = 0
    skip_count = 0
    error_count = 0
    errors = []

    for i, doc in enumerate(cursor, 1):
        # MongoDBの_idを除去（Pydanticに不要）
        doc.pop("_id", None)

        # Pydanticバリデーション
        try:
            record = JobRecord.model_validate(doc)
        except Exception as e:
            print(f"[{i}/{total}] Validation error: {e}")
            errors.append({
                "index": i,
                "url": doc.get("url", "unknown"),
                "error": str(e),
            })
            error_count += 1
            continue

        # 既存チェック
        existing = db.query(Job).filter(Job.url == record.url).first()
        if existing:
            skip_count += 1
            print(f"[{i}/{total}] SKIP (already exists): {record.url}")
            continue

        # 新規レコード作成
        job = Job(
            url=record.url,
            company_name=record.company_name,
            company_website_url=record.company_website_url,
            job_title_raw=record.job_title_raw,
            job_title_ja=record.job_title_ja,
            job_summary_ja=record.job_summary_ja,
            job_description_ja=record.job_description_ja,
            job_category=record.job_category.value if record.job_category else None,
            job_role=record.job_role,
            employment_type=record.employment_type.value if record.employment_type else None,
            remote_type=record.remote_type.value if record.remote_type else None,
            work_location_type=record.work_location.type if record.work_location else None,
            work_location_detail=record.work_location.detail if record.work_location else None,
            salary_min=record.salary.min if record.salary else None,
            salary_max=record.salary.max if record.salary else None,
            salary_note=record.salary.note if record.salary else None,
            original_language=record.original_language,
        )
        for tech in record.technologies:
            job.technologies.append(JobTechnology(technology=tech))
        db.add(job)
        success_count += 1
        print(f"[{i}/{total}] MIGRATED: {record.url}")

        if i % 10 == 0:
            db.commit()

    db.commit()
    db.close()
    mongo_client.close()

    if errors:
        error_file = "06_migration_errors.jsonl"
        with open(error_file, "w", encoding="utf-8") as f:
            for err in errors:
                f.write(json.dumps(err, ensure_ascii=False) + "\n")
        print(f"\nMigration errors saved to {error_file}")

    print(f"\nMigration completed: {success_count} migrated, {skip_count} skipped, {error_count} errors")


if __name__ == "__main__":
    migrate()
```

- [ ] **Step 2: 移行を実行する**

`.env`にMONGO_URIが設定されていることを確認してから:

Run:
```bash
cd /Users/matsunoyuki/code/yukimatsuno/job-data-platform && python 06_migrate_from_mongo.py
```

Expected: MongoDBの全ドキュメントがバリデーション → PostgreSQLに移行される。

- [ ] **Step 3: 移行後のデータを確認する**

Run:
```bash
docker-compose exec db psql -U postgres -d job_data_platform -c "SELECT COUNT(*) FROM jobs;"
```

Expected: MongoDBと同じドキュメント数。

- [ ] **Step 4: コミット**

```bash
git add 06_migrate_from_mongo.py
git commit -m "feat: add MongoDB to PostgreSQL migration script"
```

---

## Task 10: 最終確認とクリーンアップ

- [ ] **Step 1: 全テストを実行する**

Run:
```bash
cd /Users/matsunoyuki/code/yukimatsuno/job-data-platform && python -m pytest tests/ -v
```

Expected: 全テスト通過。

- [ ] **Step 2: docker-compose down → up で再起動テスト**

Run:
```bash
docker-compose down && docker-compose up --build -d
```

Expected: コンテナが正常に起動。`pgdata`ボリュームにデータが残っているので、再起動後もデータは維持される。

- [ ] **Step 3: ブラウザで最終確認**

`http://localhost:8000` にアクセスして、全機能が動作することを確認:
- 求人一覧表示
- 検索・フィルタリング
- 求人詳細ページ
- ページネーション

- [ ] **Step 4: 最終コミット**

```bash
git add -A
git commit -m "chore: Phase 1 complete - Docker + PostgreSQL + Pydantic validation"
```
