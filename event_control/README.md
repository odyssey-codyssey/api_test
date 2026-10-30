# event_control — 교통통제·행사

마라톤·행사·집회·공사 등으로 인한 교통통제를 받는다.
- 행사·집회 통제를 **진행 중 / 예정**으로 나누고 어느 도로 어느 구간인지 붙임
- 마라톤 같은 행사 일정 검색
- "이날은 이 코스 피하세요" 같은 추천 기능에 사용

이 폴더만으로 독립 실행된다 (설정·클라이언트·인증키·결과가 모두 이 안에 있음).

## 파일

| 파일 | 역할 |
|---|---|
| `.env` | 인증키 (커밋 제외) |
| `config.py` | 서비스명, `.env` 로딩, `data/` 경로 |
| `seoul_api.py` | API 클라이언트 (XML 파싱, 결과 코드 처리, 1,000건 단위 페이지 처리) |
| `check_services.py` | 이 폴더 API 점검 |
| `fetch_event_control.py` | 행사·집회 통제만 골라 진행 중/예정으로 정리 |
| `fetch_accidents.py` | 돌발정보 전체 저장 및 유형별 요약 |
| `fetch_cultural_events.py` | 문화행사 정보에서 마라톤 등 일정 검색 |
| `data/` | 실행 결과 (커밋 제외) |

## 준비

이 폴더 안에서 가상환경을 만들고 실행한다.

```bash
cd event_control
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
| 서비스명 | 어떤 데이터를 요청하는지 | `AccInfo` |
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

### 실시간 돌발정보 `AccInfo`
```
.../xml/AccInfo/1/1000/
```
- 추가값: 없음 (현재 진행 중이거나 예정된 돌발·통제 전부)
- TOPIS 교통통제 지도(topis.seoul.go.kr/map/openControlMap.do)와 같은 원천

| 필드 | 의미 | 예시 |
|---|---|---|
| `acc_id` | 돌발 ID | `1071788` |
| `occr_date` / `occr_time` | 시작 일시 | `20260407` / `1000` |
| `exp_clr_date` / `exp_clr_time` | 종료 예정 일시 | `20270301` / `000000` |
| `acc_type` | 대분류 코드 (`AccMainCode`로 이름 확인) | `A04` (공사) |
| `acc_dtype` | 세부유형 코드 (`AccSubCode`로 이름 확인) | `04B01` |
| `link_id` | 영향받는 도로 구간 (`LinkInfo`로 도로명 확인) | `1220031600` |
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

### 링크정보 `LinkInfo`
```
.../xml/LinkInfo/1/1/{링크ID}/
```
- 추가값: **링크ID**. 통제 구간이 어느 도로인지 확인하는 데 쓴다.

| 필드 | 의미 | 예시 |
|---|---|---|
| `road_name` | 도로 이름 | `봉은사로` |
| `st_node_nm` / `ed_node_nm` | 구간 시작·끝 지점 | `종합운동장삼거리` → `봉은교` |
| `map_dist` | 구간 길이 (m) | `291` |
| `reg_cd` | 자치구 코드 | `123` |

### 서울시 문화행사 정보 `culturalEventInfo` (확인 필요)
```
.../xml/culturalEventInfo/1/200/{분류}/{제목}/{날짜}/
```
- 추가값: 분류 / 제목 / 날짜. 비워둘 자리는 공백 한 칸.
- 서비스명, 파라미터 순서, 필드 이름은 아직 확인 전이다. `check_services.py`나 `fetch_cultural_events.py` 실행 결과로 확인한다.

## 데이터 연결

```
AccInfo (돌발·통제) ── acc_type / acc_dtype ──▶ AccMainCode / AccSubCode (유형 이름)
                    └─ link_id ───────────────▶ LinkInfo (도로명, 구간)
```

---

## 실행

### 1. 행사·집회 교통통제
```bash
python3 fetch_event_control.py --show-codes        # 유형 코드표 먼저 확인
python3 fetch_event_control.py                     # 행사·집회
python3 fetch_event_control.py --types 행사 집회 공사
```

처리 방식
1. 유형 코드표를 받아 `acc_type`, `acc_dtype`을 이름으로 바꾼다.
2. 유형 이름에 `--types` 단어(기본: 행사, 집회)가 들어간 건, 또는 설명에 해당 단어와 마라톤·대회·축제·통제 키워드가 함께 있는 건을 고른다.
3. 시작 일시가 지금(한국 시간)보다 뒤면 **예정**, 아니면 **진행 중**으로 나눈다.
4. `link_id`로 `LinkInfo`를 호출해 도로명과 구간을 붙인다.

결과: `data/event_control_YYYYMMDD_HHMM.csv`
(`status`, `start`, `end`, `type_nm`, `dtype_nm`, `road_name`, `section`, `link_id`, 좌표, `acc_id`, `acc_info`)

유형 코드표에 "행사"라는 이름이 정확히 없으면 `--show-codes` 결과를 보고 `--types`에 맞는 단어를 넣는다.

### 2. 돌발정보 전체
```bash
python3 fetch_accidents.py
```
유형별 건수와 행사·마라톤·집회·통제 키워드가 들어간 건을 출력한다.
결과: `data/accidents_YYYYMMDD_HHMM.csv`

### 3. 행사 일정 검색
```bash
python3 fetch_cultural_events.py --title 마라톤
python3 fetch_cultural_events.py --title 마라톤 --date 2026-11
```
결과: `data/cultural_events_{검색어}.csv`
문화행사 정보에 마라톤이 안 올라와 있을 수 있다. 그 경우 대회 일정은 서울시 교통통제 보도자료로 보완한다.

## 출처
서울특별시 TOPIS, 서울 열린데이터광장 (공공누리 1유형, 출처 표시)
