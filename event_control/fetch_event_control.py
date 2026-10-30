"""실시간 돌발정보에서 행사·집회 등 교통통제 건만 골라 '진행 중 / 예정'으로 나누고
링크정보로 도로명·구간을 붙여 저장한다.

사용 (이 폴더 안에서):
  python3 fetch_event_control.py --show-codes        # 돌발 유형 코드표 보기
  python3 fetch_event_control.py                     # 기본: 행사·집회 유형
  python3 fetch_event_control.py --types 행사 집회 공사
"""

import argparse
import csv
from datetime import datetime
from zoneinfo import ZoneInfo

from config import SERVICES, data_dir
from seoul_api import SeoulApiError, fetch_all, fetch_page

INFO_KEYWORDS = ("마라톤", "행사", "집회", "대회", "축제", "통제")


def load_codes():
    main = {r["acc_type"]: r["acc_type_nm"] for r in fetch_all(SERVICES["acc_main_code"])}
    sub = {r["acc_dtype"]: r["acc_dtype_nm"] for r in fetch_all(SERVICES["acc_sub_code"])}
    return main, sub


def to_datetime(ymd: str, hm: str):
    """'20260407' + '1000' 또는 '000000' → datetime. 형식이 이상하면 None."""
    hm = (hm or "0000").ljust(4, "0")[:4]
    try:
        return datetime.strptime(f"{ymd}{hm}", "%Y%m%d%H%M")
    except ValueError:
        return None


def link_detail(link_id: str) -> dict:
    if not link_id:
        return {}
    try:
        rows = fetch_page(SERVICES["link"], 1, 1, [link_id])["rows"]
        return rows[0] if rows else {}
    except SeoulApiError:
        return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--types", nargs="*", default=["행사", "집회"],
                    help="유형 이름에 이 단어가 들어간 건만 고른다")
    ap.add_argument("--show-codes", action="store_true")
    args = ap.parse_args()

    main_codes, sub_codes = load_codes()
    if args.show_codes:
        print("[대분류 acc_type]")
        for k, v in main_codes.items():
            print(f"  {k}: {v}")
        print("\n[세부유형 acc_dtype]")
        for k, v in sub_codes.items():
            print(f"  {k}: {v}")
        return

    now = datetime.now(ZoneInfo("Asia/Seoul")).replace(tzinfo=None)  # API 시각은 한국 시간
    rows = list(fetch_all(SERVICES["accident"]))
    picked = []
    for r in rows:
        type_nm = main_codes.get(r.get("acc_type", ""), "")
        dtype_nm = sub_codes.get(r.get("acc_dtype", ""), "")
        info = r.get("acc_info", "")
        by_type = any(t in type_nm or t in dtype_nm for t in args.types)
        by_text = any(k in info for k in INFO_KEYWORDS) and any(t in info for t in args.types)
        if not (by_type or by_text):
            continue
        start = to_datetime(r.get("occr_date", ""), r.get("occr_time", ""))
        end = to_datetime(r.get("exp_clr_date", ""), r.get("exp_clr_time", ""))
        status = "예정" if start and start > now else "진행 중"
        picked.append({**r, "type_nm": type_nm, "dtype_nm": dtype_nm, "status": status,
                       "start": start.strftime("%Y-%m-%d %H:%M") if start else "",
                       "end": end.strftime("%Y-%m-%d %H:%M") if end else ""})

    print(f"돌발 전체 {len(rows)}건 중 {args.types} 관련 {len(picked)}건")
    for p in picked:
        d = link_detail(p.get("link_id", ""))
        p["road_name"] = d.get("road_name", "")
        p["section"] = f"{d.get('st_node_nm', '')} → {d.get('ed_node_nm', '')}" if d else ""

    for status in ("진행 중", "예정"):
        group = [p for p in picked if p["status"] == status]
        print(f"\n[{status}] {len(group)}건")
        for p in group:
            summary = p.get("acc_info", "").replace("\r", " ").replace("\n", " ")[:80]
            print(f"  {p['start']} ~ {p['end']} | {p['type_nm']}/{p['dtype_nm']} | "
                  f"{p['road_name']} {p['section']} | {summary}")

    if picked:
        out = data_dir(__file__) / f"event_control_{now:%Y%m%d_%H%M}.csv"
        fields = ["status", "start", "end", "type_nm", "dtype_nm", "road_name", "section",
                  "link_id", "grs80tm_x", "grs80tm_y", "acc_id", "acc_info"]
        with out.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(picked)
        print(f"\n저장: {out}")


if __name__ == "__main__":
    main()
