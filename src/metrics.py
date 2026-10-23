"""ฟังก์ชันคำนวณตัวชี้วัดของบ้านสบาย ช็อป

ทุกฟังก์ชันรับ DataFrame ที่ได้จาก load_orders() เป็นพารามิเตอร์แรก
นิยามตัวชี้วัดอยู่ใน CLAUDE.md
"""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).resolve().parent.parent / "data"

STATUS_SUCCESS = "จัดส่งสำเร็จ"
STATUS_CANCEL = "ยกเลิก"
STATUS_RETURN = "คืนสินค้า"


def load_orders(path: Path | str = DATA / "orders.csv") -> pd.DataFrame:
    """อ่าน orders.csv แล้วเพิ่มคอลัมน์ที่ใช้บ่อย: net, unit_cost, gp, month, date"""
    orders = pd.read_csv(path, encoding="utf-8-sig")
    products = pd.read_csv(DATA / "products.csv", encoding="utf-8-sig")[["product_id", "unit_cost"]]
    df = orders.merge(products, on="product_id", how="left")

    is_success = df["status"] == STATUS_SUCCESS
    df["net"] = 0.0
    df.loc[is_success, "net"] = (
        df.loc[is_success, "qty"]
        * df.loc[is_success, "unit_price"]
        * (1 - df.loc[is_success, "discount_pct"] / 100)
    )
    df["gp"] = 0.0
    df.loc[is_success, "gp"] = (
        df.loc[is_success, "net"] - df.loc[is_success, "qty"] * df.loc[is_success, "unit_cost"]
    )

    df["month"] = df["order_datetime"].str.slice(0, 7)
    df["date"] = df["order_datetime"].str.slice(0, 10)
    return df


def net_sales(df: pd.DataFrame) -> float:
    """ยอดขายสุทธิรวม (บาท)"""
    return df["net"].sum()


def gross_profit(df: pd.DataFrame) -> float:
    """กำไรขั้นต้นรวม (บาท)"""
    return df["gp"].sum()


def aov(df: pd.DataFrame) -> float:
    """ยอดขายสุทธิเฉลี่ยต่อคำสั่งซื้อที่จัดส่งสำเร็จ (บาท)"""
    success_count = (df["status"] == STATUS_SUCCESS).sum()
    return net_sales(df) / success_count


def cancel_rate(df: pd.DataFrame) -> float:
    """อัตรายกเลิกของคำสั่งซื้อทั้งหมดใน df (เปอร์เซ็นต์ 0–100)"""
    return (df["status"] == STATUS_CANCEL).sum() / len(df) * 100


def monthly_sales(df: pd.DataFrame) -> pd.Series:
    """ยอดขายสุทธิรายเดือน index = 'YYYY-MM' เรียงตามเวลา"""
    success = df[df["status"] == STATUS_SUCCESS]
    return success.groupby("month")["net"].sum().sort_index()


def best_month(df: pd.DataFrame) -> str:
    """เดือนที่ยอดขายสุทธิสูงสุด ('YYYY-MM')"""
    return monthly_sales(df).idxmax()


def channel_share(df: pd.DataFrame, channel: str, start_month: str, end_month: str) -> float:
    """สัดส่วนยอดขายสุทธิของช่องทางในช่วงเดือน start_month..end_month (รวมทั้งสองเดือน) เป็นเปอร์เซ็นต์"""
    success = df[
        (df["status"] == STATUS_SUCCESS)
        & (df["month"] >= start_month)
        & (df["month"] <= end_month)
    ]
    total = success["net"].sum()
    if total == 0:
        return 0.0
    channel_total = success.loc[success["channel"] == channel, "net"].sum()
    return channel_total / total * 100


def rating_by_ship_bucket(df: pd.DataFrame) -> dict[str, float]:
    """คะแนนรีวิวเฉลี่ยตามระยะส่ง คืน dict คีย์ '1-2', '3-4', '5-6', '7+'"""
    d = df.dropna(subset=["ship_days", "rating"])
    bucket = pd.cut(d["ship_days"], bins=[0, 2, 4, 6, float("inf")], labels=["1-2", "3-4", "5-6", "7+"])
    return d.groupby(bucket, observed=True)["rating"].mean().to_dict()


def top_province(df: pd.DataFrame, region: str) -> str:
    """จังหวัดที่มียอดขายสุทธิสูงสุดในภูมิภาคที่ระบุ"""
    success = df[(df["status"] == STATUS_SUCCESS) & (df["region"] == region)]
    return success.groupby("province")["net"].sum().idxmax()


def avg_ship_days(df: pd.DataFrame, region: str | None = None, carrier: str | None = None,
                  start_date: str | None = None, end_date: str | None = None) -> float:
    """ระยะส่งเฉลี่ย (วัน) ตามตัวกรองที่ให้มา วันที่เป็น 'YYYY-MM-DD' และรวมทั้งสองวัน"""
    d = df.dropna(subset=["ship_days"])
    if region is not None:
        d = d[d["region"] == region]
    if carrier is not None:
        d = d[d["carrier"] == carrier]
    if start_date is not None:
        d = d[d["date"] >= start_date]
    if end_date is not None:
        d = d[d["date"] <= end_date]
    return d["ship_days"].mean()


def return_rate(df: pd.DataFrame, product_id: str | None = None,
                start_date: str | None = None, end_date: str | None = None) -> float:
    """อัตราคืนสินค้า (เปอร์เซ็นต์) ของสินค้าและช่วงวันที่ที่ระบุ"""
    d = df
    if product_id is not None:
        d = d[d["product_id"] == product_id]
    if start_date is not None:
        d = d[d["date"] >= start_date]
    if end_date is not None:
        d = d[d["date"] <= end_date]
    return (d["status"] == STATUS_RETURN).sum() / len(d) * 100


def top_products(df: pd.DataFrame, n: int = 5) -> pd.Series:
    """สินค้าขายดี n อันดับแรกตามยอดขายสุทธิ index = product_name เรียงมากไปน้อย"""
    success = df[df["status"] == STATUS_SUCCESS]
    return success.groupby("product_name")["net"].sum().sort_values(ascending=False).head(n)
