"""도로분류 → 도로정보 → 도로별 링크 → 링크정보 순으로 따라가서
특정 지역(기본: 여의도 주변) 도로의 링크 ID를 links.txt로 만든다.

사용:
  python3 build_links.py --show-roads          # 도로 목록만 출력 (먼저 이걸로 확인)
  python3 build_links.py                       # 여의도 주변 기본 키워드로 links.txt 생성
  python3 build_links.py --keywords 여의 올림픽 노들 마포대교
"""
import argparse
import csv

from config import DATA_DIR
from seoul_api import SeoulApiError, fetch_all, fetch_page

DEFAULT_KEYWORDS = ["여의", "올림픽대로", "노들로", "국회대로", "의사당", "마포대교", "원효대교", "서강대교"]


def code_and_name(row: dict):
    """필드명을 몰라도 코드/이름 필드를 추정한다."""
    code = next((v for k, v in row.items() if k.endswith("_cd") and "div" not in k), "")
    name = next((v for k, v in row.items() if "nm" in k or "name" in k), "")
    return code, name


def load_roads(debug: bool = False) -> list:
    roads = []
    for div in fetch_all("RoadDivInfo"):
        div_cd, div_nm = div["road_div_cd"], div["road_div_nm"]
        try:
            rows = list(fetch_all("RoadInfo", [div_cd]))
        except SeoulApiError as e:
            print(f"  ! RoadInfo({div_cd} {div_nm}): {e}")
            continue
        if debug and rows:
            print(f"  RoadInfo({div_cd} {div_nm}) 필드: {list(rows[0].keys())} 예시: {rows[0]}")
        for r in rows:
            code, name = code_and_name(r)
            roads.append({"div_cd": div_cd, "div_nm": div_nm, "code": code, "name": name, "raw": r})
    return roads


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keywords", nargs="*", default=DEFAULT_KEYWORDS)
    ap.add_argument("--show-roads", action="store_true")
    args = ap.parse_args()

    roads = load_roads(debug=True)
    print(f"\n도로 {len(roads)}개")
    if args.show_roads:
        for r in roads:
            print(f"  [{r['div_nm']}] {r['code']}  {r['name']}")
        return

    targets = [r for r in roads if any(k in r["name"] for k in args.keywords)]
    print(f"키워드 {args.keywords} → 대상 도로 {len(targets)}개")
    for r in targets:
        print(f"  {r['code']}  {r['name']}")

    links = {}
    for r in targets:
        try:
            rows = list(fetch_all("LinkWithLoad", [r["code"]]))
        except SeoulApiError as e:
            print(f"  ! LinkWithLoad({r['code']} {r['name']}): {e}")
            continue
        if rows and not links:
            print(f"\n  LinkWithLoad 필드: {list(rows[0].keys())} 예시: {rows[0]}")
        for row in rows:
            if row.get("link_id"):
                links.setdefault(row["link_id"], {"road_code": r["code"], "road_name": r["name"]})
    print(f"\n링크 {len(links)}개 확보, 링크정보 조회 중...")

    DATA_DIR.mkdir(exist_ok=True)
    out_csv = DATA_DIR / "links_selected.csv"
    with out_csv.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["link_id", "road_name", "st_node_nm", "ed_node_nm", "map_dist", "reg_cd"])
        for lid, meta in links.items():
            info = {}
            try:
                rows = fetch_page("LinkInfo", 1, 1, [lid])["rows"]
                info = rows[0] if rows else {}
            except SeoulApiError:
                pass
            w.writerow([lid, info.get("road_name", meta["road_name"]), info.get("st_node_nm", ""),
                        info.get("ed_node_nm", ""), info.get("map_dist", ""), info.get("reg_cd", "")])

    with open("links.txt", "w", encoding="utf-8") as f:
        f.write(f"# build_links.py 생성 / 키워드: {' '.join(args.keywords)}\n")
        f.write("\n".join(links.keys()) + "\n")
    print(f"저장: links.txt ({len(links)}개), {out_csv}")


if __name__ == "__main__":
    main()
