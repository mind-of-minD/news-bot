from datetime import datetime
from html import escape
from typing import Dict, List
from zoneinfo import ZoneInfo


Article = Dict[str, str]
JobResult = Dict[str, object]


def build_email_subject(config: dict) -> str:
    mail_config = config.get("mail", {})
    schedule_config = config.get("schedule", {})

    subject_prefix = mail_config.get("subject_prefix", "[뉴스 모니터링]")
    timezone = schedule_config.get("timezone", "Asia/Seoul")
    today = datetime.now(ZoneInfo(timezone)).strftime("%Y.%m.%d")

    return f"{subject_prefix} {today}"


def build_email_html(config: dict, job_results: List[JobResult]) -> str:
    mail_config = config.get("mail", {})
    include_empty_jobs = bool(mail_config.get("include_empty_jobs", True))

    schedule_config = config.get("schedule", {})
    timezone = schedule_config.get("timezone", "Asia/Seoul")
    today = datetime.now(ZoneInfo(timezone)).strftime("%Y.%m.%d")

    runtime = config.get("runtime", {})
    start_date = runtime.get("start_date", "")
    end_date = runtime.get("end_date", "")

    keywords = _collect_keywords(job_results)
    total_count = _count_total_articles(job_results)

    html = f"""
    <html>
      <body style="font-family: Arial, 'Malgun Gothic', sans-serif; line-height: 1.6; color: #222;">
        <h2>{escape(f"[뉴스,보도자료] {today}")}</h2>

        {_render_news_summary_by_keyword(job_results, keywords, start_date, end_date)}
        {_render_press_release_summary(job_results)}

        <p>뉴스 및 보도자료 수집 결과(총 {total_count}건)입니다.</p>

        <h3>상세 수집 결과</h3>
        {_render_detail_results(job_results, include_empty_jobs)}
      </body>
    </html>
    """

    return html


def _collect_keywords(job_results: List[JobResult]) -> List[str]:
    keywords: List[str] = []

    for job_result in job_results:
        if str(job_result.get("crawler_type", "")) != "naver_news":
            continue

        keyword = str(job_result.get("keyword", "")).strip()

        if keyword and keyword not in keywords:
            keywords.append(keyword)

    return keywords


def _count_total_articles(job_results: List[JobResult]) -> int:
    return sum(len(job_result.get("articles", [])) for job_result in job_results)


def _render_news_summary_by_keyword(
    job_results: List[JobResult],
    keywords: List[str],
    start_date: str,
    end_date: str,
) -> str:
    if not keywords:
        return ""

    html = ""

    for keyword in keywords:
        items = []

        for job_result in job_results:
            if str(job_result.get("crawler_type", "")) != "naver_news":
                continue

            if str(job_result.get("keyword", "")).strip() != keyword:
                continue

            source = str(job_result.get("source", "")).strip()
            url = str(job_result.get("url", "")).strip()
            count = len(job_result.get("articles", []))

            if not source:
                source = str(job_result.get("job_name", "")).strip()

            items.append(
                _render_summary_link(
                    label=f"{source}({count}건)",
                    url=url,
                )
            )

        news_line = ", ".join(items) if items else "-"

        html += f"""
        <div style="margin: 0 0 16px 0;">
          <p style="margin: 0 0 4px 0;">
            <strong>뉴스 :</strong> {news_line}
          </p>
          <p style="margin: 0 0 4px 24px;">
            ↳ <strong>검색어 :</strong> {escape(keyword)}
          </p>
          <p style="margin: 0 0 4px 24px;">
            ↳ <strong>기간 :</strong> {escape(start_date)} ~ {escape(end_date)}
          </p>
        </div>
        """

    return html


def _render_press_release_summary(job_results: List[JobResult]) -> str:
    items = []

    for job_result in job_results:
        crawler_type = str(job_result.get("crawler_type", ""))

        if crawler_type not in ("fire_agency", "mpm"):
            continue

        source = str(job_result.get("source", "")).strip()
        url = str(job_result.get("url", "")).strip()
        count = len(job_result.get("articles", []))

        if not source:
            source = str(job_result.get("job_name", "")).strip()

        items.append(
            _render_summary_link(
                label=f"{source}({count}건)",
                url=url,
            )
        )

    press_line = ", ".join(items) if items else "-"

    return f"""
    <div style="margin: 0 0 16px 0;">
      <p style="margin: 0 0 4px 0;">
        <strong>보도자료 :</strong> {press_line}
      </p>
    </div>
    """


def _render_summary_link(label: str, url: str) -> str:
    safe_label = escape(label)
    safe_url = escape(url)

    if not safe_url:
        return safe_label

    return f'<a href="{safe_url}" target="_blank">{safe_label}</a>'


def _render_detail_results(
    job_results: List[JobResult],
    include_empty_jobs: bool,
) -> str:
    news_by_keyword = _group_news_articles_by_keyword(job_results)
    press_articles = _collect_press_release_articles(job_results)

    html = ""

    for keyword, articles in news_by_keyword.items():
        html += f"""
        <h4 style="margin-bottom: 6px;">[뉴스] {escape(keyword)}</h4>
        """

        if not articles:
            if include_empty_jobs:
                html += "<p>수집된 신규 항목이 없습니다.</p>"
            continue

        html += "<ol>"

        for article in articles:
            html += _render_article(article)

        html += "</ol>"

    html += """
    <h4 style="margin-bottom: 6px;">[보도자료]</h4>
    """

    if not press_articles:
        if include_empty_jobs:
            html += "<p>수집된 신규 항목이 없습니다.</p>"
    else:
        html += "<ol>"

        for article in press_articles:
            html += _render_article(article)

        html += "</ol>"

    return html


def _group_news_articles_by_keyword(
    job_results: List[JobResult],
) -> Dict[str, List[Article]]:
    grouped: Dict[str, List[Article]] = {}

    for job_result in job_results:
        if str(job_result.get("crawler_type", "")) != "naver_news":
            continue

        keyword = str(job_result.get("keyword", "")).strip() or "검색어 없음"

        if keyword not in grouped:
            grouped[keyword] = []

        articles = job_result.get("articles", [])
        grouped[keyword].extend(articles)

    return grouped


def _collect_press_release_articles(
    job_results: List[JobResult],
) -> List[Article]:
    articles: List[Article] = []

    for job_result in job_results:
        crawler_type = str(job_result.get("crawler_type", ""))

        if crawler_type not in ("fire_agency", "mpm"):
            continue

        articles.extend(job_result.get("articles", []))

    return articles


def _render_article(article: Article) -> str:
    title = escape(article.get("title", ""))
    link = escape(article.get("link", ""))
    source = escape(article.get("source", ""))
    item_type = article.get("item_type", "main")
    source_type = article.get("source_type", "")
    published_at = escape(article.get("published_at", ""))

    if source_type in ("fire_agency", "mpm"):
        date_text = f" / {published_at}" if published_at else ""

        return f"""
        <li style="margin-bottom: 6px;">
          <strong>[보도자료]</strong>
          <span>[{source}{date_text}]</span>
          <a href="{link}" target="_blank">{title}</a>
        </li>
        """

    if item_type == "related":
        return f"""
        <li style="margin-left: 24px; color: #555;">
          ↳ <strong>[관련]</strong>
          <span>[{source}]</span>
          <a href="{link}" target="_blank">{title}</a>
        </li>
        """

    return f"""
    <li style="margin-bottom: 6px;">
      <strong>[메인]</strong>
      <span>[{source}]</span>
      <a href="{link}" target="_blank">{title}</a>
    </li>
    """