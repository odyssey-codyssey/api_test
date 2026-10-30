"""설정값 모음.

서비스명은 열린데이터광장 각 데이터 페이지의 'Open API' 탭 샘플 URL에서 확인할 수 있어요.
check_services.py 실행 결과 ERROR가 나는 항목은 여기 이름을 고쳐주면 됩니다.
"""
import os
from pathlib import Path

BASE_URL = "http://openapi.seoul.go.kr:8088"
ROOT_DIR = Path(__file__).resolve().parent  # 이 폴더 (.env, data/ 위치)
PAGE_SIZE = 1000  # 열린데이터광장은 한 번에 최대 1,000건


def _load_env() -> None:
    """의존성 없이 .env 파일을 읽어 환경변수로 넣는다."""
    env_path = ROOT_DIR / ".env"
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

# 이 폴더에서 쓰는 API 서비스명 (check_services.py로 검증)
SERVICES = {
    "traffic": "TrafficInfo",       # 실시간 도로소통정보 (링크ID 필요)
    "spot": "SpotInfo",             # 교통량 지점정보
    "volume": "VolInfo",            # 교통량 이력정보 (지점번호/일자/시간 필요)
    "link": "LinkInfo",             # 링크정보 (링크ID 필요)
    "link_vertex": "LinkVerInfo",   # 링크 Vertex 정보 (링크ID 필요)
    "region": "RegionInfo",         # 교통권역(자치구) 코드
    "road_div": "RoadDivInfo",      # 도로분류 코드
    "road": "RoadInfo",             # 도로정보 (도로분류 코드 필요, 확인 중)
    "road_link": "LinkWithLoad",    # 도로별 링크정보 (도로 축 코드 필요, 확인 중)
    "accident": "AccInfo",          # 실시간 돌발정보 (점검용 링크ID 얻는 데 사용)
}


def data_dir(script_file: str = "") -> Path:
    """이 폴더 아래 data/ 경로를 만들어 돌려준다."""
    d = ROOT_DIR / "data"
    d.mkdir(exist_ok=True)
    return d
