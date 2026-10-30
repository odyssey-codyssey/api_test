"""설정값 모음.

서비스명은 열린데이터광장 각 데이터 페이지의 'Open API' 탭 샘플 URL에서 확인할 수 있어요.
check_services.py 실행 결과 ERROR가 나는 항목은 여기 이름을 고쳐주면 됩니다.
"""
import os
from pathlib import Path

BASE_URL = "http://openapi.seoul.go.kr:8088"
DATA_DIR = Path(__file__).parent / "data"
PAGE_SIZE = 1000  # 열린데이터광장은 한 번에 최대 1,000건


def _load_env() -> None:
    """의존성 없이 .env 파일을 읽어 환경변수로 넣는다."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env()
API_KEY = os.environ.get("SEOUL_API_KEY", "")

# TOPIS 교통 API 서비스명 (추정값 포함, check_services.py로 검증)
SERVICES = {
    "accident": "AccInfo",          # 실시간 돌발정보
    "acc_main_code": "AccMainCode",  # 돌발 유형 코드정보
    "acc_sub_code": "AccSubCode",    # 돌발 세부유형 코드정보
    "traffic": "TrafficInfo",       # 실시간 도로소통정보 (LINK_ID 필요)
    "spot": "SpotInfo",             # 교통량 지점정보
    "volume": "VolInfo",            # 교통량 이력정보 (지점번호/일자/시간 필요)
    "link": "LinkInfo",             # 링크정보
    "link_vertex": "LinkVerInfo",   # 링크 Vertex 정보 (LINK_ID 필요)
}
