"""교통통제·행사 관련 API가 응답하는지, 서비스명이 맞는지 점검한다.

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
    acc = check("실시간 돌발정보", SERVICES["accident"])
    check("돌발 유형 코드", SERVICES["acc_main_code"])
    check("돌발 세부유형 코드", SERVICES["acc_sub_code"])
    if acc.get("link_id"):
        check("링크정보 (통제 구간 도로명)", SERVICES["link"], [acc["link_id"]])
    check("문화행사 정보 (제목: 마라톤)", SERVICES["cultural_event"], [" ", "마라톤", " "])


if __name__ == "__main__":
    main()
