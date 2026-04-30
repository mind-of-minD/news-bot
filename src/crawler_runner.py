from typing import Any, Dict, List

from typing import Any, Dict, List

from src.crawlers import fire_agency, mpm, naver_news

Article = Dict[str, str]
Job = Dict[str, Any]


CRAWLER_MAP = {
    "naver_news": naver_news.crawl,
    "fire_agency": fire_agency.crawl,
    "mpm": mpm.crawl,
}


def run_crawler(job: Job, crawler_config: Dict[str, Any]) -> List[Article]:
    crawler_type = job.get("crawler_type")

    if not crawler_type:
        raise ValueError(f"crawler_type이 없습니다: {job}")

    crawler = CRAWLER_MAP.get(crawler_type)

    if not crawler:
        available_types = ", ".join(CRAWLER_MAP.keys())
        raise ValueError(
            f"지원하지 않는 crawler_type입니다: {crawler_type}. "
            f"사용 가능: {available_types}"
        )

    return crawler(job, crawler_config)


def run_all_crawlers(
    jobs: List[Job],
    crawler_config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    job_results: List[Dict[str, Any]] = []

    for job in jobs:
        job_name = job["name"]
        crawler_type = job["crawler_type"]

        print("=" * 60)
        print(f"[JOB] {job_name}")
        print(f"[CRAWLER] {crawler_type}")
        print("=" * 60)

        articles = run_crawler(job, crawler_config)

        print(f"{job_name}: {len(articles)}개 수집\n")

        job_results.append(
            {
                "job_name": job_name,
                "crawler_type": crawler_type,
                "source": job.get("source", ""),
                "keyword": job.get("keyword", ""),
                "url": job.get("url", ""),
                "articles": articles,
            }
        )

    return job_results