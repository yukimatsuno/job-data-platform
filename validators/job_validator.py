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
