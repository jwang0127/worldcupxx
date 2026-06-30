#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
今日分析脚本

功能说明：
1. 读取 schedule.csv 中今天的比赛
2. 读取昨天赛果，作为状态分析输入
3. 可尝试调用 DeepSeek API 或 Codex CLI 生成预测
4. 若 AI 调用失败，则自动回退为本地规则预测
5. 生成当日预测看板 HTML，并内嵌 JSON 供复盘脚本读取
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


DEFAULT_ROOT = Path(r"D:\WorldCupPredict")
PARLAY_MATCH_COUNT = 3
PARLAY_RULE_NOTE = "当日正好 3 场比赛时生成比分、总进球数、半场胜平负三类三串一；当日只有 1 场比赛时只做常规预测。赔率由 fetch_sporttery.ps1 从网站实时赔率接口拉取。"


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="生成今日世界杯预测看板")
    parser.add_argument("--root", default=os.environ.get("WORLD_CUP_ROOT", str(DEFAULT_ROOT)), help="项目根目录")
    parser.add_argument("--date", default=datetime.now().strftime("%Y%m%d"), help="分析日期，格式 yyyyMMdd")
    parser.add_argument("--schedule", default="", help="赛程 CSV 路径，默认读取根目录 schedule.csv")
    parser.add_argument("--history", default="", help="历史交锋 CSV 路径，默认读取根目录 history.csv")
    parser.add_argument("--model", default="auto", choices=["auto", "deepseek", "codex", "local"], help="分析引擎")
    return parser.parse_args()


def setup_logging(root: Path, date_str: str) -> logging.Logger:
    """初始化日志。"""
    logs_dir = root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = root / "log.txt"
    daily_log_file = logs_dir / f"analyze_today_{date_str}.log"

    logger = logging.getLogger("analyze_today")
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


def normalize_date_text(value: str) -> str:
    """统一日期格式。"""
    value = str(value or "").strip()
    if not value:
        return ""
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y%m%d")
        except ValueError:
            continue
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits[:8] if len(digits) >= 8 else value


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全转换浮点数。"""
    try:
        if value in (None, ""):
            return default
        return float(str(value).strip())
    except Exception:  # noqa: BLE001
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """安全转换整数。"""
    try:
        if value in (None, ""):
            return default
        return int(float(str(value).strip()))
    except Exception:  # noqa: BLE001
        return default


def safe_str(value: Any, default: str = "") -> str:
    """安全转换字符串。"""
    if value is None:
        return default
    return str(value).strip()


def load_csv_rows(csv_path: Path) -> List[Dict[str, str]]:
    """读取 CSV。"""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV 文件不存在：{csv_path}")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        return [dict(row) for row in reader]


def filter_today_matches(rows: List[Dict[str, str]], target_date: str) -> List[Dict[str, str]]:
    """筛选当天比赛。"""
    today_matches: List[Dict[str, str]] = []
    for row in rows:
        row_date = normalize_date_text(
            safe_str(row.get("date"))
            or safe_str(row.get("match_date"))
            or safe_str(row.get("比赛日期"))
            or safe_str(row.get("kickoff_date"))
        )
        if row_date == target_date:
            today_matches.append(row)
    return today_matches


def load_yesterday_results(root: Path, target_date: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """读取昨天赛果。"""
    yesterday = (datetime.strptime(target_date, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d")
    json_path = root / yesterday / f"match_results_{yesterday}.json"
    if not json_path.exists():
        logger.warning("昨天赛果文件不存在：%s", json_path)
        return []
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        logger.warning("读取昨天赛果失败：%s", exc)
        return []


def load_history_map(history_rows: List[Dict[str, str]]) -> Dict[Tuple[str, str], List[Dict[str, str]]]:
    """构建历史交锋索引。"""
    history_map: Dict[Tuple[str, str], List[Dict[str, str]]] = {}
    for row in history_rows:
        home = safe_str(row.get("home_team") or row.get("主队"))
        away = safe_str(row.get("away_team") or row.get("客队"))
        if not home or not away:
            continue
        key = (home, away)
        reverse_key = (away, home)
        history_map.setdefault(key, []).append(row)
        history_map.setdefault(reverse_key, []).append(row)
    return history_map


def detect_schedule_fields(row: Dict[str, str], fallback_index: int) -> Dict[str, Any]:
    """从赛程 CSV 中尽量抽取通用字段。"""
    return {
        "match_id": safe_str(row.get("match_id") or row.get("场次编号") or f"{fallback_index:03d}"),
        "home_team": safe_str(row.get("home_team") or row.get("主队")),
        "away_team": safe_str(row.get("away_team") or row.get("客队")),
        "kickoff": safe_str(row.get("kickoff") or row.get("开赛时间") or row.get("match_time") or row.get("比赛时间")),
        "venue": safe_str(row.get("venue") or row.get("场地") or row.get("stadium"), "待定"),
        "group_name": safe_str(row.get("group_name") or row.get("小组") or row.get("stage"), "世界杯"),
        "home_rank": safe_int(row.get("home_rank") or row.get("主队排名")),
        "away_rank": safe_int(row.get("away_rank") or row.get("客队排名")),
        "home_odds": safe_float(row.get("home_odds") or row.get("主胜赔率")),
        "draw_odds": safe_float(row.get("draw_odds") or row.get("平局赔率")),
        "away_odds": safe_float(row.get("away_odds") or row.get("客胜赔率")),
        "over_under": safe_float(row.get("over_under") or row.get("大小球")),
    }


def outcome_from_score(score_text: str) -> str:
    """根据比分字符串判断胜平负。"""
    normalized = score_text.replace("：", "-").replace(":", "-")
    home_str, away_str = normalized.split("-", 1)
    home_goals = int(home_str.strip())
    away_goals = int(away_str.strip())
    if home_goals > away_goals:
        return "home"
    if home_goals < away_goals:
        return "away"
    return "draw"


def score_options_from(total_goals: int, outcome: str) -> Tuple[List[str], str]:
    """根据总进球和方向生成稳胆比分与冷门比分。"""
    mapping = {
        ("home", 0): (["0-0", "1-0"], "0-1"),
        ("home", 1): (["1-0", "2-0"], "0-1"),
        ("home", 2): (["2-0", "1-1"], "0-1"),
        ("home", 3): (["2-1", "3-0"], "1-2"),
        ("home", 4): (["3-1", "2-2"], "1-2"),
        ("away", 0): (["0-0", "0-1"], "1-0"),
        ("away", 1): (["0-1", "1-1"], "1-0"),
        ("away", 2): (["0-2", "1-1"], "1-0"),
        ("away", 3): (["1-2", "0-3"], "2-1"),
        ("away", 4): (["1-3", "2-2"], "2-1"),
        ("draw", 0): (["0-0", "1-1"], "1-0"),
        ("draw", 1): (["1-1", "0-0"], "1-0"),
        ("draw", 2): (["1-1", "2-2"], "2-1"),
        ("draw", 3): (["2-2", "1-1"], "2-1"),
        ("draw", 4): (["2-2", "3-3"], "3-1"),
    }
    key = (outcome, min(total_goals, 4))
    return mapping.get(key, (["2-1", "1-1"], "1-2"))


def generate_local_prediction(
    match_info: Dict[str, Any],
    history_rows: List[Dict[str, str]],
    yesterday_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """本地规则预测，作为无 AI 时的兜底方案。"""
    home_odds = match_info["home_odds"]
    draw_odds = match_info["draw_odds"]
    away_odds = match_info["away_odds"]
    home_rank = match_info["home_rank"]
    away_rank = match_info["away_rank"]
    over_under = match_info["over_under"]

    scores = {"home": 0.0, "draw": 0.0, "away": 0.0}

    if home_odds > 0:
        scores["home"] += max(0.0, 4.5 - home_odds)
    if draw_odds > 0:
        scores["draw"] += max(0.0, 4.5 - draw_odds)
    if away_odds > 0:
        scores["away"] += max(0.0, 4.5 - away_odds)

    if home_rank and away_rank:
        if home_rank < away_rank:
            scores["home"] += 0.8
        elif away_rank < home_rank:
            scores["away"] += 0.8
        else:
            scores["draw"] += 0.4

    recent_boost = 0.0
    for item in yesterday_results:
        if match_info["home_team"] in (item.get("home_team"), item.get("away_team")):
            recent_boost += 0.1
        if match_info["away_team"] in (item.get("home_team"), item.get("away_team")):
            recent_boost += 0.1
    scores["draw"] += min(recent_boost, 0.3)

    if history_rows:
        home_history_advantage = 0
        away_history_advantage = 0
        for item in history_rows[:6]:
            home = safe_str(item.get("home_team") or item.get("主队"))
            away = safe_str(item.get("away_team") or item.get("客队"))
            home_score = safe_int(item.get("home_score") or item.get("主队进球"))
            away_score = safe_int(item.get("away_score") or item.get("客队进球"))
            if home == match_info["home_team"] and away == match_info["away_team"]:
                if home_score > away_score:
                    home_history_advantage += 1
                elif home_score < away_score:
                    away_history_advantage += 1
            elif home == match_info["away_team"] and away == match_info["home_team"]:
                if home_score > away_score:
                    away_history_advantage += 1
                elif home_score < away_score:
                    home_history_advantage += 1
        if home_history_advantage > away_history_advantage:
            scores["home"] += 0.6
        elif away_history_advantage > home_history_advantage:
            scores["away"] += 0.6
        else:
            scores["draw"] += 0.3

    stable_pick = max(scores.items(), key=lambda item: item[1])[0]
    upset_pick = sorted(scores.items(), key=lambda item: item[1])[1][0]

    if over_under > 0:
        total_goals = 3 if over_under >= 2.75 else 2 if over_under >= 2.25 else 1
    elif stable_pick == "draw":
        total_goals = 2
    else:
        total_goals = 2 if abs(home_rank - away_rank) <= 8 else 3

    stable_scores, upset_score = score_options_from(total_goals, stable_pick)
    confidence = "高" if max(scores.values()) >= 1.4 else "中"
    stable_label = outcome_label(stable_pick)

    analysis = [
        f"赔率方向初判为 {stable_label}，总进球主线倾向 {total_goals} 球。",
        f"历史交锋样本数：{len(history_rows)}，结合昨日日志做状态修正。",
        f"如果临场赔率剧烈波动，优先保留总进球主线，比分玩法建议降档。"
    ]

    return {
        "match_id": match_info["match_id"],
        "home_team": match_info["home_team"],
        "away_team": match_info["away_team"],
        "kickoff": match_info["kickoff"],
        "venue": match_info["venue"],
        "group_name": match_info["group_name"],
        "stable_pick": stable_pick,
        "upset_pick": upset_pick,
        "total_goals": str(total_goals),
        "stable_scores": stable_scores,
        "upset_score": upset_score,
        "confidence": confidence,
        "analysis": analysis,
        "source": "local_rules",
    }


def build_ai_prompt(
    target_date: str,
    matches: List[Dict[str, Any]],
    yesterday_results: List[Dict[str, Any]],
    history_map: Dict[Tuple[str, str], List[Dict[str, str]]],
) -> str:
    """构造给 AI 的提示词。"""
    payload = {
        "date": target_date,
        "today_matches": [],
        "yesterday_results": yesterday_results,
    }
    for match_info in matches:
        payload["today_matches"].append(
            {
                **match_info,
                "history_rows": history_map.get((match_info["home_team"], match_info["away_team"]), [])[:8],
            }
        )

    schema = {
        "matches": [
            {
                "match_id": "001",
                "home_team": "巴西",
                "away_team": "塞尔维亚",
                "stable_pick": "home",
                "upset_pick": "draw",
                "total_goals": "2",
                "stable_scores": ["2-0", "2-1"],
                "upset_score": "1-1",
                "confidence": "高",
                "analysis": ["一句原因一", "一句原因二", "一句风险提示"],
            }
        ]
    }

    return (
        "你是世界杯赛事分析师，请只返回 JSON，不要输出 Markdown。\n"
        "请基于今天赛程、昨天赛果和历史交锋，给出每场比赛的稳胆方向、冷门方向、总进球和两组稳胆比分。\n"
        "stable_pick 只能是 home / draw / away。\n"
        "upset_pick 只能是 home / draw / away。\n"
        "total_goals 必须是数字字符串，如 1、2、3、4。\n"
        f"输入数据：{json.dumps(payload, ensure_ascii=False)}\n"
        f"输出 JSON 示例：{json.dumps(schema, ensure_ascii=False)}"
    )


def try_call_deepseek(prompt: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """调用 DeepSeek API。"""
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        logger.info("未配置 DEEPSEEK_API_KEY，跳过 DeepSeek")
        return None

    url = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions").strip()
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat").strip()
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model,
        "temperature": 0.3,
        "messages": [
            {"role": "system", "content": "你是专业的世界杯数据分析助手。"},
            {"role": "user", "content": prompt},
        ],
    }

    try:
        response = requests.post(url, headers=headers, json=body, timeout=60)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(extract_json_text(content))
    except Exception as exc:  # noqa: BLE001
        logger.warning("DeepSeek 调用失败：%s", exc)
        return None


def try_call_codex(prompt: str, logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """调用 Codex CLI。"""
    command = os.environ.get("CODEX_CLI_COMMAND", "").strip()
    if not command:
        logger.info("未配置 CODEX_CLI_COMMAND，跳过 Codex CLI")
        return None

    try:
        completed = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            shell=True,
            timeout=120,
            check=True,
        )
        output_text = completed.stdout.strip()
        if not output_text:
            logger.warning("Codex CLI 没有返回内容")
            return None
        return json.loads(extract_json_text(output_text))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Codex CLI 调用失败：%s", exc)
        return None


def generate_predictions(
    target_date: str,
    matches: List[Dict[str, Any]],
    history_map: Dict[Tuple[str, str], List[Dict[str, str]]],
    yesterday_results: List[Dict[str, Any]],
    model: str,
    logger: logging.Logger,
) -> List[Dict[str, Any]]:
    """根据所选模型生成预测结果。"""
    prompt = build_ai_prompt(target_date, matches, yesterday_results, history_map)
    ai_payload: Optional[Dict[str, Any]] = None

    if model in ("auto", "deepseek"):
        ai_payload = try_call_deepseek(prompt, logger)
    if ai_payload is None and model in ("auto", "codex"):
        ai_payload = try_call_codex(prompt, logger)

    if ai_payload and isinstance(ai_payload.get("matches"), list):
        ai_map = {str(item.get("match_id", "")).strip(): item for item in ai_payload["matches"]}
        normalized_predictions: List[Dict[str, Any]] = []
        for match_info in matches:
            ai_item = ai_map.get(match_info["match_id"])
            if not ai_item:
                normalized_predictions.append(
                    generate_local_prediction(
                        match_info,
                        history_map.get((match_info["home_team"], match_info["away_team"]), []),
                        yesterday_results,
                    )
                )
                continue
            normalized_predictions.append(
                {
                    "match_id": match_info["match_id"],
                    "home_team": match_info["home_team"],
                    "away_team": match_info["away_team"],
                    "kickoff": match_info["kickoff"],
                    "venue": match_info["venue"],
                    "group_name": match_info["group_name"],
                    "stable_pick": safe_str(ai_item.get("stable_pick"), "home"),
                    "upset_pick": safe_str(ai_item.get("upset_pick"), "draw"),
                    "total_goals": safe_str(ai_item.get("total_goals"), "2"),
                    "stable_scores": list(ai_item.get("stable_scores") or ["2-0", "2-1"]),
                    "upset_score": safe_str(ai_item.get("upset_score"), "1-1"),
                    "confidence": safe_str(ai_item.get("confidence"), "中"),
                    "analysis": list(ai_item.get("analysis") or ["AI 未给出分析，已使用默认说明"]),
                    "source": "ai",
                }
            )
        return normalized_predictions

    logger.info("开始使用本地规则生成预测")
    return [
        generate_local_prediction(
            match_info,
            history_map.get((match_info["home_team"], match_info["away_team"]), []),
            yesterday_results,
        )
        for match_info in matches
    ]


def pick_total_goals_combo(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """生成总进球三串一。"""
    selected = predictions[:3]
    combo = []
    for item in selected:
        combo.append(
            {
                "match_id": item["match_id"],
                "match_name": f'{item["home_team"]} vs {item["away_team"]}',
                "pick_type": "total_goals",
                "pick_value": item["total_goals"],
            }
        )
    return combo


def pick_score_combo(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """生成比分三串一。"""
    selected = predictions[:3]
    combo = []
    for item in selected:
        combo.append(
            {
                "match_id": item["match_id"],
                "match_name": f'{item["home_team"]} vs {item["away_team"]}',
                "pick_type": "score",
                "pick_value": item["stable_scores"][0],
            }
        )
    return combo


def pick_half_time_combo(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """生成半场胜平负三串一。"""
    selected = predictions[:3]
    combo = []
    for item in selected:
        combo.append(
            {
                "match_id": item["match_id"],
                "match_name": f'{item["home_team"]} vs {item["away_team"]}',
                "pick_type": "half_time_outcome",
                "pick_value": item.get("half_time_pick", "draw"),
            }
        )
    return combo


def build_combo_payload(predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """只在三场比赛日生成三串一；单场日只保留常规预测。"""
    if len(predictions) != PARLAY_MATCH_COUNT:
        return {
            "enabled": False,
            "rule": PARLAY_RULE_NOTE,
            "total_goals": [],
            "score": [],
            "half_time": [],
        }
    return {
        "enabled": True,
        "rule": PARLAY_RULE_NOTE,
        "odds_source": "scripts/fetch_sporttery.ps1 -> Sporttery getMatchCalculatorV1 website API",
        "total_goals": pick_total_goals_combo(predictions),
        "score": pick_score_combo(predictions),
        "half_time": pick_half_time_combo(predictions),
    }


def outcome_label(value: str) -> str:
    """将内部方向值转成中文。"""
    return {"home": "主胜", "draw": "平局", "away": "客胜"}.get(value, value)


def extract_json_text(raw_text: str) -> str:
    """兼容提取被 Markdown 代码块包裹的 JSON。"""
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def generate_html(target_date: str, predictions: List[Dict[str, Any]], payload: Dict[str, Any]) -> str:
    """生成预测看板 HTML。"""
    cards: List[str] = []
    for item in predictions:
        analysis_html = "".join(f"<li>{html.escape(str(text))}</li>" for text in item["analysis"])
        score_tags = "".join(f'<span class="score">{html.escape(score)}</span>' for score in item["stable_scores"])
        cards.append(
            f"""
            <section class="card">
              <div class="meta">
                <span class="badge">{html.escape(item["match_id"])}</span>
                <span>{html.escape(item["group_name"])}</span>
                <span>{html.escape(item["kickoff"] or "时间待定")}</span>
                <span>{html.escape(item["venue"])}</span>
              </div>
              <h2>{html.escape(item["home_team"])} vs {html.escape(item["away_team"])}</h2>
              <div class="grid">
                <div class="panel">
                  <h3>稳胆方向</h3>
                  <p class="big">{outcome_label(item["stable_pick"])}</p>
                </div>
                <div class="panel">
                  <h3>冷门方向</h3>
                  <p class="big accent">{outcome_label(item["upset_pick"])}</p>
                </div>
                <div class="panel">
                  <h3>总进球</h3>
                  <p class="big">{html.escape(item["total_goals"])} 球</p>
                </div>
                <div class="panel">
                  <h3>置信度</h3>
                  <p class="big">{html.escape(item["confidence"])}</p>
                </div>
              </div>
              <div class="scores">
                <strong>稳胆比分：</strong>{score_tags}
                <strong class="upset">冷门比分：</strong><span class="score upset">{html.escape(item["upset_score"])}</span>
              </div>
              <ul class="analysis">{analysis_html}</ul>
            </section>
            """
        )

    combo_html = ""
    combo = payload.get("combo", {})
    if combo.get("enabled"):
        combo_html = f"""
    <section class="combo">
      <article class="combo-card">
        <h2>总进球三串一</h2>
        <ul>
          {''.join(f"<li>{html.escape(item['match_name'])}：{html.escape(item['pick_value'])} 球</li>" for item in combo['total_goals'])}
        </ul>
      </article>
      <article class="combo-card">
        <h2>比分三串一</h2>
        <ul>
          {''.join(f"<li>{html.escape(item['match_name'])}：{html.escape(item['pick_value'])}</li>" for item in combo['score'])}
        </ul>
      </article>
      <article class="combo-card">
        <h2>半场胜平负三串一</h2>
        <ul>
          {''.join(f"<li>{html.escape(item['match_name'])}：{html.escape(outcome_label(item['pick_value']))}</li>" for item in combo['half_time'])}
        </ul>
      </article>
    </section>
        """

    embedded_json = json.dumps(payload, ensure_ascii=False, indent=2)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>世界杯预测看板 {target_date}</title>
  <style>
    :root {{
      --bg: #f6efe3;
      --paper: rgba(255,255,255,0.86);
      --ink: #1f241f;
      --green: #0e5c44;
      --green-2: #2f8f6b;
      --red: #b74a3a;
      --line: #d8cbb6;
      --gold: #d6a84f;
      --shadow: 0 18px 40px rgba(60, 42, 18, 0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
      background:
        radial-gradient(circle at top right, rgba(214,168,79,.28), transparent 24%),
        radial-gradient(circle at left 20%, rgba(14,92,68,.16), transparent 30%),
        linear-gradient(135deg, #efe2c4 0%, #f8f4ec 54%, #ead6b7 100%);
    }}
    .wrap {{
      max-width: 1160px;
      margin: 0 auto;
      padding: 28px 18px 48px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(14,92,68,.95), rgba(31,36,31,.94));
      color: #fff;
      border-radius: 22px;
      padding: 28px;
      box-shadow: var(--shadow);
    }}
    .hero h1 {{
      margin: 0 0 12px;
      font-size: clamp(28px, 5vw, 44px);
    }}
    .hero p {{
      margin: 0;
      line-height: 1.8;
      color: rgba(255,255,255,.86);
    }}
    .combo {{
      margin-top: 22px;
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }}
    .combo-card, .card {{
      background: var(--paper);
      backdrop-filter: blur(10px);
      border: 1px solid rgba(255,255,255,.75);
      border-radius: 20px;
      box-shadow: var(--shadow);
    }}
    .combo-card {{
      padding: 18px 20px;
    }}
    .combo-card h2 {{
      margin: 0 0 10px;
      font-size: 20px;
    }}
    .combo-card ul {{
      margin: 0;
      padding-left: 18px;
      line-height: 1.8;
    }}
    .board {{
      margin-top: 26px;
      display: grid;
      gap: 18px;
    }}
    .card {{
      padding: 22px;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      color: #5d5f58;
      font-size: 14px;
    }}
    .badge {{
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(14,92,68,.12);
      color: var(--green);
      font-weight: 700;
    }}
    h2 {{
      margin: 14px 0 18px;
      font-size: clamp(24px, 4vw, 34px);
    }}
    .grid {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }}
    .panel {{
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px 16px;
      background: rgba(255,255,255,.72);
    }}
    .panel h3 {{
      margin: 0 0 8px;
      font-size: 14px;
      color: #7d6b54;
    }}
    .big {{
      margin: 0;
      font-size: 28px;
      font-weight: 800;
      color: var(--green);
    }}
    .accent {{
      color: var(--red);
    }}
    .scores {{
      margin-top: 16px;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 10px;
    }}
    .score {{
      display: inline-block;
      padding: 7px 11px;
      border-radius: 10px;
      background: rgba(14,92,68,.1);
      color: var(--green);
      font-weight: 700;
    }}
    .score.upset {{
      background: rgba(183,74,58,.12);
      color: var(--red);
    }}
    .upset {{
      margin-left: 12px;
    }}
    .analysis {{
      margin: 16px 0 0;
      padding-left: 18px;
      line-height: 1.8;
    }}
    @media (max-width: 860px) {{
      .combo, .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <h1>世界杯预测看板 {target_date}</h1>
      <p>本页由自动化脚本生成，综合赛程、昨日赛果、历史交锋与模型判断输出。复盘程序会直接读取本页内嵌 JSON 统计命中率。</p>
    </section>

    {combo_html}

    <main class="board">
      {''.join(cards)}
    </main>
  </div>
  <script id="prediction-data" type="application/json">{embedded_json}</script>
</body>
</html>
"""


def save_outputs(root: Path, target_date: str, html_text: str, payload: Dict[str, Any], logger: logging.Logger) -> None:
    """保存 HTML 和 JSON 快照。"""
    day_dir = root / target_date
    output_dir = root / "output"
    day_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    html_path = day_dir / f"predict_{target_date}.html"
    output_html_path = output_dir / f"predict_{target_date}.html"
    payload_path = day_dir / f"predict_{target_date}.json"

    html_path.write_text(html_text, encoding="utf-8")
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    shutil.copyfile(html_path, output_html_path)

    logger.info("预测 HTML 已保存：%s", html_path)
    logger.info("预测 JSON 已保存：%s", payload_path)
    logger.info("输出目录同步文件：%s", output_html_path)


def main() -> int:
    """程序入口。"""
    args = parse_args()
    root = Path(args.root).expanduser()
    logger = setup_logging(root, args.date)

    try:
        logger.info("今日分析脚本开始执行，目标日期：%s", args.date)
        schedule_path = Path(args.schedule).expanduser() if args.schedule else root / "schedule.csv"
        history_path = Path(args.history).expanduser() if args.history else root / "history.csv"

        schedule_rows = load_csv_rows(schedule_path)
        today_rows = filter_today_matches(schedule_rows, args.date)
        if not today_rows:
            raise RuntimeError(f"在 {schedule_path} 中未找到 {args.date} 的比赛")

        history_rows = load_csv_rows(history_path) if history_path.exists() else []
        history_map = load_history_map(history_rows)
        yesterday_results = load_yesterday_results(root, args.date, logger)

        matches = [detect_schedule_fields(row, index) for index, row in enumerate(today_rows, start=1)]
        predictions = generate_predictions(args.date, matches, history_map, yesterday_results, args.model, logger)

        payload = {
            "date": args.date,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "engine": args.model,
            "matches": predictions,
            "combo": build_combo_payload(predictions),
        }

        html_text = generate_html(args.date, predictions, payload)
        save_outputs(root, args.date, html_text, payload, logger)
        logger.info("今日分析脚本执行完成，共生成 %s 场比赛预测", len(predictions))
        return 0
    except Exception as exc:  # noqa: BLE001
        logger.exception("今日分析脚本执行失败：%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
