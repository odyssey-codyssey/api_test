"""실시간 돌발정보(사고·공사·행사 통제 등)를 받아 CSV로 저장하고 유형별로 요약한다.

사용: python3 fetch_accidents.py
"""
import csv
from collections import Counter
from datetime import datetime

from config import DATA_DIR, SERVICES
from seoul_api import fetch_all

# 응답 필드명은 check_services.py 결과를 보고 필요하면 맞춰주세요
TYPE_FIELDS = ["acc_type", "ACC_TYPE", "acc_dtype", "ACC_DTYPE"]
INFO_FIELDS = ["acc_info", "ACC_INFO"]


def first_value(row: dict, keys: list) -> str:
    for k in keys:
        if row.get(k):
            return str(row[k])
    return ""


def main() -> None:
    rows = list(fetch_all(SERVICES["accident"]))
    print(f"돌발정보 {len(rows)}건")
    if not rows:
        return

    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / f"accidents_{datetime.now():%Y%m%d_%H%M}.csv"
    fields = sorted({k for r in rows for k in r.keys()})
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"저장: {out}")

    print("\n[유형별 건수]")
    for t, n in Counter(first_value(r, TYPE_FIELDS) or "(유형 필드 없음)" for r in rows).most_common():
        print(f"  {t}: {n}")

    keywords = ("행사", "마라톤", "집회", "통제")
    hits = [r for r in rows if any(k in first_value(r, INFO_FIELDS) for k in keywords)]
    print(f"\n[행사/마라톤/집회/통제 키워드 포함: {len(hits)}건]")
    for r in hits[:10]:
        print("  -", first_value(r, INFO_FIELDS)[:120])


if __name__ == "__main__":
    main()
