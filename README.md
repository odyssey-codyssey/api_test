# 서울시 교통 Open API 테스트

러닝 코스 추천 서비스에 쓸 서울시 TOPIS 교통 데이터를 서울 열린데이터광장 Open API로 받아보는 저장소.
목적별로 폴더 2개로 나뉘어 있고, **각 폴더는 설정·API 클라이언트·인증키·결과까지 모두 안에 있어서 따로 실행된다.**

## 폴더 구성

| 폴더 | 목적 | 주요 API | 주요 스크립트 |
|---|---|---|---|
| [`traffic_congestion/`](traffic_congestion/) | **교통 체증**: 도로 구간별 실시간 속도, 지점별 과거 교통량 | `TrafficInfo`, `SpotInfo`, `VolInfo`, `LinkInfo`, `LinkVerInfo` | `collect_traffic.py`, `fetch_volume_history.py`, `build_links.py` |
| [`event_control/`](event_control/) | **교통통제·행사**: 마라톤·행사·집회·공사 통제, 행사 일정 | `AccInfo`, `AccMainCode`, `AccSubCode`, `LinkInfo`, `culturalEventInfo` | `fetch_event_control.py`, `fetch_accidents.py`, `fetch_cultural_events.py` |

### traffic_congestion — 교통 체증
- 러닝 코스 주변 도로가 **지금 막히는지** 판단 (실시간 구간 속도)
- 마라톤 날 교통량이 **평소보다 얼마나 달라지는지** 비교 (문제 정의 근거)
- 여의도 등 특정 지역 도로의 링크ID 목록 생성 → 실시간 속도 주기 수집

자세한 요청값·응답값·실행법: [`traffic_congestion/README.md`](traffic_congestion/README.md)

### event_control — 교통통제·행사
- 행사·집회 교통통제를 **진행 중 / 예정**으로 나누고 어느 도로 어느 구간인지 표시
- 돌발정보(사고·공사·행사 등) 전체 저장과 유형별 요약
- 마라톤 같은 행사 일정 검색
- "이날은 이 코스 피하세요" 같은 추천 기능에 사용

자세한 요청값·응답값·실행법: [`event_control/README.md`](event_control/README.md)

## 빠른 시작

```bash
# 1) 폴더로 이동
cd traffic_congestion            # 또는 cd event_control

# 2) 가상환경 (폴더별로 만들거나 루트의 .venv를 같이 써도 됨)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3) 그 폴더의 .env에 인증키 입력
#    SEOUL_API_KEY=발급받은키

# 4) API 점검 후 스크립트 실행
python3 check_services.py
```

## 공통 사항

- **인증키**: 열린데이터광장 일반 인증키 하나로 두 폴더 API를 모두 쓸 수 있다. 폴더마다 `.env`에 같은 키를 넣는다.
- **응답 형식**: 교통 API는 `xml`만 지원한다 (`json`이면 ERROR-301). 각 폴더의 `seoul_api.py`가 XML을 딕셔너리로 바꿔준다.
- **호출 단위**: 한 번에 최대 1,000건, 넘으면 자동으로 나눠 호출한다.
- **커밋 제외**: `.env`, `.venv/`, `data/`, `__pycache__/`
- 요청 URL 구조, 응답 구조, 결과 코드 설명은 각 폴더 README에 같은 내용으로 들어 있다.

## 출처
서울특별시 TOPIS, 서울 열린데이터광장 (공공누리 1유형, 출처 표시)
