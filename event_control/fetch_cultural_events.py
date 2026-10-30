"""서울시 문화행사 정보에서 마라톤 같은 행사 일정을 찾는다.

서비스명과 파라미터 순서(분류 / 제목 / 날짜)는 열린데이터광장 '서울시 문화행사 정보'
페이지의 Open API 탭에서 확인 필요. 결과의 첫 줄에 필드 이름을 출력하니 그걸 보고 맞춘다.

사용 (이 폴더 안에서):
  python3 fetch_cultural_events.py --title 마라톤
  python3 fetch_cultural_events.py --title 마라톤 --date 2026-11
"""

import argparse
import csv

from config import SERVICES, data_dir
from seoul_api import SeoulApiError, fetch_all

BLANK = " "  # 비워둘 파라미터 자리 (공백 한 칸)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="마라톤", help="행사 제목 검색어")
    ap.add_argument("--codename", default=BLANK, help="분류 (예: 축제-기타). 기본은 전체")
    ap.add_argument("--date", default=BLANK, help="날짜 (예: 2026-11 또는 2026-11-01)")
    ap.add_argument("--limit", type=int, default=200)
    args = ap.parse_args()

    params = [args.codename, args.title, args.date]
    try:
        rows = list(fetch_all(SERVICES["cultural_event"], params, limit=args.limit))
    except SeoulApiError as e:
        print(f"ERROR: {e}")
        print("서비스명 또는 파라미터 순서를 Open API 탭에서 확인하고 config.py를 고쳐주세요.")
        return

    print(f"'{args.title}' 검색 결과 {len(rows)}건")
    if not rows:
        return
    print(f"필드: {list(rows[0].keys())}\n")

    def g(r, *keys):
        return next((r[k] for k in keys if r.get(k)), "")

    for r in rows[:30]:
        print(f"  {g(r, 'STRTDATE', 'DATE')} ~ {g(r, 'END_DATE')} | {g(r, 'GUNAME')} | "
              f"{g(r, 'TITLE')} | {g(r, 'PLACE')}")

    out = data_dir(__file__) / f"cultural_events_{args.title.strip() or 'all'}.csv"
    fields = sorted({k for r in rows for k in r})
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"\n저장: {out}")


if __name__ == "__main__":
    main()
