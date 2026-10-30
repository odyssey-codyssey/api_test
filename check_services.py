"""각 API가 실제로 응답하는지, 서비스명이 맞는지 점검한다.

사용: python3 check_services.py
"""
import json

from config import SERVICES
from seoul_api import SeoulApiError, fetch_page


def check(label: str, service: str, params=None) -> dict:
    print(f"\n=== {label} ({service}) ===")
    try:
        page = fetch_page(service, 1, 3, params)
    except SeoulApiError as e:
        print(f"  ERROR: {e}")
        return {}
    except Exception as e:  # 네트워크 오류 등
        print(f"  ERROR: {type(e).__name__}: {e}")
        return {}
    print(f"  결과: [{page['code']}] {page['message']}  / 전체 {page['total']}건")
    if page["rows"]:
        first = page["rows"][0]
        print(f"  필드: {list(first.keys())}")
        print("  예시:", json.dumps(first, ensure_ascii=False)[:500])
        return first
    return {}


def main() -> None:
    acc = check("실시간 돌발정보", SERVICES["accident"])
    check("돌발 유형 코드", SERVICES["acc_main_code"])
    check("돌발 세부유형 코드", SERVICES["acc_sub_code"])
    spot = check("교통량 지점정보", SERVICES["spot"])
    link = check("링크정보", SERVICES["link"])

    # 아래 API는 파라미터가 필요해서 위 결과에서 값을 하나 꺼내 쓴다
    link_id = link.get("link_id") or link.get("LINK_ID") or acc.get("link_id")
    if link_id:
        check("실시간 도로소통정보", SERVICES["traffic"], [link_id])
        check("링크 Vertex", SERVICES["link_vertex"], [link_id])
    else:
        print("\n(링크 ID를 못 얻어서 도로소통/Vertex 점검은 건너뜀)")

    spot_num = spot.get("spot_num") or spot.get("SPOT_NUM")
    if spot_num:
        check("교통량 이력정보 (2025-03-16 08시 예시)", SERVICES["volume"], [spot_num, "20250316", "08"])
    else:
        print("\n(지점번호를 못 얻어서 교통량 이력 점검은 건너뜀)")


if __name__ == "__main__":
    main()
