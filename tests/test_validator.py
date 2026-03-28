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
            "job_category": "エンジニアリング",
        }
        with pytest.raises(Exception):
            JobRecord.model_validate(data)

    def test_invalid_employment_type(self):
        """許可リスト外のemployment_type → バリデーションエラー"""
        data = {
            "url": "https://herp.careers/careers/companies/test/jobs/005",
            "employment_type": "派遣社員",
        }
        with pytest.raises(Exception):
            JobRecord.model_validate(data)

    def test_invalid_remote_type(self):
        """許可リスト外のremote_type → バリデーションエラー"""
        data = {
            "url": "https://herp.careers/careers/companies/test/jobs/006",
            "remote_type": "ハイブリッド",
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
