"""ทดสอบ src/report.py (ไม่เขียนทับไฟล์ reports/ จริง ใช้ tmp_path แทน)"""
import pytest

from src import metrics as m
from src import report


@pytest.fixture(scope="module")
def df():
    return m.load_orders()


def test_monthly_report_march_net_sales(tmp_path, monkeypatch, df):
    monkeypatch.setattr(report, "REPORTS_DIR", tmp_path)
    path = report.write_report("2026-03", df)

    assert path == tmp_path / "monthly_report.md"
    content = path.read_text(encoding="utf-8")
    assert "ยอดขายสุทธิ: 1,147,155 บาท" in content


def test_monthly_report_sections(tmp_path, monkeypatch, df):
    monkeypatch.setattr(report, "REPORTS_DIR", tmp_path)
    path = report.write_report("2026-03", df)
    content = path.read_text(encoding="utf-8")

    assert "# รายงานยอดขายประจำเดือน 2026-03" in content
    assert "เทียบเดือนก่อน (2026-02)" in content
    assert "อัตรายกเลิก" in content
    assert "อัตราคืนสินค้า" in content
    assert "5 สินค้าขายดี" in content
