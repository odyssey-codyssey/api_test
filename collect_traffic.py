"""links.txt에 적은 링크들의 실시간 속도를 주기적으로 수집해 CSV에 쌓는다.

사용: python3 collect_traffic.py --interval 5
  - links.txt: 한 줄에 링크 ID 하나 (# 으로 시작하면 주석)
  - Ctrl+C로 종료
"""
import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

from config import DATA_DIR, SERVICES
from seoul_api import SeoulApiError, fetch_page

LINKS_FILE = Path(__file__).parent / "links.txt"


def load_links() -> list:
    if not LINKS_FILE.exists():
        raise SystemExit("links.txt가 없어요. 수집할 링크 ID를 한 줄에 하나씩 적어주세요.")
    return [l.strip() for l in LINKS_FILE.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


def collect_once(links: list, writer) -> int:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    n = 0
    for link_id in links:
        try:
            page = fetch_page(SERVICES["traffic"], 1, 5, [link_id])
        except SeoulApiError as e:
            print(f"  ! {link_id}: {e}")
            continue
        for row in page["rows"]:
            writer.writerow({"collected_at": now, "link_id": link_id,
                             "speed": row.get("prcs_spd") or row.get("PRCS_SPD", ""),
                             "travel_time": row.get("prcs_trv_time") or row.get("PRCS_TRV_TIME", ""),
                             "raw": row})
            n += 1
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=5, help="수집 간격(분)")
    ap.add_argument("--once", action="store_true", help="한 번만 수집")
    args = ap.parse_args()

    links = load_links()
    DATA_DIR.mkdir(exist_ok=True)
    out = DATA_DIR / f"traffic_{datetime.now():%Y%m%d}.csv"
    new_file = not out.exists()
    print(f"링크 {len(links)}개, {args.interval}분 간격 → {out}")

    with out.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["collected_at", "link_id", "speed", "travel_time", "raw"])
        if new_file:
            writer.writeheader()
        while True:
            n = collect_once(links, writer)
            f.flush()
            print(f"{datetime.now():%H:%M:%S} {n}건 저장")
            if args.once:
                break
            time.sleep(args.interval * 60)


if __name__ == "__main__":
    main()
