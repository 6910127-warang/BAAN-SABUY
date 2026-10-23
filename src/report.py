"""สร้างรายงานยอดขายรายเดือนจากฟังก์ชันใน src/metrics.py

ใช้งาน:
    python -m src.report 2026-03
"""
import sys
from pathlib import Path

from src import metrics as m

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORT_FILENAME = "monthly_report.md"


def _prev_month(month: str) -> str:
    year, mon = (int(part) for part in month.split("-"))
    if mon == 1:
        return f"{year - 1}-12"
    return f"{year}-{mon - 1:02d}"


def build_report(df, month: str) -> str:
    """สร้างเนื้อหารายงาน Markdown สำหรับเดือนที่ระบุ (YYYY-MM) โดยใช้ฟังก์ชันใน metrics.py เท่านั้น"""
    monthly = m.monthly_sales(df)
    current_net = monthly.get(month, 0.0)

    prev_month = _prev_month(month)
    prev_net = monthly.get(prev_month)

    month_df = df[df["month"] == month]
    top5 = m.top_products(month_df, 5)
    cancel = m.cancel_rate(month_df)
    returned = m.return_rate(month_df)

    lines = [f"# รายงานยอดขายประจำเดือน {month}", ""]
    lines.append(f"- ยอดขายสุทธิ: {current_net:,.0f} บาท")
    if prev_net is not None:
        diff = current_net - prev_net
        diff_pct = (diff / prev_net * 100) if prev_net else 0.0
        direction = "เพิ่มขึ้น" if diff >= 0 else "ลดลง"
        lines.append(
            f"- เทียบเดือนก่อน ({prev_month}): {direction} {abs(diff):,.0f} บาท ({diff_pct:+.1f}%)"
        )
    else:
        lines.append(f"- เทียบเดือนก่อน ({prev_month}): ไม่มีข้อมูลเดือนก่อนหน้า")
    lines.append(f"- อัตรายกเลิก: {cancel:.2f}%")
    lines.append(f"- อัตราคืนสินค้า: {returned:.2f}%")
    lines.append("")
    lines.append("## 5 สินค้าขายดี (ตามยอดขายสุทธิ)")
    lines.append("")
    lines.append("| อันดับ | สินค้า | ยอดขายสุทธิ (บาท) |")
    lines.append("|---|---|---|")
    for rank, (product_name, net) in enumerate(top5.items(), start=1):
        lines.append(f"| {rank} | {product_name} | {net:,.0f} |")
    lines.append("")
    return "\n".join(lines)


def write_report(month: str, df=None) -> Path:
    if df is None:
        df = m.load_orders()
    content = build_report(df, month)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / REPORT_FILENAME
    out_path.write_text(content, encoding="utf-8")
    return out_path


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python -m src.report YYYY-MM", file=sys.stderr)
        raise SystemExit(1)
    path = write_report(argv[0])
    print(f"เขียนรายงานที่ {path}")


if __name__ == "__main__":
    main()
