# OPERATIONS

News Bot 운영 중 자주 변경하는 설정과 장애 대응 절차를 정리한 문서입니다.

---

## 1. 운영 설정 파일

운영 설정은 아래 파일에서 관리합니다.

```text
config/config.yaml
```

주요 설정 범위는 다음과 같습니다.

- 검색어
- 네이버 뉴스 언론사
- 소방청 / 인사혁신처 보도자료 수집 여부
- 수집 개수
- 중복 발송 이력 보관 기간
- 메일 제목 prefix
- 실행 날짜 범위

---

## 2. 검색어 추가 또는 삭제

검색어는 `naver_news.keywords`에서 관리합니다.

```yaml
naver_news:
  keywords:
    - "공무원"
    - "소방"
    - "교도소 출소"
```

검색어를 추가하면 모든 네이버 뉴스 매체에 대해 해당 검색어가 각각 실행됩니다.

예를 들어 검색어가 `공무원`, `소방`이고 매체가 `뉴시스`, `법률저널`이면 아래 조합으로 크롤링합니다.

```text
뉴시스 + 공무원
뉴시스 + 소방
법률저널 + 공무원
법률저널 + 소방
```

검색어를 삭제하려면 해당 줄을 제거합니다.

---

## 3. 네이버 뉴스 언론사 추가

네이버 뉴스 언론사는 `naver_news.sources`에 추가합니다.

```yaml
naver_news:
  sources:
    - name: "새 언론사"
      press: "새 언론사"
      office_section_code: "2"
      news_office_checked: "XXXX"
```

필수 값은 다음과 같습니다.

| 항목 | 의미 |
|---|---|
| `name` | 메일과 로그에 표시할 이름 |
| `press` | 기사 출처명 |
| `office_section_code` | 네이버 뉴스 URL의 언론사 분류 코드 |
| `news_office_checked` | 네이버 뉴스 언론사 코드 |

---

## 4. 네이버 언론사 코드 찾는 법

네이버 뉴스에서 특정 언론사만 수집하려면 아래 두 값이 필요합니다.

- `news_office_checked`
- `office_section_code`

찾는 절차는 다음과 같습니다.

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

검색어는 URL의 `query=` 값을 복사하지 않습니다.

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

프로그램이 실행 시 자동으로 URL 인코딩합니다.

---

## 5. 네이버 뉴스 수집 개수 변경

네이버 뉴스 수집 개수는 `naver_news.limit`에서 변경합니다.

```yaml
naver_news:
  limit: 30
```

예를 들어 매체별 검색어당 50건까지 수집하려면 아래처럼 바꿉니다.

```yaml
naver_news:
  limit: 50
```

주의: 검색어와 언론사가 많을수록 실행 시간이 길어집니다.

---

## 6. 보도자료 수집 켜기 또는 끄기

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

수집을 끄려면 `enabled`를 `false`로 바꿉니다.

```yaml
enabled: false
```

수집을 다시 켜려면 `true`로 바꿉니다.

```yaml
enabled: true
```

---

## 7. 보도자료 수집 개수 변경

기관별 `limit` 값을 수정합니다.

```yaml
press_release:
  sources:
    - name: "소방청"
      limit: 30
```

예를 들어 소방청 보도자료를 50개까지 수집하려면 아래처럼 바꿉니다.

```yaml
press_release:
  sources:
    - name: "소방청"
      limit: 50
```

---

## 8. 수집 기간 변경

수집 기간은 `date` 설정에서 관리합니다.

```yaml
date:
  mode: "relative"
  start_offset_days: -1
  end_offset_days: 0
  format: "%Y.%m.%d"
```

현재 설정의 의미는 다음과 같습니다.

| 설정 | 의미 |
|---|---|
| `start_offset_days: -1` | 실행일 기준 전날 |
| `end_offset_days: 0` | 실행일 당일 |
| `format: "%Y.%m.%d"` | 네이버 뉴스 URL에 들어가는 날짜 형식 |

예를 들어 2026.04.30에 실행하면 아래 기간으로 검색합니다.

```text
2026.04.29 ~ 2026.04.30
```

2일 전부터 당일까지 검색하려면 아래처럼 바꿉니다.

```yaml
date:
  start_offset_days: -2
  end_offset_days: 0
```

---

## 9. 중복 발송 이력 보관 기간 변경

중복 제거용 발송 이력은 `data/sent_articles.json`에 저장됩니다.

보관 기간은 `deduplication.retention_days`에서 관리합니다.

```yaml
deduplication:
  retention_days: 7
  key: "link"
```

예를 들어 14일간 보관하려면 아래처럼 바꿉니다.

```yaml
deduplication:
  retention_days: 14
```

보관 기간이 지난 기록은 다음 실행 시 자동 삭제됩니다.

---

## 10. 수신자 변경

수신자는 환경변수 `EMAIL_TO`에서 관리합니다.

로컬 실행 시에는 `.env` 파일을 수정합니다.

```env
EMAIL_TO=receiver@company.com
```

여러 명에게 보내려면 쉼표로 구분합니다.

```env
EMAIL_TO=a@company.com,b@company.com,c@company.com
```

GitHub Actions에서는 Repository secrets의 `EMAIL_TO` 값을 수정합니다.

경로:

```text
Settings
→ Secrets and variables
→ Actions
→ Repository secrets
→ EMAIL_TO
```

---

## 11. 발신 메일 계정 변경

발신 계정은 아래 환경변수로 관리합니다.

```env
SMTP_HOST=smtp.worksmobile.com
SMTP_PORT=587
SMTP_USER=your_email@company.com
SMTP_PASSWORD=external_app_password
```

네이버웍스 SMTP 예시:

```env
SMTP_HOST=smtp.worksmobile.com
SMTP_PORT=587
SMTP_USER=your_email@company.com
SMTP_PASSWORD=네이버웍스_외부앱_비밀번호
```

Gmail SMTP 예시:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=team.account@gmail.com
SMTP_PASSWORD=구글_앱_비밀번호
```

SMTP 비밀번호는 일반 로그인 비밀번호가 아니라 외부 앱 비밀번호를 사용합니다.

---

## 12. 실행 시간 변경

GitHub Actions 자동 실행 시간은 아래 파일에서 관리합니다.

```text
.github/workflows/daily.yml
```

한국시간 오전 11시에 실행하려면 cron은 UTC 기준으로 아래와 같습니다.

```yaml
schedule:
  - cron: "0 2 * * *"
```

한국시간과 UTC의 관계:

```text
KST = UTC + 9
```

예를 들어 한국시간 오전 9시에 실행하려면 UTC 00:00입니다.

```yaml
schedule:
  - cron: "0 0 * * *"
```

한국시간 오후 6시에 실행하려면 UTC 09:00입니다.

```yaml
schedule:
  - cron: "0 9 * * *"
```

---

## 13. GitHub Actions 수동 실행

수동 실행 경로:

```text
GitHub Repository
→ Actions
→ Daily News Bot
→ Run workflow
```

수동 실행 후 확인할 것:

1. 크롤링 성공 여부
2. 메일 발송 성공 여부
3. `data/sent_articles.json` 변경 여부
4. 변경된 `sent_articles.json`이 commit/push 되었는지 여부

---

## 14. 발송 이력 초기화

중복 발송 이력을 초기화하려면 `data/sent_articles.json`을 아래처럼 비웁니다.

```json
{
  "sent_articles": []
}
```

주의: 이 파일을 초기화하면 최근에 발송했던 기사도 다시 발송될 수 있습니다.

---

## 15. 로컬 테스트 명령어

프로젝트 폴더로 이동합니다.

```bash
cd "C:\Users\mjjeong\Desktop\개발\운영용 뉴스 수집 시스템\news-bot"
```

가상환경을 활성화합니다.

```bash
.venv\Scripts\activate
```

전체 실행:

```bash
python -m src.main
```

일부 크롤러만 테스트:

```bash
python -c "from src.config_loader import load_config; from src.crawler_runner import run_all_crawlers; c=load_config(); crawler_config=c.get('crawler', {}); crawler_config['headless']=False; results=run_all_crawlers(c['jobs'][:2], crawler_config); print(len(results)); print(results[0]['articles'][0])"
```

브라우저 창을 보이게 하려면 `.env`에 아래 값을 둡니다.

```env
CRAWLER_HEADLESS=false
```

브라우저 창을 숨기려면 아래처럼 바꿉니다.

```env
CRAWLER_HEADLESS=true
```

---

## 16. 장애 대응

### 16.1 메일 발송 실패

확인할 값:

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `EMAIL_TO`

네이버웍스 기본값:

```text
SMTP_HOST=smtp.worksmobile.com
SMTP_PORT=587
```

Gmail 기본값:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
```

`SMTP_PORT`는 값만 입력해야 합니다.

올바른 예:

```text
587
```

잘못된 예:

```text
SMTP_PORT=587
```

---

### 16.2 Playwright 브라우저 오류

아래 명령어를 실행했는지 확인합니다.

```bash
playwright install chromium
```

회사 네트워크에서 SSL 인증서 오류가 발생하면 아래 명령어를 사용합니다.

```bash
set NODE_TLS_REJECT_UNAUTHORIZED=0
playwright install chromium
```

---

### 16.3 소방청 또는 인사혁신처 접속 실패

기관 사이트에서 일시적으로 연결을 닫을 수 있습니다.

대표 오류:

```text
Page.goto: net::ERR_CONNECTION_CLOSED
```

대응 방법:

1. 잠시 후 다시 실행합니다.
2. 해당 기관 URL을 브라우저에서 직접 열어봅니다.
3. 계속 실패하면 해당 기관의 `enabled`를 임시로 `false`로 바꿉니다.
4. 크롤러의 재시도 로직을 확인합니다.

임시로 소방청 수집을 끄는 예:

```yaml
- name: "소방청"
  crawler_type: "fire_agency"
  enabled: false
```

---

### 16.4 네이버 뉴스 수집 결과가 비정상적임

가능한 원인:

- 네이버 검색 결과 HTML 구조 변경
- selector 변경 필요
- 네이버 접속 차단 또는 일시적 로딩 실패
- 검색어 또는 언론사 코드 오류

확인 파일:

```text
src/crawlers/naver_news.py
```

확인할 config:

```yaml
news_office_checked: "1003"
office_section_code: "2"
```

---

### 16.5 중복 제거가 작동하지 않음

확인할 파일:

```text
data/sent_articles.json
src/state_store.py
src/deduplicator.py
```

GitHub Actions에서 실행하는 경우에는 `daily.yml`에 아래 권한이 있어야 합니다.

```yaml
permissions:
  contents: write
```

그리고 실행 후 commit 단계가 있어야 합니다.

```yaml
- name: Commit updated sent articles
  run: |
    git config user.name "github-actions[bot]"
    git config user.email "github-actions[bot]@users.noreply.github.com"
    git add data/sent_articles.json
    git diff --cached --quiet || git commit -m "Update sent articles"
    git push
```

---

## 17. 운영 변경 후 반영 절차

코드를 수정하거나 config를 바꾼 뒤 아래 순서로 반영합니다.

```bash
git status
git add .
git commit -m "Update news bot configuration"
git push
```

GitHub에 push하면 다음 예약 실행부터 반영됩니다.

즉시 확인하려면 GitHub Actions에서 수동 실행합니다.

```text
Actions
→ Daily News Bot
→ Run workflow
```

---

## 18. 권장 운영 방식

- 검색어는 너무 많이 늘리지 않습니다.
- 신규 언론사를 추가할 때는 로컬에서 먼저 테스트합니다.
- `data/sent_articles.json`은 임의로 삭제하지 않습니다.
- SMTP 비밀번호는 `.env`나 GitHub Secrets에만 저장합니다.
- `.env`는 GitHub에 올리지 않습니다.
- 기관 사이트 접속 오류는 일시적일 수 있으므로 재시도 후 판단합니다.
