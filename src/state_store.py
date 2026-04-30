import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from zoneinfo import ZoneInfo


DEFAULT_STATE_PATH = "data/sent_articles.json"


def load_state(state_path: str = DEFAULT_STATE_PATH) -> Dict[str, Any]:
    """
    발송 이력 파일을 읽는다.
    파일이 없으면 기본 구조를 반환한다.
    """

    path = Path(state_path)

    if not path.exists():
        return {"sent_articles": []}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if "sent_articles" not in data:
        data["sent_articles"] = []

    return data


def save_state(
    state: Dict[str, Any],
    state_path: str = DEFAULT_STATE_PATH,
) -> None:
    """
    발송 이력 파일을 저장한다.
    """

    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def prune_old_sent_articles(
    state: Dict[str, Any],
    retention_days: int,
    timezone: str = "Asia/Seoul",
) -> Dict[str, Any]:
    """
    retention_days보다 오래된 발송 이력을 삭제한다.
    """

    now = datetime.now(ZoneInfo(timezone))
    cutoff = now - timedelta(days=retention_days)

    kept_articles = []

    for article in state.get("sent_articles", []):
        sent_at_text = article.get("sent_at")

        if not sent_at_text:
            continue

        try:
            sent_at = datetime.fromisoformat(sent_at_text)
        except ValueError:
            continue

        if sent_at >= cutoff:
            kept_articles.append(article)

    state["sent_articles"] = kept_articles
    return state


def get_sent_links(state: Dict[str, Any]) -> set[str]:
    """
    이미 발송한 URL 목록을 set으로 반환한다.
    """

    return {
        article["link"]
        for article in state.get("sent_articles", [])
        if article.get("link")
    }


def append_sent_articles(
    state: Dict[str, Any],
    articles: List[Dict[str, str]],
    timezone: str = "Asia/Seoul",
) -> Dict[str, Any]:
    """
    메일 발송 성공 후, 새로 보낸 기사/보도자료 URL을 발송 이력에 추가한다.
    """

    if "sent_articles" not in state:
        state["sent_articles"] = []

    now = datetime.now(ZoneInfo(timezone)).isoformat()
    existing_links = get_sent_links(state)

    for article in articles:
        link = article.get("link", "").strip()

        if not link:
            continue

        if link in existing_links:
            continue

        state["sent_articles"].append(
            {
                "link": link,
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "source_type": article.get("source_type", ""),
                "keyword": article.get("keyword", ""),
                "item_type": article.get("item_type", ""),
                "published_at": article.get("published_at", ""),
                "sent_at": now,
            }
        )

        existing_links.add(link)

    return state