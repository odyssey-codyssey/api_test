# 서울시 교통 Open API 테스트

러닝 코스 추천 서비스에 쓸 TOPIS 교통 데이터(실시간 도로소통, 돌발·통제, 교통량 이력)를 서울 열린데이터광장 Open API로 받아보는 스크립트 모음.

---

## 1. 준비

### 가상환경과 패키지
홈브루 파이썬은 시스템 전체 설치를 막아두므로 프로젝트 안에 가상환경을 만든다.

```bash
python3 -m venv .venv
source .venv/bin/activate        # 터미널을 새로 열 때마다 다시 실행
pip install -r requirements.txt
```

### 인증키
열린데이터광장에서 **일반 인증키**를 발급받아 `.env`에 넣는다. `.env`는 `.gitignore`에 등록되어 있어 커밋되지 않는다.

```
SEOUL_API_KEY=발급받은키
```

---

## 2. 요청 방법

### URL 구조
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
| 추가값 | API마다 필요한 조건 (링크ID, 날짜 등) | `1010009500` |

예: 링크 `1010009500`의 현재 속도

```
http://openapi.seoul.go.kr:8088/{인증키}/xml/TrafficInfo/1/5/1010009500/
```

### 호출 제한
- 한 번에 **최대 1,000건**. 더 많으면 `1/1000`, `1001/2000`처럼 나눠 호출한다 (`seoul_api.fetch_all`이 자동 처리).
- 열린데이터광장 안내상 제약 없이 계속 쓰려면 활용사례(갤러리)에 결과물을 등록해야 한다.

---

## 3. 응답 구조

모든 API가 같은 틀로 응답한다.

```xml
<TrafficInfo>
  <list_total_count>1</list_total_count>      <!-- 조건에 맞는 전체 개수 -->
  <RESULT>
    <CODE>INFO-000</CODE>                      <!-- 결과 코드 -->
    <MESSAGE>정상 처리되었습니다</MESSAGE>
  </RESULT>
  <row>                                        <!-- 데이터 한 줄, 여러 개 올 수 있음 -->
    <link_id>1010009500</link_id>
    <prcs_spd>8</prcs_spd>
    <prcs_trv_time>62</prcs_trv_time>
  </row>
</TrafficInfo>
```

`seoul_api.py`가 이 XML을 `[{"link_id": "1010009500", "prcs_spd": "8", ...}]` 같은 딕셔너리 목록으로 바꿔준다. 값은 모두 문자열이므로 계산할 때 숫자로 변환한다.

### 결과 코드

| 코드 | 의미 | 대응 |
|---|---|---|
| `INFO-000` | 정상 | |
| `INFO-200` | 요청은 맞는데 데이터 없음 | 통제 중인 도로 등. 오류 아님 |
| `ERROR-301` | 서비스는 있는데 형식 또는 필요한 추가값이 잘못됨 | `xml`인지, 추가값을 넣었는지 확인 |
| `ERROR-500` | 서버 오류. 실제로는 **서비스명이 틀린 경우**가 대부분 | `config.py`의 서비스명 확인 |

---

## 4. API별 요청값과 응답값

### 실시간 도로소통 `TrafficInfo`
- 추가값: **링크ID**

| 필드 | 의미 | 예시 |
|---|---|---|
| `link_id` | 도로 구간 ID | `1010009500` |
| `prcs_spd` | 현재 평균 속도 (km/h) | `8` (거의 정체) |
| `prcs_trv_time` | 구간 통과 시간 (초) | `62` |

전면통제 구간은 `INFO-200`(데이터 없음)으로 온다.

### 링크정보 `LinkInfo`
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
- 추가값: **링크ID**

| 필드 | 의미 | 예시 |
|---|---|---|
| `link_id` | 도로 구간 ID | `1220031600` |
| `ver_seq` | 점 순서 | `1`, `2`, `3`... |
| `grs80tm_x` / `grs80tm_y` | 그 점의 좌표 (아래 좌표 주의 참고) | `206174` / `446261` |

점들을 `ver_seq` 순서대로 이으면 도로 선이 된다.

### 실시간 돌발정보 `AccInfo`
- 추가값: 없음 (현재 진행 중인 돌발·통제 전부)

| 필드 | 의미 | 예시 |
|---|---|---|
| `acc_id` | 돌발 ID | `1071788` |
| `occr_date` / `occr_time` | 시작 일시 | `20260407` / `1000` |
| `exp_clr_date` / `exp_clr_time` | 종료 예정 일시 | `20270301` / `000000` |
| `acc_type` | 대분류 코드 (`AccMainCode`로 이름 확인) | `A04` (공사) |
| `acc_dtype` | 세부 코드 (`AccSubCode`로 이름 확인) | `04B01` |
| `link_id` | 영향받는 도로 구간 | `1220031600` |
| `grs80tm_x` / `grs80tm_y` | 발생 위치 좌표 | |
| `acc_info` | 설명 원문 (일시, 장소, 통제 내용) | `봉은교 구조개선공사 … 양방향 전면통제` |
| `acc_road_code` | 도로 코드 | `009` |

종료 예정 일시가 미래 날짜로 오므로 "통제 예정" 정보로도 쓸 수 있다.

### 돌발 유형 코드 `AccMainCode` / 세부유형 코드 `AccSubCode`
- 추가값: 없음

| API | 필드 | 예시 |
|---|---|---|
| `AccMainCode` (13건) | `acc_type`, `acc_type_nm` | `A01` → `교통사고` |
| `AccSubCode` (43건) | `acc_dtype`, `acc_dtype_nm` | `01B01` → `추돌사고` |

### 교통량 지점정보 `SpotInfo`
- 추가값: 없음 (139개 지점)

| 필드 | 의미 | 예시 |
|---|---|---|
| `spot_num` | 측정 지점 번호 | `C-02` |
| `spot_nm` | 지점 이름 | `월드컵대교` |
| `grs80tm_x` / `grs80tm_y` | 지점 좌표 | `189882` / `450789` |

### 교통량 이력정보 `VolInfo`
- 추가값: **지점번호 / 날짜(YYYYMMDD) / 시(HH)**
- 예: `.../VolInfo/1/1000/C-02/20250316/08/`

| 필드 | 의미 | 예시 |
|---|---|---|
| `spot_num` | 측정 지점 번호 | `C-02` |
| `ymd` / `hh` | 날짜, 시 | `20250316` / `08` |
| `io_type` | 방향 구분 (1 또는 2) | `1` |
| `lane_num` | 차로 번호 | `1` |
| `vol` | 해당 시간 동안 지나간 차량 수 | `403` |

한 지점·한 시간에 **방향 × 차로 수만큼 여러 줄**이 온다. 시간당 총 교통량은 `vol`을 모두 더한다. `io_type` 1, 2가 각각 어느 방향인지는 공식 문서에서 아직 확인하지 못했다.

### 기반 코드 `RegionInfo` / `RoadDivInfo`
- 추가값: 없음

| API | 필드 | 예시 |
|---|---|---|
| `RegionInfo` (25건) | `reg_cd`, `reg_name` | `100` → `종로구` |
| `RoadDivInfo` (4건) | `road_div_cd`, `road_div_nm` | `02` → `도시고속도로` |

### 확인 중인 API

| API | 상태 |
|---|---|
| `RoadInfo` (도로정보) | 존재함(ERROR-301). 도로분류 코드를 추가값으로 넣는 것으로 추정, `build_links.py --show-roads`로 확인 중 |
| `LinkWithLoad` (도로별 링크정보) | 존재함(INFO-200). 추가값은 "도로 축 코드"로 추정, `RoadInfo` 결과의 코드를 넣어 확인 예정 |

---

## 5. 데이터끼리 연결되는 방식

```
도로 데이터 → link_id 로 연결

  AccInfo (돌발) ──link_id──┐
                            ├─▶ LinkInfo     (어느 도로, 어느 구간인지)
  LinkWithLoad (도로별) ────┤
                            ├─▶ TrafficInfo  (지금 속도)
                            └─▶ LinkVerInfo  (지도에 그릴 좌표)

교통량 데이터 → spot_num 으로 연결

  SpotInfo (지점 위치) ──spot_num──▶ VolInfo (날짜·시간별 교통량)
```

교통량 지점(`spot_num`)과 도로 구간(`link_id`)은 직접 연결되지 않으므로, 필요하면 좌표 거리로 가까운 것끼리 묶는다.

### 좌표 주의
`grs80tm_x` / `grs80tm_y`는 위도·경도가 아니라 **미터 단위 평면 좌표(GRS80 TM)**다. 지도에 올리려면 위경도로 변환해야 한다. 정확한 좌표계(EPSG 코드)는 변환 코드를 만들 때 실제 위치와 맞춰보며 확정한다.

---

## 6. 스크립트

| 파일 | 역할 |
|---|---|
| `config.py` | 서비스명, 경로, `.env` 로딩 |
| `seoul_api.py` | 공통 클라이언트 (XML 파싱, 결과 코드 처리, 1,000건 단위 페이지 처리) |
| `check_services.py` | API별 응답 코드, 필드, 예시 1건 점검 |
| `probe_links.py` | 링크 관련 서비스명 후보 시험 |
| `build_links.py` | 도로분류 → 도로 → 도로별 링크 → 링크정보로 `links.txt` 생성 |
| `fetch_accidents.py` | 돌발·통제 정보 저장 및 유형별 요약 |
| `fetch_volume_history.py` | 마라톤 날 vs 평소 날 시간대별 교통량 비교 |
| `collect_traffic.py` | `links.txt` 링크의 실시간 속도 주기 수집 |

### 실행 예

```bash
# 1. API 점검
python3 check_services.py

# 2. 여의도 주변 링크 목록 만들기
python3 build_links.py --show-roads           # 도로 목록 확인
python3 build_links.py                        # 기본 키워드로 links.txt 생성
python3 build_links.py --keywords 여의 올림픽대로 노들로

# 3. 돌발·통제 정보
python3 fetch_accidents.py

# 4. 마라톤 날 교통량 비교
python3 fetch_volume_history.py --list-spots
python3 fetch_volume_history.py --keyword 세종대로 --event 20250316 --base 20250309 20250323

# 5. 실시간 속도 수집
python3 collect_traffic.py --once
python3 collect_traffic.py --interval 5
```

비교 날짜(`--event`, `--base`)는 실제 대회 일정을 확인해서 넣는다.

### 결과 파일 (`data/`, 커밋 제외)

| 파일 | 내용 |
|---|---|
| `accidents_YYYYMMDD_HHMM.csv` | 돌발·통제 원본 |
| `volume_compare_YYYYMMDD.csv` | 지점·시간대별 마라톤 날 교통량, 평소 평균, 비율 |
| `traffic_YYYYMMDD.csv` | 수집 시각별 링크 속도 |
| `links_selected.csv` | `build_links.py`가 고른 링크와 도로명·구간·자치구 |

---

## 출처
- 데이터: 서울특별시 TOPIS, 서울 열린데이터광장 (공공누리 1유형, 출처 표시)
