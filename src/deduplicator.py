from typing import Dict, List, Set, Tuple


Article = Dict[str, str]


def deduplicate_articles(
    articles: List[Article],
    sent_links: Set[str],
) -> Tuple[List[Article], List[Article]]:
    """
    크롤링된 기사 목록에서 중복 URL을 제거한다.

    제거 기준:
    1. 이미 발송된 URL(sent_links)
    2. 이번 실행 안에서 중복으로 나온 URL

    반환:
    - new_articles: 새로 발송할 기사
    - skipped_articles: 중복으로 제외된 기사
    """

    new_articles: List[Article] = []
    skipped_articles: List[Article] = []

    seen_in_current_run: Set[str] = set()

    for article in articles:
        link = article.get("link", "").strip()

        if not link:
            skipped_articles.append(article)
            continue

        if link in sent_links:
            skipped_articles.append(article)
            continue

        if link in seen_in_current_run:
            skipped_articles.append(article)
            continue

        new_articles.append(article)
        seen_in_current_run.add(link)

    return new_articles, skipped_articles


def flatten_job_results(job_results: List[Dict]) -> List[Article]:
    """
    job별 결과를 하나의 기사 목록으로 합친다.
    """

    all_articles: List[Article] = []

    for job_result in job_results:
        articles = job_result.get("articles", [])
        all_articles.extend(articles)

    return all_articles