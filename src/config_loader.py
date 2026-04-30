from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import yaml


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {config_path}")

    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not config:
        raise ValueError("config.yaml이 비어 있습니다.")

    start_date, end_date = build_date_range(config)

    config["runtime"] = {
        "start_date": start_date,
        "end_date": end_date,
    }

    config["jobs"] = build_jobs(config, start_date, end_date)

    return config


def build_date_range(config: Dict[str, Any]) -> tuple[str, str]:
    schedule_config = config.get("schedule", {})
    date_config = config.get("date", {})

    timezone = schedule_config.get("timezone", "Asia/Seoul")
    date_format = date_config.get("format", "%Y.%m.%d")

    start_offset_days = int(date_config.get("start_offset_days", -1))
    end_offset_days = int(date_config.get("end_offset_days", 0))

    today = datetime.now(ZoneInfo(timezone)).date()

    start_date = today + timedelta(days=start_offset_days)
    end_date = today + timedelta(days=end_offset_days)

    return start_date.strftime(date_format), end_date.strftime(date_format)


def build_jobs(
    config: Dict[str, Any],
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:
    jobs: List[Dict[str, Any]] = []

    jobs.extend(build_naver_news_jobs(config, start_date, end_date))
    jobs.extend(build_press_release_jobs(config))

    return jobs


def build_naver_news_jobs(
    config: Dict[str, Any],
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:
    naver_config = config.get("naver_news", {})

    keywords = naver_config.get("keywords", [])
    limit = int(naver_config.get("limit", 30))
    common_params = naver_config.get("common_params", {})
    sources = naver_config.get("sources", [])

    if not keywords:
        return []

    jobs: List[Dict[str, Any]] = []

    for source in sources:
        source_name = source["name"]
        press = source.get("press", source_name)
        office_section_code = str(source["office_section_code"])
        news_office_checked = str(source["news_office_checked"])

        for keyword in keywords:
            params = {
                **common_params,
                "query": keyword,
                "ds": start_date,
                "de": end_date,
                "office_section_code": office_section_code,
                "news_office_checked": news_office_checked,
            }

            url = "https://search.naver.com/search.naver?" + urlencode(params)

            jobs.append(
                {
                    "name": f"{source_name}_{keyword}",
                    "crawler_type": "naver_news",
                    "source": source_name,
                    "press": press,
                    "keyword": keyword,
                    "url": url,
                    "limit": limit,
                    "start_date": start_date,
                    "end_date": end_date,
                }
            )

    return jobs


def build_press_release_jobs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    press_release_config = config.get("press_release", {})
    sources = press_release_config.get("sources", [])

    jobs: List[Dict[str, Any]] = []

    for source in sources:
        enabled = bool(source.get("enabled", False))

        if not enabled:
            continue

        jobs.append(
            {
                "name": source["name"],
                "crawler_type": source["crawler_type"],
                "source": source["name"],
                "press": source["name"],
                "keyword": "",
                "url": source["url"],
                "limit": int(source.get("limit", 30)),
            }
        )

    return jobs