# traffic_congestion — 교통 체증

서울 도로의 실시간 구간 속도와 과거 교통량을 받는다.
- 러닝 코스 주변 도로가 지금 막히는지 판단
- 마라톤 날 교통량이 평소보다 얼마나 달라지는지 비교 (문제 정의 근거)

이 폴더만으로 독립 실행된다 (설정·클라이언트·인증키·결과가 모두 이 안에 있음).

## 파일

| 파일 | 역할 |
|---|---|
| `.env` | 인증키 (커밋 제외) |
| `config.py` | 서비스명, `.env` 로딩, `data/` 경로 |
| `seoul_api.py` | API 클라이언트 (XML 파싱, 결과 코드 처리, 1,000건 단위 페이지 처리) |
| `check_services.py` | 이 폴더 API 점검 |
| `collect_traffic.py` | `links.txt` 링크의 실시간 속도 주기 수집 |
| `links.txt` | 수집할 링크ID 목록 (`build_links.py`가 채움) |
| `fetch_volume_history.py` | 마라톤 날 vs 평소 날 시간대별 교통량 비교 |
| `build_links.py` | 도로 이름으로 링크ID 목록 생성 → `links.txt` |
| `probe_links.py` | 링크 관련 서비스명 후보 시험 |
| `data/` | 실행 결과 (커밋 제외) |

## 준비

이 폴더 안에서 가상환경을 만들고 실행한다.

```bash
cd traffic_congestion
python3 -m venv .venv
source .venv/bin/activate        # 터미널을 새로 열 때마다 다시 실행
pip install -r requirements.txt
```

이 폴더의 `.env`에 열린데이터광장 **일반 인증키**를 넣는다 (`.gitignore`에 등록되어 커밋되지 않음).

```
SEOUL_API_KEY=발급받은키
```

먼저 API가 응답하는지 점검한다.

```bash
python3 check_services.py
```

## 요청 방법

파라미터를 `?a=1&b=2`가 아니라 **URL 경로에 순서대로** 붙인다.

```
http://openapi.seoul.go.kr:8088/{인증키}/xml/{서비스명}/{시작번호}/{끝번호}/{추가값...}/
```

| 자리 | 의미 | 예시 |
|---|---|---|
| 인증키 | 발급받은 일반 인증키 | `.env`의 값 |
| 형식 | 응답 형식. **교통 API는 `xml`만 지원** (`json`이면 ERROR-301) | `xml` |
| 서비스명 | 어떤 데이터를 요청하는지 | `TrafficInfo` |
| 시작/끝번호 | 몇 번째 행부터 몇 번째 행까지 | `1/1000` |
| 추가값 | API마다 필요한 조건 | 아래 API별 설명 참고 |

- 한 번에 **최대 1,000건**. 더 많으면 나눠 호출한다 (`seoul_api.fetch_all`이 자동 처리).
- 열린데이터광장 안내상 제약 없이 계속 쓰려면 활용사례(갤러리)에 결과물을 등록해야 한다.

## 응답 구조

```xml
<서비스명>
  <list_total_count>1</list_total_count>      <!-- 조건에 맞는 전체 개수 -->
  <RESULT>
    <CODE>INFO-000</CODE>                      <!-- 결과 코드 -->
    <MESSAGE>정상 처리되었습니다</MESSAGE>
  </RESULT>
  <row> ... </row>                             <!-- 데이터 한 줄, 여러 개 올 수 있음 -->
</서비스명>
```

`seoul_api.py`가 XML을 딕셔너리 목록으로 바꿔준다. 값은 모두 문자열이므로 계산할 때 숫자로 변환한다.

| 코드 | 의미 | 대응 |
|---|---|---|
| `INFO-000` | 정상 | |
| `INFO-200` | 요청은 맞는데 데이터 없음 | 오류 아님 |
| `ERROR-301` | 서비스는 있는데 형식 또는 필요한 추가값이 잘못됨 | `xml`인지, 추가값을 넣었는지 확인 |
| `ERROR-500` | 서버 오류. 실제로는 **서비스명이 틀린 경우**가 대부분 | `config.py`의 서비스명 확인 |

### 좌표 주의
`grs80tm_x` / `grs80tm_y`는 위도·경도가 아니라 **미터 단위 평면 좌표(GRS80 TM)**다. 지도에 올리려면 위경도로 변환해야 한다.

---

## API별 요청값과 응답값

### 실시간 도로소통 `TrafficInfo`
```
.../xml/TrafficInfo/1/5/{링크ID}/
```
- 추가값: **링크ID** (하나씩 호출)

| 필드 | 의미 | 예시 |
|---|---|---|
| `link_id` | 도로 구간 ID | `1010009500` |
| `prcs_spd` | 현재 평균 속도 (km/h) | `8` (거의 정체) |
| `prcs_trv_time` | 구간 통과 시간 (초) | `62` |

전면통제 구간은 `INFO-200`(데이터 없음)으로 온다.

### 링크정보 `LinkInfo`
```
.../xml/LinkInfo/1/1/{링크ID}/
```
- 추가값: **링크ID** (없으면 ERROR-301)

| 필드 | 의미 | 예시 |
|---|---|---|
| `link_id` | 도로 구간 ID | `1220031600` |
| `road_name` | 도로 이름 | `봉은사로` |
| `st_node_nm` | 구간 시작 지점 | `종합운동장삼거리` |
| `ed_node_nm` | 구간 끝 지점 | `봉은교` |
| `map_dist` | 구간 길이 (m) | `291` |
| `reg_cd` | 자치구 코드 (`RegionInfo`로 이름 확인) | `123` |

### 링크 좌표 `LinkVerInfo`
```
.../xml/LinkVerInfo/1/100/{링크ID}/
```
- 추가값: **링크ID**

| 필드 | 의미 | 예시 |
|---|---|---|
| `link_id` | 도로 구간 ID | `1220031600` |
| `ver_seq` | 점 순서 | `1`, `2`, `3`... |
| `grs80tm_x` / `grs80tm_y` | 그 점의 좌표 | `206174` / `446261` |

점들을 `ver_seq` 순서대로 이으면 도로 선이 된다.

### 교통량 지점정보 `SpotInfo`
```
.../xml/SpotInfo/1/1000/
```
- 추가값: 없음 (139개 지점)

| 필드 | 의미 | 예시 |
|---|---|---|
| `spot_num` | 측정 지점 번호 | `C-02` |
| `spot_nm` | 지점 이름 | `월드컵대교` |
| `grs80tm_x` / `grs80tm_y` | 지점 좌표 | `189882` / `450789` |

### 교통량 이력정보 `VolInfo`
```
.../xml/VolInfo/1/1000/{지점번호}/{YYYYMMDD}/{HH}/
예: .../xml/VolInfo/1/1000/C-02/20250316/08/
```
- 추가값: **지점번호 / 날짜 / 시** (한 번에 한 시간씩)

| 필드 | 의미 | 예시 |
|---|---|---|
| `spot_num` | 측정 지점 번호 | `C-02` |
| `ymd` / `hh` | 날짜, 시 | `20250316` / `08` |
| `io_type` | 방향 구분 (1 또는 2) | `1` |
| `lane_num` | 차로 번호 | `1` |
| `vol` | 해당 시간 동안 지나간 차량 수 | `403` |

한 지점·한 시간에 **방향 × 차로 수만큼 여러 줄**이 온다. 시간당 총 교통량은 `vol`을 모두 더한다. `io_type` 1, 2가 각각 어느 방향인지는 아직 확인하지 못했다.

### 기반 코드 `RegionInfo` / `RoadDivInfo`
- 추가값: 없음

| API | 필드 | 예시 |
|---|---|---|
| `RegionInfo` (25건) | `reg_cd`, `reg_name` | `100` → `종로구` |
| `RoadDivInfo` (4건) | `road_div_cd`, `road_div_nm` | `02` → `도시고속도로` |

### 확인 중

| API | 상태 |
|---|---|
| `RoadInfo` (도로정보) | 존재함(ERROR-301). 도로분류 코드를 추가값으로 넣는 것으로 추정 |
| `LinkWithLoad` (도로별 링크정보) | 존재함(INFO-200). 추가값은 "도로 축 코드"로 추정 |

## 데이터 연결

```
link_id 로 연결
  LinkWithLoad (도로별 링크) ──▶ LinkInfo    (어느 도로, 어느 구간)
                              ├▶ TrafficInfo (지금 속도)
                              └▶ LinkVerInfo (지도에 그릴 좌표)

spot_num 으로 연결
  SpotInfo (지점 위치) ──▶ VolInfo (날짜·시간별 교통량)
```

교통량 지점과 도로 구간은 직접 연결되지 않으므로, 필요하면 좌표 거리로 묶는다.

---

## 실행

### 1. 링크 목록 만들기
```bash
python3 build_links.py --show-roads                       # 도로 목록 확인 (RoadInfo 필드도 출력)
python3 build_links.py                                    # 여의도 주변 기본 키워드로 links.txt 생성
python3 build_links.py --keywords 여의 올림픽대로 노들로
```
흐름: `RoadDivInfo` → `RoadInfo` → 키워드로 도로 거르기 → `LinkWithLoad` → `LinkInfo`
결과: `links.txt`, `data/links_selected.csv`

### 2. 실시간 속도 수집
```bash
python3 collect_traffic.py --once        # 한 번만
python3 collect_traffic.py --interval 5  # 5분마다 계속, Ctrl+C로 종료
```
결과: `data/traffic_YYYYMMDD.csv` (`collected_at`, `link_id`, `speed`, `travel_time`, `raw`)

### 3. 마라톤 날 교통량 비교
```bash
python3 fetch_volume_history.py --list-spots
python3 fetch_volume_history.py --list-spots --keyword 대교
python3 fetch_volume_history.py --keyword 세종대로 --event 20250316 --base 20250309 20250323
```

| 옵션 | 의미 | 기본값 |
|---|---|---|
| `--keyword` | 지점명 필터 | 전체 |
| `--event` | 행사(마라톤) 날짜 | - |
| `--base` | 비교할 평소 날짜들 | - |
| `--hours` | 시간 범위 | `6-13` |
| `--max-spots` | 최대 지점 수 (호출량 제한) | `5` |

- 호출 수 = 지점 수 × 날짜 수 × 시간 수
- 비교 날짜는 실제 대회 일정을 확인해서 넣는다
- 결과: `data/volume_compare_YYYYMMDD.csv` (`spot_num`, `spot_nm`, `hour`, `event_vol`, `base_avg`, `ratio`)

## 출처
서울특별시 TOPIS, 서울 열린데이터광장 (공공누리 1유형, 출처 표시)
