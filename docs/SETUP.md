# SETUP

News Bot을 처음 설치하고 실행하기 위한 설정 문서입니다.

---

## 1. 로컬 실행 준비

프로젝트 폴더로 이동합니다.

```bash
cd "C:\Users\mjjeong\Desktop\개발\운영용 뉴스 수집 시스템\news-bot"
```

가상환경을 생성합니다.

```bash
python -m venv .venv
```

가상환경을 활성화합니다.

```bash
.venv\Scripts\activate
```

필요한 패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

---

## 2. Playwright 브라우저 설치

크롤러는 Playwright Chromium을 사용합니다.

```bash
playwright install chromium
```

회사 네트워크에서 SSL 인증서 오류가 발생하면 아래 명령어를 사용합니다.

```bash
set NODE_TLS_REJECT_UNAUTHORIZED=0
playwright install chromium
```

---

## 3. .env 파일 생성

프로젝트 루트에 `.env` 파일을 만듭니다.

```env
CRAWLER_HEADLESS=false

SMTP_HOST=smtp.worksmobile.com
SMTP_PORT=587
SMTP_USER=your_email@company.com
SMTP_PASSWORD=external_app_password
EMAIL_TO=receiver@company.com
```

브라우저 창을 숨기려면 아래처럼 설정합니다.

```env
CRAWLER_HEADLESS=true
```

---

## 4. SMTP 설정

네이버웍스 사용 시:

```env
SMTP_HOST=smtp.worksmobile.com
SMTP_PORT=587
SMTP_USER=your_email@company.com
SMTP_PASSWORD=네이버웍스_외부앱_비밀번호
EMAIL_TO=receiver@company.com
```

Gmail 사용 시:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=team.account@gmail.com
SMTP_PASSWORD=구글_앱_비밀번호
EMAIL_TO=receiver@company.com
```

SMTP 비밀번호는 일반 로그인 비밀번호가 아니라 외부 앱 비밀번호를 사용합니다.

---

## 5. 로컬 실행 테스트

전체 실행:

```bash
python -m src.main
```

일부 크롤러만 테스트:

```bash
python -c "from src.config_loader import load_config; from src.crawler_runner import run_all_crawlers; c=load_config(); crawler_config=c.get('crawler', {}); crawler_config['headless']=False; results=run_all_crawlers(c['jobs'][:2], crawler_config); print(len(results)); print(results[0]['articles'][0])"
```

---

## 6. GitHub Repository 연결

초기 commit:

```bash
git init
git branch -M main
git add .
git commit -m "Initial commit"
```

원격 repository 연결:

```bash
git remote add origin https://github.com/OWNER/news-bot.git
git push -u origin main
```

이미 `origin`이 잘못 등록되어 있으면 수정합니다.

```bash
git remote set-url origin https://github.com/OWNER/news-bot.git
```

---

## 7. GitHub Secrets 등록

GitHub repository에서 아래 경로로 이동합니다.

```text
Settings
→ Secrets and variables
→ Actions
→ Repository secrets
```

등록할 값:

| Name | Value |
|---|---|
| `SMTP_HOST` | `smtp.worksmobile.com` 또는 `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | 발신 메일 주소 |
| `SMTP_PASSWORD` | 외부 앱 비밀번호 |
| `EMAIL_TO` | 수신자 메일 주소 |

주의: Value에는 값만 입력합니다.

예:

```text
smtp.worksmobile.com
```

아래처럼 입력하지 않습니다.

```text
SMTP_HOST=smtp.worksmobile.com
```

---

## 8. GitHub Actions 확인

workflow 파일 위치:

```text
.github/workflows/daily.yml
```

수동 실행:

```text
GitHub Repository
→ Actions
→ Daily News Bot
→ Run workflow
```

한국시간 오전 11시에 자동 실행하려면 cron은 UTC 기준으로 아래와 같이 설정합니다.

```yaml
schedule:
  - cron: "0 2 * * *"
```

---

## 9. 발송 이력 파일 확인

발송 성공 후 아래 파일이 갱신됩니다.

```text
data/sent_articles.json
```

초기 상태:

```json
{
  "sent_articles": []
}
```

GitHub Actions에서 실행한 경우, workflow가 이 파일을 다시 commit/push 해야 다음 실행에서 중복 제거가 유지됩니다.
