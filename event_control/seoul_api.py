"""서울 열린데이터광장 Open API 공통 클라이언트.

TOPIS 교통 API는 JSON을 지원하지 않아 XML로 받아서 dict로 변환한다.
"""
import xml.etree.ElementTree as ET
from typing import Dict, Iterator, List, Optional

import requests

from config import API_KEY, BASE_URL, PAGE_SIZE

# 결과 코드: INFO-000 정상, INFO-200 데이터 없음, 나머지는 오류
OK_CODES = {"INFO-000"}
EMPTY_CODES = {"INFO-200"}


class SeoulApiError(RuntimeError):
    pass


def _build_url(service: str, start: int, end: int, params: List[str], fmt: str = "xml") -> str:
    if not API_KEY:
        raise SeoulApiError(".env 파일에 SEOUL_API_KEY가 없어요.")
    path = [BASE_URL, API_KEY, fmt, service, str(start), str(end)] + [str(p) for p in params]
    return "/".join(path) + "/"


def _row_to_dict(row: ET.Element) -> Dict[str, str]:
    return {child.tag: (child.text or "").strip() for child in row}


def fetch_page(service: str, start: int, end: int, params: Optional[List[str]] = None,
               timeout: int = 15) -> Dict:
    """한 페이지를 호출하고 {'total', 'rows', 'code', 'message'}를 돌려준다."""
    url = _build_url(service, start, end, params or [])
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError:
        raise SeoulApiError(f"XML이 아닌 응답: {resp.text[:300]}")

    # 정상: <서비스명><list_total_count/><RESULT/><row/>...</서비스명>
    # 오류: <response><RESULT/></response> 또는 <RESULT/>
    result = root if root.tag == "RESULT" else root.find(".//RESULT")
    code = result.findtext("CODE", "").strip() if result is not None else ""
    message = result.findtext("MESSAGE", "").strip() if result is not None else ""

    if code in EMPTY_CODES:
        return {"total": 0, "rows": [], "code": code, "message": message}
    if code not in OK_CODES:
        raise SeoulApiError(f"{service} 호출 실패 [{code or 'UNKNOWN'}] {message}")

    rows = [_row_to_dict(r) for r in root.findall("row")]
    total_text = root.findtext("list_total_count", "0").strip() or "0"
    return {"total": int(total_text), "rows": rows, "code": code, "message": message}


def fetch_all(service: str, params: Optional[List[str]] = None, limit: Optional[int] = None) -> Iterator[Dict]:
    """1,000건씩 나눠 끝까지(또는 limit까지) 가져온다."""
    start = 1
    fetched = 0
    while True:
        end = start + PAGE_SIZE - 1
        page = fetch_page(service, start, end, params)
        for row in page["rows"]:
            yield row
            fetched += 1
            if limit and fetched >= limit:
                return
        if not page["rows"] or end >= page["total"]:
            return
        start = end + 1
