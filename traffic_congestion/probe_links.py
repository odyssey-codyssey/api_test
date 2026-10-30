"""링크 목록을 얻기 위한 서비스명 후보를 시험한다.

사용 (이 폴더 안에서): python3 probe_links.py
"""

from config import SERVICES
from seoul_api import SeoulApiError, fetch_page


def try_call(service, params=None):
    try:
        page = fetch_page(service, 1, 3, params)
    except SeoulApiError as e:
        return f"ERROR {str(e)[-60:]}"
    except Exception as e:
        return f"ERROR {type(e).__name__}"
    keys = list(page["rows"][0].keys()) if page["rows"] else []
    sample = page["rows"][0] if page["rows"] else {}
    return f"[{page['code']}] 전체 {page['total']}건 필드={keys} 예시={sample}"


def main():
    # 1) 돌발정보에서 링크 ID와 도로 코드 몇 개 확보
    acc = fetch_page(SERVICES["accident"], 1, 40)["rows"]
    link_ids = list(dict.fromkeys(r["link_id"] for r in acc if r.get("link_id")))[:8]
    road_codes = list(dict.fromkeys(r["acc_road_code"] for r in acc if r.get("acc_road_code")))[:3]
    print("링크 후보:", link_ids)
    print("도로코드 후보:", road_codes)

    # 2) 실시간 도로소통: 여러 링크로 시험 (통제 구간은 데이터가 없을 수 있음)
    print("\n[실시간 도로소통 TrafficInfo]")
    for lid in link_ids:
        print(f"  {lid}: {try_call(SERVICES['traffic'], [lid])}")

    # 3) 링크정보: 링크 ID를 파라미터로
    print("\n[링크정보 LinkInfo + link_id]")
    print(" ", try_call("LinkInfo", [link_ids[0]]) if link_ids else "링크 없음")

    # 4) 도로정보 / 도로별 링크정보 후보 이름
    print("\n[도로정보 후보]")
    for name in ["RoadInfo", "RoadDivInfo", "RoadList", "RoadInfoList"]:
        print(f"  {name}: {try_call(name)}")

    print("\n[도로별 링크정보 후보 (도로코드 파라미터)]")
    code = road_codes[0] if road_codes else "001"
    for name in ["LinkWithLoad", "RoadLinkInfo", "LinkInfoByRoad", "RoadLink", "LinkWithRoad"]:
        print(f"  {name}({code}): {try_call(name, [code])}")

    print("\n[교통권역 / 도로분류 후보]")
    for name in ["RegionInfo", "RoadDivInfo", "RoadDiv"]:
        print(f"  {name}: {try_call(name)}")


if __name__ == "__main__":
    main()
