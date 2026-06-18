#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
赛果抓取脚本

功能说明：
1. 每天下午 14:00 后抓取当天世界杯比赛赛果
2. 优先从 API 获取，失败后可尝试网页抓取
3. 如果在线抓取失败，则自动回退到用户提供的 CSV 文件
4. 输出 JSON 和给 Codex 使用的 TXT 摘要
5. 所有日志统一写入根目录 log.txt，并额外写入 logs 子目录
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


DEFAULT_ROOT = Path(r"D:\WorldCupPredict")
DEFAULT_TIMEOUT = 20
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:139.0) Gecko/20100101 Firefox/139.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; SM-S9180) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
]


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="抓取今日世界杯赛果并生成归档文件")
    parser.add_argument("--root", default=os.environ.get("WORLD_CUP_ROOT", str(DEFAULT_ROOT)), help="项目根目录")
    parser.add_argument("--date", default=datetime.now().strftime("%Y%m%d"), help="目标日期，格式 yyyyMMdd")
    parser.add_argument("--api-url", default=os.environ.get("RESULTS_API_URL", ""), help="赛果 API 地址")
    parser.add_argument("--page-url", default=os.environ.get("RESULTS_PAGE_URL", ""), help="赛果网页地址")
    parser.add_argument("--csv", default=os.environ.get("RESULTS_CSV_PATH", ""), help="备用 CSV 文件路径")
    parser.add_argument("--overwrite", action="store_true", help="是否覆盖已存在文件")
    parser.add_argument("--min-delay", type=float, default=1.2, help="请求最小延时，秒")
    parser.add_argument("--max-delay", type=float, default=3.0, help="请求最大延时，秒")
    return parser.parse_args()


def setup_logging(root: Path, date_str: str) -> logging.Logger:
    """初始化日志。"""
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = root / "log.txt"
    daily_log_file = logs_dir / f"fetch_results_{date_str}.log"

    logger = logging.getLogger("fetch_results")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    daily_handler = logging.FileHandler(daily_log_file, encoding="utf-8")
    daily_handler.setFormatter(formatter)
    logger.addHandler(daily_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def ensure_structure(root: Path) -> None:
    """创建项目目录结构。"""
    for name in ("scripts", "data", "output", "logs"):
        (root / name).mkdir(parents=True, exist_ok=True)


def sleep_random(min_delay: float, max_delay: float) -> None:
    """随机延时，降低被反爬拦截的概率。"""
    if max_delay < min_delay:
        max_delay = min_delay
    time.sleep(random.uniform(min_delay, max_delay))


def request_with_retry(
    url: str,
    logger: logging.Logger,
    min_delay: float,
    max_delay: float,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Any] = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 3,
) -> requests.Response:
    """带有 UA 轮换和重试能力的请求函数。"""
    last_error: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        merged_headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
        }
        if headers:
            merged_headers.update(headers)

        sleep_random(min_delay, max_delay)
        try:
            logger.info("开始请求：%s（第 %s 次）", url, attempt)
            response = requests.request(
                method=method,
                url=url,
                headers=merged_headers,
                params=params,
                data=data,
                timeout=timeout,
            )
            response.raise_for_status()
            return response
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.warning("请求失败：%s（第 %s 次）", exc, attempt)

    raise RuntimeError(f"请求失败，重试 {retries} 次后仍未成功：{last_error}")


def normalize_date_text(value: str) -> str:
    """将多种日期格式统一为 yyyyMMdd。"""
    if not value:
        return ""

    value = str(value).strip()
    candidates = [
        "%Y%m%d",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    for pattern in candidates:
        try:
            return datetime.strptime(value, pattern).strftime("%Y%m%d")
        except ValueError:
            continue

    digits = re.sub(r"\D", "", value)
    if len(digits) >= 8:
        return digits[:8]
    return value


def safe_int(value: Any, default: int = 0) -> int:
    """安全转换整数。"""
    if value is None or value == "":
        return default
    try:
        return int(float(str(value).strip()))
    except Exception:  # noqa: BLE001
        return default


def safe_str(value: Any, default: str = "") -> str:
    """安全转换字符串。"""
    if value is None:
        return default
    return str(value).strip()


def detect_total_goals(home_score: int, away_score: int) -> int:
    """计算总进球数。"""
    return home_score + away_score


def normalize_odds_total_goals(item: Dict[str, Any]) -> Dict[str, float]:
    """归一化总进球赔率字段。"""
    result: Dict[str, float] = {}
    direct_keys = ["0", "1", "2", "3", "4+"]
    for key in direct_keys:
        value = item.get(key)
        if value not in (None, ""):
            try:
                result[key] = float(value)
            except Exception:  # noqa: BLE001
                continue

    alias_map = {
        "0": ["odds_0", "goals_0", "ttg_0"],
        "1": ["odds_1", "goals_1", "ttg_1"],
        "2": ["odds_2", "goals_2", "ttg_2"],
        "3": ["odds_3", "goals_3", "ttg_3"],
        "4+": ["odds_4_plus", "goals_4_plus", "ttg_4_plus", "odds_4+"],
    }
    for target_key, aliases in alias_map.items():
        if target_key in result:
            continue
        for alias in aliases:
            value = item.get(alias)
            if value in (None, ""):
                continue
            try:
                result[target_key] = float(value)
                break
            except Exception:  # noqa: BLE001
                continue
    return result


def normalize_match(item: Dict[str, Any], fallback_index: int, target_date: str) -> Dict[str, Any]:
    """将不同来源的赛果字段统一成目标结构。"""
    match_id = (
        safe_str(item.get("match_id"))
        or safe_str(item.get("id"))
        or safe_str(item.get("matchId"))
        or safe_str(item.get("event_id"))
        or f"{fallback_index:03d}"
    )
    home_team = (
        safe_str(item.get("home_team"))
        or safe_str(item.get("homeTeam"))
        or safe_str(item.get("strHomeTeam"))
        or safe_str(item.get("home"))
    )
    away_team = (
        safe_str(item.get("away_team"))
        or safe_str(item.get("awayTeam"))
        or safe_str(item.get("strAwayTeam"))
        or safe_str(item.get("away"))
    )
    home_score = safe_int(
        item.get("home_score", item.get("intHomeScore", item.get("homeScore", item.get("score1"))))
    )
    away_score = safe_int(
        item.get("away_score", item.get("intAwayScore", item.get("awayScore", item.get("score2"))))
    )
    half_time_score = (
        safe_str(item.get("half_time_score"))
        or safe_str(item.get("halfTimeScore"))
        or safe_str(item.get("strHTScore"))
        or safe_str(item.get("ht_score"))
        or "-"
    )
    possession = safe_str(item.get("possession"), "-")
    yellow_cards = safe_str(item.get("yellow_cards", item.get("yellowCards")), "-")
    red_cards = safe_str(item.get("red_cards", item.get("redCards")), "-")
    odds_total_goals = normalize_odds_total_goals(item)

    if not home_team or not away_team:
        raise ValueError("比赛数据缺少主客队字段，无法归一化")

    return {
        "match_id": match_id,
        "home_team": home_team,
        "away_team": away_team,
        "home_score": home_score,
        "away_score": away_score,
        "total_goals": detect_total_goals(home_score, away_score),
        "half_time_score": half_time_score,
        "possession": possession,
        "yellow_cards": yellow_cards,
        "red_cards": red_cards,
        "odds_total_goals": odds_total_goals,
        "match_date": target_date,
    }


def iter_possible_match_items(payload: Any) -> Iterable[Dict[str, Any]]:
    """递归扫描任意 JSON，尽量找出比赛对象。"""
    if isinstance(payload, list):
        for item in payload:
            yield from iter_possible_match_items(item)
        return

    if not isinstance(payload, dict):
        return

    keys = set(payload.keys())
    has_team_field = {"home_team", "away_team"} <= keys or {"homeTeam", "awayTeam"} <= keys or {"strHomeTeam", "strAwayTeam"} <= keys
    has_score_field = bool(keys & {"home_score", "away_score", "homeScore", "awayScore", "intHomeScore", "intAwayScore"})
    if has_team_field and has_score_field:
        yield payload

    for value in payload.values():
        yield from iter_possible_match_items(value)


def fetch_from_api(
    api_url: str,
    target_date: str,
    logger: logging.Logger,
    min_delay: float,
    max_delay: float,
) -> List[Dict[str, Any]]:
    """从 API 抓取赛果。"""
    if not api_url:
        return []

    response = request_with_retry(
        url=api_url,
        logger=logger,
        min_delay=min_delay,
        max_delay=max_delay,
        headers={"Referer": api_url},
    )
    payload = response.json()

    matches: List[Dict[str, Any]] = []
    for index, item in enumerate(iter_possible_match_items(payload), start=1):
        item_date = normalize_date_text(
            safe_str(item.get("match_date"))
            or safe_str(item.get("date"))
            or safe_str(item.get("event_date"))
            or safe_str(item.get("strTimestamp"))
        )
        if item_date and item_date != target_date:
            continue
        matches.append(normalize_match(item, index, target_date))

    logger.info("API 抓取完成，共获取 %s 场比赛", len(matches))
    return matches


def extract_json_from_html(html_text: str) -> List[Any]:
    """从网页源码中提取可能的 JSON 片段。"""
    extracted: List[Any] = []

    patterns = [
        r"<script[^>]*id=[\"']__NEXT_DATA__[\"'][^>]*>(.*?)</script>",
        r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        r"window\.__INITIAL_STATE__\s*=\s*(\{.*?\})\s*;",
        r"window\.__DATA__\s*=\s*(\{.*?\})\s*;",
    ]

    for pattern in patterns:
        for matched in re.findall(pattern, html_text, flags=re.IGNORECASE | re.DOTALL):
            content = matched.strip()
            if not content:
                continue
            try:
                extracted.append(json.loads(content))
            except Exception:  # noqa: BLE001
                continue

    return extracted


def fetch_from_page(
    page_url: str,
    target_date: str,
    logger: logging.Logger,
    min_delay: float,
    max_delay: float,
) -> List[Dict[str, Any]]:
    """从网页抓取赛果，优先提取页面内嵌 JSON。"""
    if not page_url:
        return []

    response = request_with_retry(
        url=page_url,
        logger=logger,
        min_delay=min_delay,
        max_delay=max_delay,
        headers={"Referer": page_url},
    )
    html_text = response.text

    matches: List[Dict[str, Any]] = []
    for payload in extract_json_from_html(html_text):
        for index, item in enumerate(iter_possible_match_items(payload), start=1):
            item_date = normalize_date_text(
                safe_str(item.get("match_date"))
                or safe_str(item.get("date"))
                or safe_str(item.get("event_date"))
                or safe_str(item.get("strTimestamp"))
            )
            if item_date and item_date != target_date:
                continue
            try:
                matches.append(normalize_match(item, index, target_date))
            except Exception as exc:  # noqa: BLE001
                logger.warning("网页数据归一化失败：%s", exc)

    logger.info("网页抓取完成，共获取 %s 场比赛", len(matches))
    return matches


def load_from_csv(csv_path: Path, target_date: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """从用户提供的 CSV 读取赛果。"""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 文件不存在：{csv_path}")

    matches: List[Dict[str, Any]] = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for index, row in enumerate(reader, start=1):
            row_date = normalize_date_text(
                safe_str(row.get("date"))
                or safe_str(row.get("match_date"))
                or safe_str(row.get("比赛日期"))
            )
            if row_date and row_date != target_date:
                continue
            matches.append(normalize_match(row, index, target_date))

    logger.info("CSV 读取完成，共获取 %s 场比赛", len(matches))
    return matches


def deduplicate_matches(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 match_id 去重。"""
    unique_map: Dict[str, Dict[str, Any]] = {}
    for item in matches:
        unique_map[item["match_id"]] = item
    return sorted(unique_map.values(), key=lambda x: x["match_id"])


def build_summary_lines(matches: List[Dict[str, Any]]) -> List[str]:
    """生成给 Codex 直接读取的摘要文本。"""
    lines = []
    for item in matches:
        line = (
            f'{item["match_id"]}|{item["home_team"]}|{item["home_score"]}|'
            f'{item["away_team"]}|{item["away_score"]}|总进球{item["total_goals"]}|半场{item["half_time_score"]}'
        )
        lines.append(line)
    return lines


def save_outputs(root: Path, target_date: str, matches: List[Dict[str, Any]], logger: logging.Logger) -> None:
    """保存 JSON 和 TXT 摘要。"""
    day_dir = root / target_date
    day_dir.mkdir(parents=True, exist_ok=True)

    json_path = day_dir / f"match_results_{target_date}.json"
    summary_path = day_dir / f"summary_{target_date}.txt"

    with json_path.open("w", encoding="utf-8") as file:
        json.dump(matches, file, ensure_ascii=False, indent=2)

    summary_lines = build_summary_lines(matches)
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    # 额外同步一份到 data 目录，便于历史汇总或其他脚本读取。
    data_json_path = root / "data" / f"match_results_{target_date}.json"
    data_summary_path = root / "data" / f"summary_{target_date}.txt"
    with data_json_path.open("w", encoding="utf-8") as file:
        json.dump(matches, file, ensure_ascii=False, indent=2)
    data_summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    logger.info("JSON 已保存：%s", json_path)
    logger.info("摘要已保存：%s", summary_path)


def should_skip_output(root: Path, target_date: str, overwrite: bool) -> bool:
    """判断是否跳过写入。"""
    if overwrite:
        return False
    json_path = root / target_date / f"match_results_{target_date}.json"
    return json_path.exists()


def main() -> int:
    """程序入口。"""
    args = parse_args()
    root = Path(args.root).expanduser()
    ensure_structure(root)
    logger = setup_logging(root, args.date)

    try:
        logger.info("赛果抓取脚本开始执行，目标日期：%s", args.date)

        if should_skip_output(root, args.date, args.overwrite):
            logger.info("目标文件已存在，未指定 --overwrite，跳过本次执行")
            return 0

        all_matches: List[Dict[str, Any]] = []

        if args.api_url:
            try:
                all_matches.extend(fetch_from_api(args.api_url, args.date, logger, args.min_delay, args.max_delay))
            except Exception as exc:  # noqa: BLE001
                logger.warning("API 抓取失败：%s", exc)

        if not all_matches and args.page_url:
            try:
                all_matches.extend(fetch_from_page(args.page_url, args.date, logger, args.min_delay, args.max_delay))
            except Exception as exc:  # noqa: BLE001
                logger.warning("网页抓取失败：%s", exc)

        if not all_matches and args.csv:
            logger.info("开始使用 CSV 备用方案")
            all_matches.extend(load_from_csv(Path(args.csv), args.date, logger))

        if not all_matches:
            raise RuntimeError(
                "未获取到任何赛果数据。请检查 API/网页配置，或使用 --csv 指定备用文件。"
            )

        all_matches = deduplicate_matches(all_matches)
        save_outputs(root, args.date, all_matches, logger)
        logger.info("赛果抓取脚本执行完成，共保存 %s 场比赛", len(all_matches))
        return 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("赛果抓取脚本执行失败：%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
