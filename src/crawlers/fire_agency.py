from typing import Dict, List
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


Article = Dict[str, str]


def crawl(job: Dict, crawler_config: Dict) -> List[Article]:
    """
    소방청 보도자료 목록 페이지를 크롤링한다.

    반환 형식:
    [
        {
            "title": "...",
            "link": "...",
            "source": "소방청",
            "source_type": "fire_agency",
            "keyword": "",
            "item_type": "press_release",
            "published_at": "2026-04-30"
        }
    ]
    """

    url = job["url"]
    limit = int(job.get("limit", 30))
    source = job.get("source", "소방청")

    headless = bool(crawler_config.get("headless", True))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)

        try:
            page = browser.new_page(
                viewport={"width": 1280, "height": 1600},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )

            _goto_with_retry(page, url)

            articles = page.evaluate(
                """
                ({ source, limit }) => {
                    const results = [];
                    const seen = new Set();

                    function cleanText(text) {
                        return (text || '').replace(/\\s+/g, ' ').trim();
                    }

                    const rows = Array.from(
                        document.querySelectorAll('table.bbsList tbody tr')
                    );

                    for (const row of rows) {
                        const titleLink = row.querySelector('td.title a[href]');
                        const dateCell = row.querySelector('td.created');

                        if (!titleLink) continue;

                        const title = cleanText(titleLink.innerText);
                        const href = titleLink.getAttribute('href');
                        const publishedAt = dateCell ? cleanText(dateCell.innerText) : '';

                        if (!title || !href) continue;

                        const link = new URL(href, window.location.href).href;

                        if (seen.has(link)) continue;

                        results.push({
                            title,
                            link,
                            source,
                            source_type: 'mpm',
                            keyword: '',
                            item_type: 'press_release',
                            published_at: publishedAt
                        });

                        seen.add(link);

                        if (results.length >= limit) {
                            break;
                        }
                    }

                    return results;
                }
                """,
                {"source": source, "limit": limit},
            )

            return articles

        finally:
            browser.close()
    
def _goto_with_retry(page, url: str, retries: int = 3) -> None:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(3000)
            return
        except Exception as e:
            last_error = e
            print(f"[WARN] 소방청 접속 실패 {attempt}/{retries}: {e}")
            page.wait_for_timeout(3000)

    raise last_error