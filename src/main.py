import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from src.config_loader import load_config
from src.crawler_runner import run_all_crawlers
from src.deduplicator import deduplicate_articles
from src.mailer import get_recipients, send_email
from src.renderer import build_email_html, build_email_subject
from src.state_store import (
    append_sent_articles,
    get_sent_links,
    load_state,
    prune_old_sent_articles,
    save_state,
)


def str_to_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default

    return value.lower() in ("true", "1", "yes", "y")


def main() -> None:
    load_dotenv()

    config = load_config()

    schedule_config = config.get("schedule", {})
    timezone = schedule_config.get("timezone", "Asia/Seoul")

    dedup_config = config.get("deduplication", {})
    retention_days = int(dedup_config.get("retention_days", 7))

    crawler_config = config.get("crawler", {})
    crawler_config["headless"] = str_to_bool(
        os.getenv("CRAWLER_HEADLESS"),
        default=True,
    )

    print("[START] 뉴스/보도자료 수집 시작")
    print(f"[DATE] {config['runtime']['start_date']} ~ {config['runtime']['end_date']}")

    state = load_state()
    state = prune_old_sent_articles(
        state=state,
        retention_days=retention_days,
        timezone=timezone,
    )

    sent_links = get_sent_links(state)

    print(f"[STATE] 최근 발송 URL {len(sent_links)}개 로딩")
    print(f"[STATE] 보관 기간: {retention_days}일")

    raw_job_results = run_all_crawlers(
        jobs=config.get("jobs", []),
        crawler_config=crawler_config,
    )

    filtered_job_results: List[Dict[str, Any]] = []
    all_new_articles: List[Dict[str, str]] = []

    for job_result in raw_job_results:
        articles = job_result.get("articles", [])

        new_articles, skipped_articles = deduplicate_articles(
            articles=articles,
            sent_links=sent_links,
        )

        for article in new_articles:
            sent_links.add(article["link"])

        filtered_result = {
            **job_result,
            "articles": new_articles,
            "collected_count": len(articles),
            "new_count": len(new_articles),
            "skipped_duplicate_count": len(skipped_articles),
        }

        filtered_job_results.append(filtered_result)
        all_new_articles.extend(new_articles)

        print(
            f"[DEDUP] {job_result['job_name']} "
            f"수집 {len(articles)}개 / 신규 {len(new_articles)}개 / 중복 {len(skipped_articles)}개"
        )

    if not all_new_articles:
        print("[MAIL] 새로 발송할 항목이 없습니다.")

        # 7일 지난 기록 삭제 결과는 저장해둔다.
        save_state(state)
        print("[DONE] 종료")
        return

    subject = build_email_subject(config)
    html_body = build_email_html(config, filtered_job_results)
    recipients = get_recipients()

    print(f"[MAIL] 수신자 {len(recipients)}명")
    print(f"[MAIL] 제목: {subject}")

    send_email(
        subject=subject,
        html_body=html_body,
        recipients=recipients,
    )

    print("[MAIL] 발송 완료")

    state = append_sent_articles(
        state=state,
        articles=all_new_articles,
        timezone=timezone,
    )

    state = prune_old_sent_articles(
        state=state,
        retention_days=retention_days,
        timezone=timezone,
    )

    save_state(state)

    print(f"[STATE] 발송 이력 저장 완료: {len(state.get('sent_articles', []))}개")
    print("[DONE] 전체 작업 완료")


if __name__ == "__main__":
    main()