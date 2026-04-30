# News Bot

네이버 뉴스 검색 결과와 기관 보도자료를 수집하여, 새로 수집된 항목만 이메일로 발송하는 자동화 프로그램입니다.

현재 수집 대상은 다음과 같습니다.

- 네이버 뉴스 검색 결과
- 소방청 보도자료
- 인사혁신처 보도자료

중복 발송 방지를 위해 최근 발송한 URL은 `data/sent_articles.json`에 저장하며, 설정된 보관 기간이 지나면 자동 삭제됩니다.

---

## 1. 주요 기능

- 네이버 뉴스 검색어별 수집
- 언론사별 네이버 뉴스 수집
- 소방청 보도자료 수집
- 인사혁신처 보도자료 수집
- URL 기준 중복 제거
- 최근 발송 이력 7일 보관
- HTML 이메일 발송
- GitHub Actions를 통한 매일 자동 실행
- Gmail / 네이버웍스 SMTP 발송 지원

---

## 2. 폴더 구조

```text
news-bot/
├─ .github/                         # GitHub 관련 설정 폴더
│  └─ workflows/                    # GitHub Actions workflow 저장 폴더
│     └─ daily.yml                  # 매일 정해진 시간에 자동 실행되는 서버 실행 설정
│
├─ config/                          # 프로그램 운영 설정 파일 모음
│  ├─ config.yaml                   # 실제 운영 설정 파일
│  └─ config.example.yaml           # 샘플 설정 파일, 인수인계/초기 세팅용
│
├─ data/                            # 프로그램 실행 중 유지해야 하는 상태 데이터
│  └─ sent_articles.json            # 최근 발송한 기사/보도자료 URL 기록
│
├─ docs/                            # 사용법과 운영 문서
│  ├─ SETUP.md                      # 최초 설치, GitHub Secrets, SMTP 설정 가이드
│  └─ OPERATIONS.md                 # 검색어/언론사/실행시간/수신자 수정 방법
│
├─ src/                             # Python 소스 코드
│  ├─ main.py                       # 전체 실행 진입점
│  ├─ config_loader.py              # config.yaml 읽기, 날짜/검색어 설정 처리
│  ├─ crawler_runner.py             # crawler_type에 따라 알맞은 크롤러 선택 실행
│  ├─ deduplicator.py               # URL 기준 중복 제거
│  ├─ state_store.py                # sent_articles.json 읽기/쓰기/오래된 기록 삭제
│  ├─ renderer.py                   # 이메일 HTML 본문 생성
│  ├─ mailer.py                     # SMTP 이메일 발송
│  │
│  └─ crawlers/                     # 수집 대상별 크롤러 모음
│     ├─ __init__.py                # crawlers 폴더를 Python 패키지로 인식시키는 파일
│     ├─ naver_news.py              # 네이버 뉴스 검색 결과 크롤러
│     ├─ fire_agency.py             # 소방청 보도자료 페이지 크롤러
│     └─ mpm.py                     # 인사혁신처 보도자료 페이지 크롤러
│
├─ .env.example                     # 로컬 실행용 환경변수 샘플
├─ .gitignore                       # GitHub에 올리지 않을 파일 목록
├─ requirements.txt                 # Python 패키지 의존성 목록
└─ README.md                        # 프로젝트 개요, 실행법, 운영법 문서
```

---

## 3. 실행 흐름

1. `config/config.yaml` 파일을 읽습니다.
2. 실행일 기준으로 `start_date`와 `end_date`를 생성합니다.
3. 네이버 뉴스 검색어와 언론사 조합으로 검색 URL을 생성합니다.
4. 네이버 뉴스, 소방청, 인사혁신처 페이지를 크롤링합니다.
5. `data/sent_articles.json`에서 최근 발송 URL을 조회합니다.
6. URL 기준으로 이미 발송한 항목을 제거합니다.
7. 신규 항목만 HTML 이메일 본문으로 생성합니다.
8. SMTP를 통해 이메일을 발송합니다.
9. 발송에 성공하면 신규 URL을 `data/sent_articles.json`에 저장합니다.
10. 보관 기간이 지난 발송 이력은 자동 삭제합니다.

---

## 4. 중복 제거 정책

중복 제거 기준은 URL입니다.

같은 URL이면 같은 기사 또는 같은 보도자료로 판단합니다.

예를 들어 같은 기사가 `공무원` 검색 결과와 `소방` 검색 결과에 모두 잡히더라도, URL이 같으면 한 번만 발송됩니다.

발송 이력은 아래 파일에 저장됩니다.

`data/sent_articles.json`

기본 보관 기간은 7일입니다.

```yaml
deduplication:
  retention_days: 7
  key: "link"
```

보관 기간이 지난 기록은 다음 실행 시 자동 삭제됩니다.

---

## 5. 환경변수

로컬 실행 시 프로젝트 루트에 `.env` 파일을 만듭니다.

```env
CRAWLER_HEADLESS=false

SMTP_HOST=smtp.worksmobile.com
SMTP_PORT=587
SMTP_USER=your_email@company.com
SMTP_PASSWORD=external_app_password
EMAIL_TO=receiver@company.com
```

네이버웍스 SMTP를 사용할 경우 아래처럼 설정합니다.

```env
SMTP_HOST=smtp.worksmobile.com
SMTP_PORT=587
SMTP_USER=your_email@company.com
SMTP_PASSWORD=네이버웍스_외부앱_비밀번호
EMAIL_TO=receiver@company.com
```

Gmail SMTP를 사용할 경우 아래처럼 설정합니다.

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=team.account@gmail.com
SMTP_PASSWORD=구글_앱_비밀번호
EMAIL_TO=receiver@company.com
```

---

## 6. 설치 및 로컬 실행

가상환경을 생성합니다.

```bash
python -m venv .venv
```

가상환경을 활성화합니다.

Windows:

```bash
.venv\Scripts\activate
```

Mac/Linux:

```bash
source .venv/bin/activate
```

필요한 Python 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

Playwright 브라우저를 설치합니다.

```bash
playwright install chromium
```

회사 네트워크에서 SSL 인증서 오류가 발생하면 아래 명령어로 우회 설치할 수 있습니다.

```bash
set NODE_TLS_REJECT_UNAUTHORIZED=0
playwright install chromium
```

프로그램을 실행합니다.

```bash
python -m src.main
```

---

## 7. config.yaml 설정

운영 설정은 `config/config.yaml`에서 관리합니다.

```yaml
schedule:
  timezone: "Asia/Seoul"
  run_time: "11:00"

date:
  mode: "relative"
  start_offset_days: -1
  end_offset_days: 0
  format: "%Y.%m.%d"

deduplication:
  retention_days: 7
  key: "link"

crawler:
  max_scroll_attempts: 30
  scroll_wait_ms: 2000

mail:
  subject_prefix: "[뉴스 모니터링]"
  sender_name: "뉴스 자동 발송봇"
  include_empty_jobs: true
```

각 설정의 의미는 아래와 같습니다.

| 설정 | 의미 |
|---|---|
| `schedule.timezone` | 날짜 계산 기준 시간대 |
| `schedule.run_time` | 운영자가 확인하기 위한 실행 시간 표기 |
| `date.start_offset_days` | 검색 시작일. 실행일 기준 며칠 전인지 설정 |
| `date.end_offset_days` | 검색 종료일. 실행일 기준 며칠 후/당일인지 설정 |
| `deduplication.retention_days` | 발송 이력 보관 기간 |
| `crawler.max_scroll_attempts` | 네이버 뉴스 스크롤 최대 시도 횟수 |
| `crawler.scroll_wait_ms` | 스크롤 후 대기 시간 |
| `mail.subject_prefix` | 이메일 제목 앞부분 |
| `mail.include_empty_jobs` | 신규 항목이 없는 섹션도 메일에 표시할지 여부 |

---

## 8. 네이버 뉴스 설정

네이버 뉴스는 검색어와 언론사 코드를 조합하여 URL을 자동 생성합니다.

```yaml
naver_news:
  keywords:
    - "공무원"

  limit: 30

  common_params:
    ssc: "tab.news.all"
    sm: "tab_opt"
    sort: "0"
    photo: "0"
    field: "0"
    pd: "4"
    docid: ""
    related: "0"
    mynews: "1"
    office_type: "2"
    nso: "so:r,p:1d"
    is_sug_officeid: "0"
    office_category: "0"
    service_area: "0"

  sources:
    - name: "뉴시스"
      press: "뉴시스"
      office_section_code: "2"
      news_office_checked: "1003"

    - name: "법률저널"
      press: "법률저널"
      office_section_code: "8"
      news_office_checked: "2144"
```

`keywords`에는 검색어를 입력합니다.

`sources`에는 수집할 언론사 정보를 입력합니다.

`news_office_checked`는 네이버 뉴스에서 사용하는 언론사 코드입니다.

`office_section_code`는 네이버 뉴스 URL에 포함되는 언론사 분류 코드입니다.

---

## 9. 검색어 추가 방법

검색어는 `naver_news.keywords`에 추가합니다.

```yaml
naver_news:
  keywords:
    - "공무원"
    - "소방"
    - "소방공무원"
```

검색어가 여러 개면 각각 별도로 검색합니다.

예를 들어 검색어가 `공무원`, `소방`이고 언론사가 `뉴시스`, `법률저널`이면 아래 조합으로 실행됩니다.

- 뉴시스 + 공무원
- 뉴시스 + 소방
- 법률저널 + 공무원
- 법률저널 + 소방

즉, `공무원, 소방`을 한 번에 검색하는 것이 아니라 검색어별로 각각 검색합니다.

---

## 10. 네이버 언론사 코드 찾는 법

네이버 뉴스에서 특정 언론사만 수집하려면 아래 두 값이 필요합니다.

- `news_office_checked`
- `office_section_code`

찾는 순서는 아래와 같습니다.

1. 네이버에서 원하는 검색어로 뉴스 검색을 합니다.
2. 검색 옵션을 엽니다.
3. 언론사를 선택합니다.
4. 원하는 언론사를 체크합니다.
5. 검색 결과 URL을 복사합니다.
6. URL에서 아래 값을 확인합니다.

```text
news_office_checked=XXXX
office_section_code=Y
```

예를 들어 URL에 아래 값이 있으면:

```text
news_office_checked=1003
office_section_code=2
```

config에는 이렇게 입력합니다.

```yaml
- name: "뉴시스"
  press: "뉴시스"
  office_section_code: "2"
  news_office_checked: "1003"
```

검색어는 URL의 `query=` 값을 직접 복사하지 않습니다.

URL에는 아래처럼 보일 수 있습니다.

```text
query=%EA%B3%B5%EB%AC%B4%EC%9B%90
```

이 값은 `공무원`이 URL 인코딩된 형태입니다.

config에는 한글 검색어를 그대로 입력합니다.

```yaml
keywords:
  - "공무원"
```

프로그램이 자동으로 URL 인코딩합니다.

---

## 11. 보도자료 설정

소방청과 인사혁신처 보도자료는 `press_release.sources`에서 관리합니다.

```yaml
press_release:
  sources:
    - name: "소방청"
      crawler_type: "fire_agency"
      url: "https://www.nfa.go.kr/nfa/news/pressrelease/press/"
      limit: 30
      enabled: true

    - name: "인사혁신처"
      crawler_type: "mpm"
      url: "https://www.mpm.go.kr/mpm/comm/newsPress/newsPressRelease/"
      limit: 30
      enabled: true
```

각 설정의 의미는 아래와 같습니다.

| 설정 | 의미 |
|---|---|
| `name` | 메일에 표시할 기관명 |
| `crawler_type` | 사용할 크롤러 종류 |
| `url` | 보도자료 목록 페이지 URL |
| `limit` | 최대 수집 개수 |
| `enabled` | 수집 여부 |

`enabled: false`로 설정하면 해당 크롤러는 실행하지 않습니다.

---

## 12. 이메일 양식

메일 상단은 아래 형식으로 생성됩니다.

```text
[뉴스,보도자료] 2026.04.30

뉴스 : 뉴시스(3건), 법률저널(2건), 서울신문(0건), ...
↳ 검색어 : 공무원
↳ 기간 : 2026.04.29 ~ 2026.04.30
보도자료 : 소방청(2건), 인사혁신처(1건)

뉴스 및 보도자료 수집 결과(총 n건)입니다.
```

뉴스사명과 기관명에는 링크가 걸립니다.

- 뉴스사명 클릭: 해당 네이버 뉴스 검색 URL로 이동
- 소방청 클릭: 소방청 보도자료 목록으로 이동
- 인사혁신처 클릭: 인사혁신처 보도자료 목록으로 이동

메일 본문에는 섹션별로 신규 항목이 표시됩니다.

네이버 뉴스는 아래 형식으로 표시됩니다.

```text
[메인] [언론사명] 기사 제목
↳ [관련] [언론사명] 관련 기사 제목
```

보도자료는 아래 형식으로 표시됩니다.

```text
[보도자료] [기관명 / 등록일] 보도자료 제목
```

---

## 13. GitHub Actions 자동 실행

자동 실행 설정 파일은 아래에 있습니다.

```text
.github/workflows/daily.yml
```

한국시간 오전 11시에 실행하려면 cron은 UTC 기준으로 설정합니다.

```yaml
schedule:
  - cron: "0 2 * * *"
```

UTC 02:00은 한국시간 11:00입니다.

수동 실행은 GitHub에서 아래 경로로 진행합니다.

```text
Repository
→ Actions
→ Daily News Bot
→ Run workflow
```

---

## 14. GitHub Secrets

GitHub Actions에서 이메일 발송을 하려면 Repository secrets에 아래 값을 등록해야 합니다.

경로:

```text
Settings
→ Secrets and variables
→ Actions
→ Repository secrets
```

등록할 값은 아래와 같습니다.

| Name | Value |
|---|---|
| `SMTP_HOST` | `smtp.worksmobile.com` 또는 `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | 발신 메일 주소 |
| `SMTP_PASSWORD` | 외부 앱 비밀번호 |
| `EMAIL_TO` | 수신자 메일 주소 |

여러 명에게 보내려면 쉼표로 구분합니다.

```text
a@company.com,b@company.com
```

주의할 점은 `Value`에는 값만 입력해야 한다는 것입니다.

예를 들어 `SMTP_HOST`의 Value에는 아래처럼 입력합니다.

```text
smtp.worksmobile.com
```

아래처럼 입력하면 안 됩니다.

```text
SMTP_HOST=smtp.worksmobile.com
```

---

## 15. GitHub Actions에서 발송 이력 저장

`data/sent_articles.json`은 실행 후 변경됩니다.

GitHub Actions가 이 파일을 다시 repository에 저장하려면 workflow에 아래 권한이 필요합니다.

```yaml
permissions:
  contents: write
```

그리고 실행 후 commit 단계가 필요합니다.

```yaml
- name: Commit updated sent articles
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add data/sent_articles.json
    git diff --cached --quiet || git commit -m "Update sent articles"
    git push
```

이 단계가 없으면 GitHub Actions 실행 중에는 중복 이력이 저장되지만, 다음 실행에는 반영되지 않을 수 있습니다.

---

## 16. Git에 올리지 말아야 할 파일

`.gitignore`에는 아래 항목을 포함합니다.

```gitignore
.venv/
.env
__pycache__/
*.pyc
```

특히 `.env`는 SMTP 비밀번호가 들어 있으므로 절대 GitHub에 올리지 않습니다.

GitHub Actions에서는 `.env` 대신 Repository secrets를 사용합니다.

---

## 17. 자주 수정하는 항목

검색어를 추가하려면 `naver_news.keywords`를 수정합니다.

```yaml
naver_news:
  keywords:
    - "공무원"
    - "소방"
```

언론사를 추가하려면 `naver_news.sources`를 수정합니다.

```yaml
naver_news:
  sources:
    - name: "새 언론사"
      press: "새 언론사"
      office_section_code: "2"
      news_office_checked: "XXXX"
```

보도자료 수집을 끄려면 `enabled` 값을 `false`로 바꿉니다.

```yaml
enabled: false
```

네이버 뉴스 기사 수를 바꾸려면 `naver_news.limit`을 수정합니다.

```yaml
naver_news:
  limit: 50
```

보도자료 수집 개수를 바꾸려면 각 기관의 `limit`을 수정합니다.

```yaml
press_release:
  sources:
    - name: "소방청"
      limit: 50
```

중복 보관 기간을 바꾸려면 `deduplication.retention_days`를 수정합니다.

```yaml
deduplication:
  retention_days: 7
```

수신자를 변경하려면 GitHub Secrets의 `EMAIL_TO` 값을 수정합니다.

---

## 18. 장애 대응

메일 발송이 실패하면 아래 값을 먼저 확인합니다.

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `EMAIL_TO`

네이버웍스 기본 SMTP 설정은 아래와 같습니다.

```text
SMTP_HOST=smtp.worksmobile.com
SMTP_PORT=587
```

Gmail 기본 SMTP 설정은 아래와 같습니다.

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

Playwright 실행이 실패하면 아래 명령어가 실행되었는지 확인합니다.

```bash
playwright install chromium
```

네이버 뉴스가 수집되지 않으면 네이버 검색 결과 HTML 구조가 바뀌었을 수 있습니다.

이 경우 아래 파일의 selector 수정이 필요합니다.

```text
src/crawlers/naver_news.py
```

소방청 또는 인사혁신처가 수집되지 않으면 기관 홈페이지 HTML 구조가 바뀌었을 수 있습니다.

이 경우 아래 파일의 selector를 확인합니다.

```text
src/crawlers/fire_agency.py
src/crawlers/mpm.py
```

중복 제거가 작동하지 않으면 아래 파일을 확인합니다.

```text
data/sent_articles.json
src/state_store.py
src/deduplicator.py
```

GitHub Actions에서 실행한 경우, `sent_articles.json` 변경사항이 commit/push 되는지도 확인합니다.

GitHub Actions에서 아래 오류가 발생하면 Secrets 값이 잘못 입력된 경우가 많습니다.

```text
ValueError: invalid literal for int() with base 10: '***'
```

이 경우 `SMTP_PORT`의 Value가 `587`인지 확인합니다.

아래처럼 입력하면 안 됩니다.

```text
SMTP_PORT=587
```

아래처럼 값만 입력해야 합니다.

```text
587
```

---

## 19. 라이선스

Internal use only.
