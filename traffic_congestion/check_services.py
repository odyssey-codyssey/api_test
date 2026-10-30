"""교통 체증 관련 API가 응답하는지, 서비스명이 맞는지 점검한다.

사용 (이 폴더 안에서): python3 check_services.py
"""
import json

from config import SERVICES
from seoul_api import SeoulApiError, fetch_page


def check(label, service, params=None):
    print(f"\n=== {label} ({service}) ===")
    try:
        page = fetch_page(service, 1, 3, params)
    except SeoulApiError as e:
        print(f"  ERROR: {e}")
        return {}
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        return {}
    print(f"  결과: [{page['code']}] {page['message']}  / 전체 {page['total']}건")
    if page["rows"]:
        first = page["rows"][0]
        print(f"  필드: {list(first.keys())}")
        print("  예시:", json.dumps(first, ensure_ascii=False)[:500])
        return first
    return {}


def main():
    check("교통권역(자치구) 코드", SERVICES["region"])
    check("도로분류 코드", SERVICES["road_div"])
    spot = check("교통량 지점정보", SERVICES["spot"])

    # 통제 구간이 아닌 링크를 찾기 위해 돌발정보에서 링크ID 여러 개를 시험
    acc = fetch_page(SERVICES["accident"], 1, 20)["rows"]
    link_ids = list(dict.fromkeys(r["link_id"] for r in acc if r.get("link_id")))
    for lid in link_ids:
        if check(f"실시간 도로소통 (링크 {lid})", SERVICES["traffic"], [lid]):
            check("링크정보", SERVICES["link"], [lid])
            check("링크 Vertex", SERVICES["link_vertex"], [lid])
            break

    if spot.get("spot_num"):
        check("교통량 이력정보 (2025-03-16 08시 예시)", SERVICES["volume"], [spot["spot_num"], "20250316", "08"])


if __name__ == "__main__":
    main()
