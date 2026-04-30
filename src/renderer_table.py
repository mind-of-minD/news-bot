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
    news_summary = _build_news_summary(job_results, keywords)
    press_summary = _build_press_release_summary(job_results)

    news_total = sum(row["total"] for row in news_summary)
    press_total = sum(row["count"] for row in press_summary)
    total_count = news_total + press_total

    html = f"""
    <html>
      <body style="font-family: Arial, 'Malgun Gothic', sans-serif; line-height: 1.6; color: #222;">
        <p>안녕하세요.</p>

        <p>{escape(today)} 기준 뉴스 및 보도자료 수집 결과를 공유드립니다.</p>

        <h3>1. 수집 요약</h3>
        <ul>
          <li>수집 기간: {escape(start_date)} ~ {escape(end_date)}</li>
          <li>검색어: {escape(", ".join(keywords) if keywords else "-")}</li>
          <li>총 수집 건수: {total_count}건</li>
          <li>수집 구분: 뉴스, 보도자료</li>
        </ul>

        <h3>2. 뉴스 수집 결과</h3>
        {_render_news_summary_table(news_summary, keywords, news_total)}

        <h3>3. 보도자료 수집 결과</h3>
        {_render_press_release_summary_table(press_summary, press_total)}

        <h3>4. 참고사항</h3>
        <ul>
          <li>일부 매체는 검색어별 수집 건수가 0건으로 확인될 수 있습니다.</li>
          <li>동일 URL은 중복 제거되어 한 번만 발송됩니다.</li>
        </ul>

        <p>감사합니다.</p>

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


def _build_news_summary(
    job_results: List[JobResult],
    keywords: List[str],
) -> List[Dict]:
    summary_by_source: Dict[str, Dict] = {}

    for job_result in job_results:
        if str(job_result.get("crawler_type", "")) != "naver_news":
            continue

        source = str(job_result.get("source", "")).strip()
        keyword = str(job_result.get("keyword", "")).strip()
        url = str(job_result.get("url", "")).strip()
        count = len(job_result.get("articles", []))

        if not source:
            source = str(job_result.get("job_name", "")).strip()

        if source not in summary_by_source:
            summary_by_source[source] = {
                "source": source,
                "counts": {kw: 0 for kw in keywords},
                "urls": {kw: "" for kw in keywords},
                "total": 0,
            }

        if keyword:
            summary_by_source[source]["counts"][keyword] = count
            summary_by_source[source]["urls"][keyword] = url

        summary_by_source[source]["total"] += count

    return list(summary_by_source.values())


def _build_press_release_summary(job_results: List[JobResult]) -> List[Dict]:
    summary: List[Dict] = []

    for job_result in job_results:
        crawler_type = str(job_result.get("crawler_type", ""))

        if crawler_type not in ("fire_agency", "mpm"):
            continue

        source = str(job_result.get("source", "")).strip()
        url = str(job_result.get("url", "")).strip()
        count = len(job_result.get("articles", []))

        if not source:
            source = str(job_result.get("job_name", "")).strip()

        summary.append(
            {
                "source": source,
                "url": url,
                "count": count,
            }
        )

    return summary


def _render_news_summary_table(
    news_summary: List[Dict],
    keywords: List[str],
    news_total: int,
) -> str:
    if not news_summary:
        return "<p>뉴스 수집 결과가 없습니다.</p>"

    header_cells = "".join(
        f'<th style="{_th_style()}">{escape(keyword)}</th>'
        for keyword in keywords
    )

    body_rows = ""

    for row in news_summary:
        source = escape(row["source"])
        keyword_cells = ""

        for keyword in keywords:
            count = row["counts"].get(keyword, 0)
            url = row["urls"].get(keyword, "")
            label = f"{count}건"

            keyword_cells += (
                f'<td style="{_td_style(text_align="right")}">'
                f'{_link_or_text(label, url)}'
                f"</td>"
            )

        body_rows += f"""
        <tr>
          <td style="{_td_style()}">{source}</td>
          {keyword_cells}
          <td style="{_td_style(text_align="right")}"><strong>{row["total"]}건</strong></td>
        </tr>
        """

    total_keyword_cells = ""

    for keyword in keywords:
        keyword_total = sum(row["counts"].get(keyword, 0) for row in news_summary)
        total_keyword_cells += (
            f'<td style="{_td_style(text_align="right")}">'
            f"<strong>{keyword_total}건</strong>"
            f"</td>"
        )

    body_rows += f"""
    <tr>
      <td style="{_td_style()}"><strong>뉴스 합계</strong></td>
      {total_keyword_cells}
      <td style="{_td_style(text_align="right")}"><strong>{news_total}건</strong></td>
    </tr>
    """

    return f"""
    <table style="{_table_style()}">
      <thead>
        <tr>
          <th style="{_th_style()}">매체</th>
          {header_cells}
          <th style="{_th_style()}">합계</th>
        </tr>
      </thead>
      <tbody>
        {body_rows}
      </tbody>
    </table>
    """


def _render_press_release_summary_table(
    press_summary: List[Dict],
    press_total: int,
) -> str:
    if not press_summary:
        return "<p>보도자료 수집 결과가 없습니다.</p>"

    body_rows = ""

    for row in press_summary:
        source = escape(row["source"])
        count = row["count"]
        url = row["url"]

        body_rows += f"""
        <tr>
          <td style="{_td_style()}">{_link_or_text(source, url)}</td>
          <td style="{_td_style(text_align="right")}">{count}건</td>
        </tr>
        """

    body_rows += f"""
    <tr>
      <td style="{_td_style()}"><strong>보도자료 합계</strong></td>
      <td style="{_td_style(text_align="right")}"><strong>{press_total}건</strong></td>
    </tr>
    """

    return f"""
    <table style="{_table_style()}">
      <thead>
        <tr>
          <th style="{_th_style()}">기관</th>
          <th style="{_th_style()}">수집 건수</th>
        </tr>
      </thead>
      <tbody>
        {body_rows}
      </tbody>
    </table>
    """


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


def _link_or_text(label: str, url: str) -> str:
    safe_label = escape(label)
    safe_url = escape(url)

    if not safe_url:
        return safe_label

    return f'<a href="{safe_url}" target="_blank">{safe_label}</a>'


def _table_style() -> str:
    return (
        "border-collapse: collapse; "
        "width: 100%; "
        "margin: 8px 0 18px 0; "
        "font-size: 14px;"
    )


def _th_style() -> str:
    return (
        "border: 1px solid #ddd; "
        "padding: 8px; "
        "background-color: #f3f3f3; "
        "text-align: left;"
    )


def _td_style(text_align: str = "left") -> str:
    return (
        "border: 1px solid #ddd; "
        "padding: 8px; "
        f"text-align: {text_align};"
    )