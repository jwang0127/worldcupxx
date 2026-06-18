#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
昨日复盘脚本

功能说明：
1. 自动读取昨天的赛果 JSON
2. 自动读取昨天的预测看板 HTML
3. 统计稳胆命中率、冷门命中、总进球准确率、三串一命中情况
4. 输出复盘报告 TXT
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ROOT = Path(r"D:\WorldCupPredict")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="复盘昨天的世界杯预测结果")
    parser.add_argument(
        "--root",
        default=os.environ.get("WORLD_CUP_ROOT", str(DEFAULT_ROOT)),
        help="项目根目录",
    )
    parser.add_argument(
        "--date",
        default=(datetime.now() - timedelta(days=1)).strftime("%Y%m%d"),
        help="复盘日期，默认昨天，格式 yyyyMMdd",
    )
    return parser.parse_args()


def setup_logging(root: Path, date_str: str) -> logging.Logger:
    """初始化日志。"""
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = root / "log.txt"
    daily_log_file = logs_dir / f"review_yesterday_{date_str}.log"

    logger = logging.getLogger("review_yesterday")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    for file_path in (log_file, daily_log_file):
        handler = logging.FileHandler(file_path, encoding="utf-8")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def load_results(root: Path, date_str: str) -> List[Dict[str, Any]]:
    """读取赛果文件。"""
    json_path = root / date_str / f"match_results_{date_str}.json"
    if not json_path.exists():
        raise FileNotFoundError(f"赛果文件不存在：{json_path}")
    return json.loads(json_path.read_text(encoding="utf-8"))


def find_prediction_html(root: Path, date_str: str) -> Optional[Path]:
    """查找预测 HTML 文件。"""
    candidates = [
        root / date_str / f"predict_{date_str}.html",
        root / "output" / f"predict_{date_str}.html",
        root / f"predict_{date_str}.html",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def extract_prediction_payload(html_text: str) -> Dict[str, Any]:
    """从 HTML 中提取内嵌的预测 JSON。"""
    pattern = r'<script id="prediction-data" type="application/json">(.*?)</script>'
    matched = re.search(pattern, html_text, flags=re.DOTALL | re.IGNORECASE)
    if not matched:
        raise ValueError("预测 HTML 中未找到 prediction-data JSON 片段")
    return json.loads(matched.group(1))


def compute_outcome(home_score: int, away_score: int) -> str:
    """计算比赛胜平负结果。"""
    if home_score > away_score:
        return "home"
    if home_score < away_score:
        return "away"
    return "draw"


def parse_score_text(score_text: str) -> Tuple[int, int]:
    """解析比分字符串。"""
    normalized = score_text.replace("：", "-").replace(":", "-")
    home_str, away_str = normalized.split("-", 1)
    return int(home_str.strip()), int(away_str.strip())


def calc_percentage(hit: int, total: int) -> str:
    """计算百分比文本。"""
    if total <= 0:
        return "0.00%"
    return f"{(hit / total) * 100:.2f}%"


def evaluate_combo(
    combo_items: List[Dict[str, Any]],
    result_map: Dict[str, Dict[str, Any]],
) -> Tuple[bool, List[str]]:
    """评估三串一是否命中。"""
    messages: List[str] = []
    if not combo_items:
        return False, ["未提供三串一数据"]

    all_hit = True
    for item in combo_items:
        match_id = str(item.get("match_id", "")).strip()
        actual = result_map.get(match_id)
        if not actual:
            all_hit = False
            messages.append(f"{match_id} 缺少赛果，无法判断")
            continue

        actual_home = int(actual["home_score"])
        actual_away = int(actual["away_score"])
        actual_total = actual_home + actual_away
        actual_outcome = compute_outcome(actual_home, actual_away)
        pick_type = item.get("pick_type")
        pick_value = item.get("pick_value")

        hit = False
        if pick_type == "total_goals":
            hit = str(actual_total) == str(pick_value)
        elif pick_type == "outcome":
            hit = actual_outcome == str(pick_value)
        elif pick_type == "score":
            hit = f"{actual_home}-{actual_away}" == str(pick_value).replace("：", "-").replace(":", "-")

        if not hit:
            all_hit = False
        messages.append(
            f'{match_id} {actual["home_team"]} {actual_home}-{actual_away} {actual["away_team"]} '
            f'| 玩法={pick_type} | 预测={pick_value} | {"命中" if hit else "未命中"}'
        )

    return all_hit, messages


def build_report(
    results: List[Dict[str, Any]],
    prediction_payload: Optional[Dict[str, Any]],
    html_path: Optional[Path],
    date_str: str,
) -> str:
    """生成复盘报告文本。"""
    lines: List[str] = []
    lines.append(f"世界杯昨日复盘报告 - {date_str}")
    lines.append("=" * 48)
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"赛果场次：{len(results)}")
    lines.append(f"预测文件：{html_path if html_path else '未找到'}")
    lines.append("")

    if not prediction_payload:
        lines.append("未找到可解析的预测看板，无法统计命中率。")
        lines.append("")
        lines.append("实际赛果：")
        for item in results:
            lines.append(
                f'{item["match_id"]} | {item["home_team"]} {item["home_score"]}-{item["away_score"]} '
                f'{item["away_team"]} | 总进球 {item["total_goals"]} | 半场 {item["half_time_score"]}'
            )
        return "\n".join(lines)

    prediction_matches = prediction_payload.get("matches", [])
    prediction_map = {str(item.get("match_id", "")).strip(): item for item in prediction_matches}
    result_map = {str(item["match_id"]).strip(): item for item in results}

    stable_total = 0
    stable_hit = 0
    upset_total = 0
    upset_hit = 0
    total_goals_total = 0
    total_goals_hit = 0

    lines.append("一、核心命中统计")
    lines.append("-" * 48)

    detail_lines: List[str] = []
    for match_id, actual in result_map.items():
        predicted = prediction_map.get(match_id)
        if not predicted:
            detail_lines.append(f"{match_id} 未找到对应预测记录")
            continue

        actual_home = int(actual["home_score"])
        actual_away = int(actual["away_score"])
        actual_outcome = compute_outcome(actual_home, actual_away)
        actual_total_goals = actual_home + actual_away

        stable_outcome = str(predicted.get("stable_pick", "")).strip()
        upset_outcome = str(predicted.get("upset_pick", "")).strip()
        predicted_total_goals = str(predicted.get("total_goals", "")).strip()

        if stable_outcome:
            stable_total += 1
            if stable_outcome == actual_outcome:
                stable_hit += 1

        if upset_outcome:
            upset_total += 1
            if upset_outcome == actual_outcome:
                upset_hit += 1

        if predicted_total_goals:
            total_goals_total += 1
            if predicted_total_goals == str(actual_total_goals):
                total_goals_hit += 1

        detail_lines.append(
            f'{match_id} | {actual["home_team"]} {actual_home}-{actual_away} {actual["away_team"]} '
            f'| 稳胆={"命中" if stable_outcome == actual_outcome else "未中"} '
            f'| 冷门={"命中" if upset_outcome == actual_outcome else "未中"} '
            f'| 总进球预测={predicted_total_goals} 实际={actual_total_goals}'
        )

    lines.append(f"稳胆命中率：{stable_hit}/{stable_total}（{calc_percentage(stable_hit, stable_total)}）")
    lines.append(f"冷门命中率：{upset_hit}/{upset_total}（{calc_percentage(upset_hit, upset_total)}）")
    lines.append(
        f"总进球预测准确率：{total_goals_hit}/{total_goals_total}（{calc_percentage(total_goals_hit, total_goals_total)}）"
    )

    combo = prediction_payload.get("combo", {})
    total_goals_combo_hit, total_goals_combo_messages = evaluate_combo(combo.get("total_goals", []), result_map)
    score_combo_hit, score_combo_messages = evaluate_combo(combo.get("score", []), result_map)

    lines.append(f"三串一（总进球）是否命中：{'是' if total_goals_combo_hit else '否'}")
    lines.append(f"三串一（比分）是否命中：{'是' if score_combo_hit else '否'}")
    lines.append("")

    lines.append("二、逐场复盘")
    lines.append("-" * 48)
    lines.extend(detail_lines or ["无逐场数据"])
    lines.append("")

    lines.append("三、三串一复盘")
    lines.append("-" * 48)
    lines.append("总进球三串一：")
    lines.extend(total_goals_combo_messages)
    lines.append("")
    lines.append("比分三串一：")
    lines.extend(score_combo_messages)
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    """程序入口。"""
    args = parse_args()
    root = Path(args.root).expanduser()
    logger = setup_logging(root, args.date)

    try:
        logger.info("昨日复盘脚本开始执行，目标日期：%s", args.date)
        results = load_results(root, args.date)
        html_path = find_prediction_html(root, args.date)

        prediction_payload: Optional[Dict[str, Any]] = None
        if html_path:
            try:
                prediction_payload = extract_prediction_payload(html_path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                logger.warning("解析预测看板失败：%s", exc)

        report_text = build_report(results, prediction_payload, html_path, args.date)
        output_path = root / args.date / f"review_{args.date}.txt"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report_text, encoding="utf-8")

        logger.info("复盘报告已生成：%s", output_path)
        logger.info("昨日复盘脚本执行完成")
        return 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("昨日复盘脚本执行失败：%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
