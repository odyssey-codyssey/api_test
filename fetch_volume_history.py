"""교통량 이력정보로 '마라톤 날 vs 평소 같은 요일' 시간대별 교통량을 비교한다.

사용 예:
  # 지점명에 '세종대로'가 들어간 지점들, 2025 서울마라톤(3/16) vs 앞뒤 일요일
  python3 fetch_volume_history.py --keyword 세종대로 --event 20250316 --base 20250309 20250323

  # 지점 목록만 보고 싶을 때
  python3 fetch_volume_history.py --list-spots --keyword 여의
"""
import argparse
import csv
from collections import defaultdict

from config import DATA_DIR, SERVICES
from seoul_api import SeoulApiError, fetch_all, fetch_page

NAME_FIELDS = ["spot_nm", "SPOT_NM"]
NUM_FIELDS = ["spot_num", "SPOT_NUM"]
VOL_FIELDS = ["vol", "VOL"]


def pick(row: dict, keys: list) -> str:
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return str(row[k])
    return ""


def load_spots(keyword: str) -> list:
    spots = list(fetch_all(SERVICES["spot"]))
    if keyword:
        spots = [s for s in spots if keyword in pick(s, NAME_FIELDS)]
    return spots


def hourly_volume(spot_num: str, ymd: str, hour: int) -> int:
    """한 지점·한 날짜·한 시간의 교통량 합계(차로/방향 합산)."""
    try:
        page = fetch_page(SERVICES["volume"], 1, 1000, [spot_num, ymd, f"{hour:02d}"])
    except SeoulApiError as e:
        print(f"    ! {spot_num} {ymd} {hour:02d}시: {e}")
        return 0
    total = 0
    for row in page["rows"]:
        try:
            total += int(float(pick(row, VOL_FIELDS) or 0))
        except ValueError:
            pass
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keyword", default="", help="지점명 필터 (예: 세종대로, 종로, 여의)")
    ap.add_argument("--event", help="행사(마라톤) 날짜 YYYYMMDD")
    ap.add_argument("--base", nargs="*", default=[], help="비교할 평소 날짜들 YYYYMMDD")
    ap.add_argument("--hours", default="6-13", help="시간 범위, 예: 6-13")
    ap.add_argument("--max-spots", type=int, default=5, help="호출량을 줄이기 위한 최대 지점 수")
    ap.add_argument("--list-spots", action="store_true")
    args = ap.parse_args()

    spots = load_spots(args.keyword)
    print(f"지점 {len(spots)}개 (키워드: '{args.keyword}')")
    if args.list_spots or not args.event:
        for s in spots[:50]:
            print(f"  {pick(s, NUM_FIELDS):>8}  {pick(s, NAME_FIELDS)}")
        if not args.event:
            print("\n--event 날짜를 주면 비교를 실행해요.")
        return

    h_from, h_to = (int(x) for x in args.hours.split("-"))
    hours = list(range(h_from, h_to + 1))
    spots = spots[: args.max_spots]
    dates = [args.event] + args.base

    # results[(spot_num, date)][hour] = volume
    results = defaultdict(dict)
    for s in spots:
        num, name = pick(s, NUM_FIELDS), pick(s, NAME_FIELDS)
        print(f"\n[{num}] {name}")
        for d in dates:
            for h in hours:
                results[(num, d)][h] = hourly_volume(num, d, h)
            print(f"  {d}: " + " ".join(f"{h:02d}시={results[(num, d)][h]}" for h in hours))

    # 마라톤 날 vs 평소 평균 비교
    print("\n[요약] 마라톤 날 / 평소 평균")
    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / f"volume_compare_{args.event}.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["spot_num", "spot_nm", "hour", "event_vol", "base_avg", "ratio"])
        for s in spots:
            num, name = pick(s, NUM_FIELDS), pick(s, NAME_FIELDS)
            for h in hours:
                ev = results[(num, args.event)][h]
                base_vals = [results[(num, d)][h] for d in args.base]
                base_avg = sum(base_vals) / len(base_vals) if base_vals else 0
                ratio = round(ev / base_avg, 2) if base_avg else ""
                w.writerow([num, name, h, ev, round(base_avg, 1), ratio])
                if ratio != "":
                    print(f"  {name} {h:02d}시: {ev} / {base_avg:.0f} = {ratio}")
    print(f"\n저장: {out}")


if __name__ == "__main__":
    main()
