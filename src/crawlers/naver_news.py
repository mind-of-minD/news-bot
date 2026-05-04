from typing import Dict, List

from playwright.sync_api import Page, sync_playwright


Article = Dict[str, str]


def crawl(job: Dict, crawler_config: Dict) -> List[Article]:
    """
    네이버 뉴스 검색 결과를 크롤링한다.

    반환 형식:
    [
        {
            "title": "...",
            "link": "...",
            "source": "뉴시스",
            "source_type": "naver_news",
            "keyword": "공무원",
            "item_type": "main" | "related"
        }
    ]
    """

    url = job["url"]
    limit = int(job.get("limit", 30))
    source = job.get("source", "")
    keyword = job.get("keyword", "")

    max_scroll_attempts = int(crawler_config.get("max_scroll_attempts", 30))
    scroll_wait_ms = int(crawler_config.get("scroll_wait_ms", 2000))
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

            articles: List[Article] = []
            seen_links = set()
            scroll_attempts = 0
            stagnant_count = 0

            while len(articles) < limit and scroll_attempts <= max_scroll_attempts:
                previous_count = len(articles)

                extracted = _extract_articles_from_page(page, source, keyword)

                for article in extracted:
                    link = article["link"]

                    if link in seen_links:
                        continue

                    seen_links.add(link)
                    articles.append(article)

                    if len(articles) >= limit:
                        break

                if len(articles) >= limit:
                    break

                prev_cards = page.locator("div.fds-news-item-list-tab").count()

                page.mouse.wheel(0, 3000)

                try:
                    page.wait_for_function(
                        """
                        (prev) => {
                            return document.querySelectorAll('div.fds-news-item-list-tab').length > prev;
                        }
                        """,
                        prev_cards,
                        timeout=3000,
                    )
                except Exception:
                    pass

                page.wait_for_timeout(scroll_wait_ms)

                if len(articles) == previous_count:
                    stagnant_count += 1
                else:
                    stagnant_count = 0

                if stagnant_count >= 3:
                    break

                scroll_attempts += 1

            return articles[:limit]

        finally:
            browser.close()


def _extract_articles_from_page(
    page: Page,
    source: str,
    keyword: str,
) -> List[Article]:
    return page.evaluate(
        """
        ({ source, keyword }) => {
            const results = [];
            const seen = new Set();

            function cleanText(text) {
                return (text || '').replace(/\\s+/g, ' ').trim();
            }

            function isValidArticleUrl(href) {
                if (!href) return false;
                if (href.startsWith('javascript:')) return false;

                try {
                    const url = new URL(href);
                    const host = url.hostname;

                    const blockedHosts = [
                        'search.naver.com',
                        'www.naver.com',
                        'mail.naver.com',
                        'keep.naver.com',
                        'help.naver.com',
                        'media.naver.com',
                        'mkt.naver.com'
                    ];

                    if (blockedHosts.some((blocked) => host.includes(blocked))) {
                        return false;
                    }

                    if (host.includes('pstatic.net')) return false;

                    return true;
                } catch (e) {
                    return false;
                }
            }

            function getMainPress(articleBlock) {
                const profile = articleBlock.querySelector(
                    ':scope > .sds-comps-profile, :scope > div[data-sds-comp="Profile"]'
                );

                if (!profile) return '';

                const pressEl = profile.querySelector(
                    '.sds-comps-profile-info-title-text'
                );

                return pressEl ? cleanText(pressEl.innerText) : '';
            }

            function getRelatedPress(relatedBlock) {
                const pressEl = relatedBlock.querySelector(
                    '.sds-comps-profile-info-title-text'
                );

                return pressEl ? cleanText(pressEl.innerText) : '';
            }

            const candidateBlocks = Array.from(
                document.querySelectorAll(
                    'div.sds-comps-vertical-layout.sds-comps-full-layout'
                )
            );

            const articleBlocks = candidateBlocks.filter((block) => {
                const profile = block.querySelector(
                    ':scope > .sds-comps-profile, :scope > div[data-sds-comp="Profile"]'
                );

                const mainTitle = block.querySelector(
                    ':scope a[data-heatmap-target=".tit"] .sds-comps-text-type-headline1'
                );

                return profile && mainTitle;
            });

            for (const articleBlock of articleBlocks) {
                const mainPress = getMainPress(articleBlock) || source;

                const mainTitleLink = articleBlock.querySelector(
                    'a[data-heatmap-target=".tit"]:has(.sds-comps-text-type-headline1)'
                );

                if (mainTitleLink) {
                    const link = mainTitleLink.href;
                    const title = cleanText(mainTitleLink.innerText);

                    if (
                        isValidArticleUrl(link) &&
                        title.length >= 8 &&
                        !seen.has(link)
                    ) {
                        results.push({
                            title,
                            link,
                            source: mainPress,
                            source_type: 'naver_news',
                            keyword,
                            item_type: 'main'
                        });

                        seen.add(link);
                    }
                }

                const relatedBlocks = Array.from(
                    articleBlock.querySelectorAll('.OUm_HkSP9Spsiw2TDZjZ')
                );

                for (const relatedBlock of relatedBlocks) {
                    const relatedTitleLink = relatedBlock.querySelector(
                        'a[data-heatmap-target=".tit"][href]'
                    );

                    if (!relatedTitleLink) continue;

                    const link = relatedTitleLink.href;
                    const title = cleanText(relatedTitleLink.innerText);

                    if (!isValidArticleUrl(link)) continue;
                    if (!title || title.length < 8) continue;
                    if (seen.has(link)) continue;

                    const relatedPress = getRelatedPress(relatedBlock) || source;

                    results.push({
                        title,
                        link,
                        source: relatedPress,
                        source_type: 'naver_news',
                        keyword,
                        item_type: 'related'
                    });

                    seen.add(link);
                }
            }

            return results;
        }
        """,
        {"source": source, "keyword": keyword},
    )

def _goto_with_retry(page: Page, url: str, retries: int = 3) -> None:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(3000)
            return
        except Exception as e:
            last_error = e
            print(f"[WARN] 네이버 뉴스 접속 실패 {attempt}/{retries}: {e}")
            page.wait_for_timeout(3000)

    raise last_error