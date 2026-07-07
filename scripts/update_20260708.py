#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATE = "20260708"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def odds_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_odds(value: Any) -> str:
    number = odds_float(value)
    return "-" if number is None else f"{number:.2f}"


def load_world_cup_odds() -> dict[str, dict[str, Any]]:
    payload = read_json(DATA_DIR / f"{DATE}.json")
    return {
        str(item["id"]).lstrip("0"): item
        for item in payload.get("matches", [])
        if item.get("league") == "世界杯"
    }


def load_world_cup_match(date: str, match_no: str) -> dict[str, Any]:
    payload = read_json(DATA_DIR / f"{date}.json")
    for item in payload.get("matches", []):
        if item.get("league") == "世界杯" and str(item.get("id", "")).lstrip("0") == str(match_no):
            return item
    raise KeyError(f"World Cup match {match_no} not found in data/{date}.json")


def css() -> str:
    return """
:root{--bg:#071310;--card:#10221f;--panel:#132b26;--line:#24483f;--text:#eefbf6;--muted:#9ab7ae;--green:#58d68d;--blue:#73c7ff;--gold:#f2c15a;--red:#ff817b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.65}
header{padding:24px 18px 12px;max-width:1180px;margin:auto}h1{margin:0 0 14px;font-size:32px;letter-spacing:0}
nav{display:flex;gap:10px;flex-wrap:wrap}nav a{color:var(--text);text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:7px 10px;background:#0c1b18}
main{max-width:1180px;margin:auto;padding:0 18px 42px}.section{margin-top:22px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin-top:12px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px}
.metric strong{display:block;color:var(--green);font-size:24px}.metric small,.muted{color:var(--muted)}.good{color:var(--green)}.warn{color:var(--gold)}.bad{color:var(--red)}
.tableWrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:760px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{color:var(--blue);font-weight:700}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 8px;margin:2px;background:#0c1b18}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;margin-top:14px;overflow:hidden}summary{cursor:pointer;padding:15px 16px;display:grid;grid-template-columns:1fr auto 1.4fr;gap:12px;align-items:center}summary strong{color:var(--green);font-size:24px}
.body{border-top:1px solid var(--line);padding:16px}.analysisTables{display:grid;grid-template-columns:minmax(260px,.62fr) minmax(0,1.38fr);gap:12px;align-items:start}.scoreMatrix table,.evTable table{min-width:0}.evTable table{table-layout:fixed}.evTable td{word-break:break-word}
@media(max-width:900px){.grid,.cols,summary,.analysisTables{grid-template-columns:1fr}h1{font-size:26px}table{min-width:680px}.scoreMatrix table,.evTable table{min-width:0}}
"""


def build_results() -> dict[str, Any]:
    return {
        "date": "20260707",
        "stage": "knockout",
        "status": "90min_finished",
        "matches": [
            {
                "game_id": "53452513",
                "match_no": "93",
                "home_team": "葡萄牙",
                "away_team": "西班牙",
                "score": "0-1",
                "home_goals": 0,
                "away_goals": 1,
                "decisive_moment": "90+1分钟西班牙进球",
                "winner_team": "西班牙",
                "advance_team": "西班牙",
                "prediction_main_score": "1-2",
                "prediction_backup_scores": ["0-2", "1-1"],
                "prediction_upset_score": "2-1",
                "in_score_pool": False,
                "review": "方向命中但0-1没有进入比分池。根因不是昨天大比分后今天必小，而是西班牙优势被模型翻译成双方进球/2-3球，低估了淘汰赛末段才破门、葡萄牙低位拖慢节奏以及领先后立即收住的1球路径。后续强队低赔且总进球2/3接近时，必须把1-0或0-1放入比分池。",
            },
            {
                "game_id": "53452515",
                "match_no": "94",
                "home_team": "美国",
                "away_team": "比利时",
                "score": "1-4",
                "home_goals": 1,
                "away_goals": 4,
                "winner_team": "比利时",
                "advance_team": "比利时",
                "prediction_main_score": "1-1",
                "prediction_backup_scores": ["2-1", "1-2"],
                "prediction_upset_score": "0-1",
                "in_score_pool": False,
                "review": "方向和比分池均失手，1-4没有进入池。根因是模型把美国主场和均势赔率保护得过重，把比利时高质量进攻、领先后美国压上产生的连续反击空间降成了1-2/2-2观察项。后续主队有进球路但防线被客队速度/转换克制时，比分池不能只保守到1-2，必须给1-3/1-4一个尾部候选。",
            },
        ],
    }


def build_lessons() -> dict[str, Any]:
    return {
        "date": "20260707",
        "headline": "07-07复盘：同日出现0-1和1-4，问题是比分池尾部覆盖不足，不是简单追大追小",
        "summary": "葡萄牙0-1西班牙说明强队优势也可能只在最后阶段兑现，低总进球路径不能被双方进球模型挤掉；美国1-4比利时说明均势/主场保护不能压过进攻质量和落后后压上带来的尾部放大。今日模型同时保留低比分正路和大比分尾部，但不因昨日大小球结果做机械外推。",
        "lessons": [
            "比分池必须覆盖盘口低位以外的结构性路径：0-1和1-4都曾在赔率表存在，但没有进入展示池，说明筛选层过窄。",
            "强队低赔不等于必穿大球。若对手能拖节奏且总进球2/3接近，1-0或0-1需要进入稳胆池。",
            "均势赔率不等于比分均势。若客队进攻质量更好，且主队落后后必须压上，1-3/1-4必须进入防大池。",
            "今日不做大小球惯性外推：阿根廷场看强弱差与埃及抗压，瑞士场看哥伦比亚方向与低总进球，不因为昨日有1-4就强行追大。",
            "串关主线从精确比分降权，优先方向/总进球组合；比分串只小注，并明确列出尾部防线。",
        ],
        "weight_adjustments": {
            "late_single_goal_path": 0.07,
            "score_pool_tail_coverage": 0.08,
            "home_field_overprotection": -0.06,
            "market_odds_direct_inference": -0.04,
            "attack_quality_transition": 0.07,
            "yesterday_score_pattern_inertia": -0.09,
        },
    }


def prediction_payload(odds: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "date": DATE,
        "stage": "knockout",
        "review_source": "data/model_review_lessons_20260707.json",
        "matches": [
            {
                "game_id": "53452521",
                "match_no": "95",
                "round": "16强赛",
                "home_team": "阿根廷",
                "away_team": "埃及",
                "kickoff_bjt": "2026-07-08 00:00:00 +08:00",
                "venue": odds["95"].get("venue", ""),
                "model_version": "v8.4-score-pool-tail-coverage",
                "direction_90min": "home",
                "direction_text": "阿根廷90分钟胜优先，主线2-0，防1-0/2-1",
                "half_time": "阿根廷 1-0 埃及",
                "half_time_pick": "home",
                "hafu_pick": "hh",
                "main_score": "2-0",
                "backup_scores": ["1-0", "2-1"],
                "tail_scores": ["3-0", "1-1"],
                "upset_score": "1-1",
                "goals_range": "1-3球，核心2球",
                "advance_pick": "阿根廷",
                "advance_probability_text": "90分钟：阿根廷胜 70% / 平 20% / 埃及胜 10%；最终晋级：阿根廷 82% / 埃及 18%",
                "core_view": "阿根廷实力、控场和淘汰赛经验明显在上，HAD主胜1.22给出方向确认，但不能直接从低赔推出大胜。埃及小组不败、上一轮点球晋级，说明抗压和拖节奏能力有效；因此主线是阿根廷2-0，比分池补入1-0来吸收昨日0-1漏池教训，同时保留2-1防埃及定位球/反击破门。",
                "review_adjustment": "昨日0-1提示强队末段兑现的低比分必须入池，昨日1-4提示尾部大比分不能消失。本场不追昨日大小球惯性：2球为主，3-0只作早球/压制触发，1-1作冷平保护。",
                "score_matrix_top": [
                    {"score": "2-0", "probability": 0.20, "ev_signal": "+0.04", "label": "强队正路零封"},
                    {"score": "1-0", "probability": 0.16, "ev_signal": "+0.03", "label": "末段兑现/降速"},
                    {"score": "2-1", "probability": 0.13, "ev_signal": "+0.02", "label": "埃及破门保护"},
                    {"score": "3-0", "probability": 0.11, "ev_signal": "防穿", "label": "早球后拉开"},
                    {"score": "1-1", "probability": 0.08, "ev_signal": "防冷", "label": "埃及拖入加时"},
                ],
                "ev_table": [
                    {"market": "阿根廷90分钟方向", "model_probability": 0.70, "fair_odds": 1.43, "market_odds": odds["95"]["odds"]["had"]["home"], "ev_signal": "方向确认", "note": "赔率支持强方向，但不直接等同高EV。"},
                    {"market": "比分：2-0 / 1-0 / 2-1", "model_probability": 0.49, "fair_odds": 2.04, "market_odds": "4.50 / 5.70 / 6.80", "ev_signal": "+0.04", "note": "把1-0纳入稳胆池，修正昨日低比分漏池。"},
                    {"market": "总进球：2球，防1/3球", "model_probability": 0.61, "fair_odds": 1.64, "market_odds": f"{odds['95']['odds']['ttg']['s2']} / {odds['95']['odds']['ttg']['s1']} / {odds['95']['odds']['ttg']['s3']}", "ev_signal": "+0.03", "note": "2球最低且结构吻合，不机械追大。"},
                    {"market": "半全场：胜胜", "model_probability": 0.56, "fair_odds": 1.79, "market_odds": odds["95"]["odds"]["hafu"]["hh"], "ev_signal": "低赔稳定", "note": "阿根廷早段建立优势路径最清晰。"},
                ],
                "model_insights": [
                    {"title": "比分池", "content": "稳胆2-0、1-0、2-1；防穿3-0，防冷1-1。"},
                    {"title": "伤停/体能", "content": "未纳入新增硬伤停，埃及连续高压淘汰赛后体能劣势更明显。"},
                    {"title": "串关", "content": "适合做二串一第一腿方向或总进球2/3，不建议单压大胜比分。"},
                ],
                "team_reading": [
                    "阿根廷强在控场、禁区前连续创造和领先后的节奏管理。",
                    "埃及强在低位抗压和反击第一脚，弱点是长期被压后出球质量下降。",
                    "赔率、实力和赛程结构都支持阿根廷，但比分池必须保留1-0低比分正路。",
                ],
                "triggers": [
                    "阿根廷30分钟前进球：2-0/3-0升权，1-0降一档。",
                    "半场0-0：1-0和1-1升权，胜胜半全场降权。",
                    "埃及先破门：2-1与1-1升权，总进球3球进入主池。",
                ],
                "odds_snapshot": odds["95"],
                "odds_source": "Sporttery calculator getMatchCalculatorV1, data/20260708.json",
            },
            {
                "game_id": "53452523",
                "match_no": "96",
                "round": "16强赛",
                "home_team": "瑞士",
                "away_team": "哥伦比亚",
                "kickoff_bjt": "2026-07-08 04:00:00 +08:00",
                "venue": odds["96"].get("venue", ""),
                "model_version": "v8.4-score-pool-tail-coverage",
                "direction_90min": "away",
                "direction_text": "哥伦比亚90分钟不败，主线1-1，防0-1/1-2",
                "half_time": "瑞士 0-0 哥伦比亚",
                "half_time_pick": "draw",
                "hafu_pick": "dd",
                "main_score": "1-1",
                "backup_scores": ["0-1", "1-2"],
                "tail_scores": ["0-2", "2-1"],
                "upset_score": "2-1",
                "goals_range": "1-3球，核心2球",
                "advance_pick": "哥伦比亚",
                "advance_probability_text": "90分钟：瑞士胜 26% / 平 31% / 哥伦比亚胜 43%；最终晋级：瑞士 42% / 哥伦比亚 58%",
                "core_view": "哥伦比亚方向更优，客胜2.12与比分低位0-1/1-2给出支持；但瑞士淘汰赛2-0和小组稳定性说明其低风险防守不能被忽略。总进球2球最低、0-0赔率不高，说明比赛可能长时间胶着。主线选1-1，实际晋级略偏哥伦比亚，0-1与1-2作为客胜路径。",
                "review_adjustment": "昨日1-4提醒尾部比分要有覆盖，但本场两队结构不是开放对攻，不能因昨日大比分就追3/4球。比分池加入0-2作为哥伦比亚顺风尾部，也保留2-1防瑞士利用定位球和领先后降速。",
                "score_matrix_top": [
                    {"score": "1-1", "probability": 0.18, "ev_signal": "+0.04", "label": "均势主线"},
                    {"score": "0-1", "probability": 0.16, "ev_signal": "+0.03", "label": "哥伦比亚小胜"},
                    {"score": "1-2", "probability": 0.14, "ev_signal": "+0.03", "label": "客胜开放延展"},
                    {"score": "0-2", "probability": 0.09, "ev_signal": "防穿", "label": "顺风零封"},
                    {"score": "2-1", "probability": 0.08, "ev_signal": "防冷", "label": "瑞士定位球反打"},
                ],
                "ev_table": [
                    {"market": "哥伦比亚不败/90分钟方向", "model_probability": 0.74, "fair_odds": 1.35, "market_odds": f"{odds['96']['odds']['had']['draw']} / {odds['96']['odds']['had']['away']}", "ev_signal": "+0.03", "note": "方向偏客，但平局保护很重。"},
                    {"market": "比分：1-1 / 0-1 / 1-2", "model_probability": 0.48, "fair_odds": 2.08, "market_odds": "4.50 / 7.00 / 6.50", "ev_signal": "+0.04", "note": "比分池覆盖平局与客胜两条主路径。"},
                    {"market": "总进球：2球，防1/3球", "model_probability": 0.60, "fair_odds": 1.67, "market_odds": f"{odds['96']['odds']['ttg']['s2']} / {odds['96']['odds']['ttg']['s1']} / {odds['96']['odds']['ttg']['s3']}", "ev_signal": "+0.04", "note": "2球最低且符合淘汰赛胶着。"},
                    {"market": "半全场：平平 / 平负", "model_probability": 0.45, "fair_odds": 2.22, "market_odds": f"{odds['96']['odds']['hafu']['dd']} / {odds['96']['odds']['hafu']['da']}", "ev_signal": "+0.03", "note": "半场僵持概率高，下半场哥伦比亚解决比赛是次路径。"},
                ],
                "model_insights": [
                    {"title": "比分池", "content": "稳胆1-1、0-1、1-2；防穿0-2，防冷2-1。"},
                    {"title": "伤停/体能", "content": "未纳入新增硬伤停，瑞士稳定性高，哥伦比亚前场冲击更强。"},
                    {"title": "串关", "content": "更适合做总进球2或哥伦比亚不败，不建议重仓单一客胜比分。"},
                ],
                "team_reading": [
                    "瑞士强在防守站位、定位球和领先后的降速能力。",
                    "哥伦比亚强在前场个人能力和转换速度，能制造更高质量的最后一击。",
                    "赔率不能直接决定结果，但与实力画像一致：哥伦比亚略优，平局权重必须保留。",
                ],
                "triggers": [
                    "半场0-0：1-1和0-1继续升权，2球总进球最稳。",
                    "哥伦比亚先进球：0-1/0-2升权，瑞士压上后1-2保留。",
                    "瑞士先进球：2-1和1-1升权，哥伦比亚晋级概率下调。",
                ],
                "odds_snapshot": odds["96"],
                "odds_source": "Sporttery calculator getMatchCalculatorV1, data/20260708.json",
            },
        ],
    }


def make_leg(match: dict[str, Any], score_pick: str, goals_pick: str, hafu_pick: str, note: str, ev_signal: str = "+0.03") -> dict[str, Any]:
    odds = match["odds_snapshot"]["odds"]
    score_odds = " / ".join(fmt_odds(odds["crs"].get(score)) for score in score_pick.split(" / "))
    goals_odds = " / ".join(fmt_odds(odds["ttg"].get(f"s{goal.strip()}")) for goal in goals_pick.replace("球", "").split(" / "))
    hafu_map = {"胜胜": "hh", "平胜": "dh", "平平": "dd", "平负": "da", "负负": "aa", "胜平": "hd", "负平": "ad"}
    hafu_odds = " / ".join(fmt_odds(odds["hafu"].get(hafu_map.get(item.strip(), ""))) for item in hafu_pick.split(" / "))
    return {
        "match_no": match["match_no"],
        "match": f"{match['home_team']} vs {match['away_team']}",
        "direction": match["direction_text"],
        "score_pick": score_pick,
        "score_odds": score_odds,
        "goals_pick": goals_pick,
        "goals_odds": goals_odds,
        "half_full_pick": hafu_pick,
        "half_full_odds": hafu_odds,
        "ev_signal": ev_signal,
        "note": note,
    }


def build_parlay(predictions: dict[str, Any]) -> dict[str, Any]:
    matches = {item["match_no"]: item for item in predictions["matches"]}
    match97_odds = load_world_cup_match("20260710", "97")
    match97 = {
        "match_no": "97",
        "home_team": "法国",
        "away_team": "摩洛哥",
        "direction_text": "法国90分钟胜优先，主线2-0，防2-1/1-1",
        "odds_snapshot": match97_odds,
    }
    leg95 = make_leg(matches["95"], "2-0 / 1-0", "2球 / 3球", "胜胜 / 平胜", "阿根廷方向稳定，比分池补入1-0吸收昨日低比分漏池。")
    leg96 = make_leg(matches["96"], "1-1 / 0-1", "2球 / 1球", "平平 / 平负", "哥伦比亚略优但平局保护重，适合总进球和不败路径。")
    leg97 = make_leg(match97, "2-0 / 2-1", "2球 / 3球", "胜胜 / 平胜", "法国方向稳定但不追穿，摩洛哥抗压强，比分池保留2-1与1-1防线。")
    return {
        "date": DATE,
        "stage": "round16_parlay",
        "headline": "07-08更新：比分串降权，方向+总进球为主，防0-1与1-4两类漏池",
        "summary": "今日95/96主推二串一；三串一第三腿接入下一场97法国 vs 摩洛哥，不再重复96。组合仍以方向+总进球为主，不把昨日大比分或小比分机械外推到今天。",
        "groups": [
            {
                "title": "主票：95-96二串一",
                "summary": "阿根廷胜/总进球2-3 + 哥伦比亚不败/总进球1-2，比分只作辅助。",
                "legs": [leg95, leg96],
            },
            {
                "title": "比分二串一小注",
                "summary": "只保留低仓位，重点覆盖昨日漏掉的1球正路和客队小胜路径。",
                "legs": [
                    make_leg(matches["95"], "2-0", "2球", "胜胜", "阿根廷正路零封，但1-0需同步防。", "+0.02"),
                    make_leg(matches["96"], "1-1", "2球", "平平", "瑞士胶着能力强，哥伦比亚晋级可留到加时/点球。", "+0.02"),
                ],
            },
            {
                "title": "三串一：方向/总进球混合",
                "summary": "95、96、97三场各取一腿，避免把精确比分当主仓。",
                "legs": [
                    make_leg(matches["95"], "2-0 / 1-0", "2球", "胜胜", "阿根廷胜方向腿。"),
                    make_leg(matches["96"], "1-1 / 0-1", "2球", "平平 / 平负", "96总进球2球腿。"),
                    make_leg(match97, "2-0 / 2-1", "2球 / 3球", "胜胜 / 平胜", "97法国方向腿，防摩洛哥把比赛拖窄。", "+0.02"),
                ],
            },
        ],
        "odds_source": "Sporttery calculator getMatchCalculatorV1, data/20260708.json for 95/96; data/20260710.json for 97",
    }


def render_parlay_group(group: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{esc(item['match_no'])}</td><td>{esc(item['match'])}</td><td>{esc(item['direction'])}</td>"
        f"<td>{esc(item['score_pick'])}</td><td>{esc(item['score_odds'])}</td>"
        f"<td>{esc(item['goals_pick'])}</td><td>{esc(item['goals_odds'])}</td>"
        f"<td>{esc(item['half_full_pick'])}</td><td>{esc(item['half_full_odds'])}</td>"
        f"<td>{esc(item['ev_signal'])}</td><td>{esc(item['note'])}</td>"
        "</tr>"
        for item in group.get("legs", [])
    )
    return f"""<div class="card"><h3>{esc(group['title'])}</h3><p class="muted">{esc(group['summary'])}</p>
<div class="tableWrap"><table><thead><tr><th>场次</th><th>比赛</th><th>方向</th><th>比分</th><th>比分赔率</th><th>总进球</th><th>进球赔率</th><th>半全场</th><th>半全场赔率</th><th>EV</th><th>说明</th></tr></thead><tbody>{rows}</tbody></table></div></div>"""


def render_prediction_page(predictions: dict[str, Any], lessons: dict[str, Any], parlay: dict[str, Any]) -> str:
    cards: list[str] = []
    for item in predictions["matches"]:
        matrix = "".join(
            f"<tr><td>{esc(row['score'])}</td><td>{float(row['probability'])*100:.1f}%</td><td>{esc(row['ev_signal'])}</td><td>{esc(row['label'])}</td></tr>"
            for row in item["score_matrix_top"]
        )
        ev_rows = "".join(
            f"<tr><td>{esc(row['market'])}</td><td>{float(row['model_probability'])*100:.1f}%</td><td>{float(row['fair_odds']):.2f}</td><td>{esc(row.get('market_odds','-'))}</td><td>{esc(row['ev_signal'])}</td><td>{esc(row['note'])}</td></tr>"
            for row in item["ev_table"]
        )
        insights = "".join(f"<div class='panel'><h3>{esc(row['title'])}</h3><p>{esc(row['content'])}</p></div>" for row in item["model_insights"])
        reading = "".join(f"<li>{esc(text)}</li>" for text in item["team_reading"])
        triggers = "".join(f"<li>{esc(text)}</li>" for text in item["triggers"])
        odds = item["odds_snapshot"]["odds"]
        cards.append(
            f"""<details open><summary><span>{esc(item['match_no'])} {esc(item['home_team'])} vs {esc(item['away_team'])}</span><strong>{esc(item['main_score'])}</strong><em>{esc(item['direction_text'])} / 晋级 {esc(item['advance_pick'])}</em></summary>
<div class="body">
<div class="grid">
<div class="panel metric">开球<strong>{esc(item['kickoff_bjt'][5:16])}</strong><small>{esc(item['venue'])}</small></div>
<div class="panel metric">半场<strong>{esc(item['half_time'])}</strong><small>半全场 {esc(item['hafu_pick'])}</small></div>
<div class="panel metric">90分钟<strong>{esc(item['direction_text'])}</strong><small>{esc(item['goals_range'])}</small></div>
<div class="panel metric">晋级<strong>{esc(item['advance_pick'])}</strong><small>{esc(item['advance_probability_text'])}</small></div>
</div>
<div class="card"><h3>判断路径</h3><p>{esc(item['core_view'])}</p><p class="muted">{esc(item['review_adjustment'])}</p></div>
<div class="analysisTables"><div class="card scoreMatrix"><h3>比分池</h3><div class="tableWrap"><table><thead><tr><th>比分</th><th>概率</th><th>EV</th><th>标签</th></tr></thead><tbody>{matrix}</tbody></table></div></div>
<div class="card evTable"><h3>EV表</h3><div class="tableWrap"><table><thead><tr><th>市场</th><th>模型概率</th><th>公平赔率</th><th>市场赔率</th><th>EV</th><th>说明</th></tr></thead><tbody>{ev_rows}</tbody></table></div></div></div>
<div class="grid">{insights}</div>
<div class="cols"><div class="card"><h3>球队画像</h3><ul>{reading}</ul></div><div class="card"><h3>触发条件</h3><ul>{triggers}</ul></div></div>
<div class="card"><h3>赔率快照</h3><p class="muted">HAD {esc(odds['had']['home'])}/{esc(odds['had']['draw'])}/{esc(odds['had']['away'])}；TTG低位：2球 {esc(odds['ttg']['s2'])}，3球 {esc(odds['ttg']['s3'])}；比分低位参考：1-1 {esc(odds['crs'].get('1-1'))}，2-0 {esc(odds['crs'].get('2-0'))}，0-1 {esc(odds['crs'].get('0-1'))}。来源：{esc(item['odds_source'])}</p></div>
</div></details>"""
        )
    lesson_items = "".join(f"<li>{esc(text)}</li>" for text in lessons["lessons"])
    parlay_html = "".join(render_parlay_group(group) for group in parlay["groups"])
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>20260708 淘汰赛预测</title><style>{css()}</style></head>
<body><header><h1>20260708 淘汰赛预测</h1><nav><a href="../index.html">首页</a><a href="../parlay/">串关</a><a href="../knockout/">淘汰赛日历</a></nav></header><main>
<section class="section"><h2>昨日复盘与模型修正</h2><div class="card"><p><strong>{esc(lessons['headline'])}</strong></p><p>{esc(lessons['summary'])}</p><ul>{lesson_items}</ul></div></section>
<section class="section" id="parlay"><h2>二串一 / 三串一</h2><div class="card"><p><strong>{esc(parlay['headline'])}</strong></p><p>{esc(parlay['summary'])}</p><p class="muted">赔率来源：{esc(parlay['odds_source'])}</p></div>{parlay_html}</section>
<section class="section"><h2>今日比赛预测</h2>{''.join(cards)}</section>
</main></body></html>"""


def render_parlay_page(parlay: dict[str, Any]) -> str:
    groups = "".join(render_parlay_group(group) for group in parlay["groups"])
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>未来串关</title><style>{css()}</style></head>
<body><header><h1>未来串关</h1><nav><a href="../index.html">首页</a><a href="../20260708/">07-08预测</a><a href="../knockout/">淘汰赛日历</a></nav></header><main>
<section class="section"><h2>未来串关</h2><div class="card"><p><strong>{esc(parlay['headline'])}</strong></p><p>{esc(parlay['summary'])}</p><p class="muted">赔率来源：{esc(parlay['odds_source'])}</p></div>{groups}</section>
</main></body></html>"""


def patch_home_page() -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace("07-07预测", "07-08预测")
    text = text.replace("葡萄牙 / 西班牙 胜者", "西班牙")
    text = text.replace("美国 / 比利时 胜者", "比利时")
    future_section = (
        '<section class="section" id="future"><h2>未来三天比赛</h2><div class="card tableWrap"><table>'
        '<thead><tr><th>北京时间</th><th>场次</th><th>轮次</th><th>对阵</th><th>下场对手</th></tr></thead><tbody>'
        '<tr><td>07-08 00:00</td><td>95</td><td>16强赛</td><td>阿根廷 vs 埃及</td><td>瑞士 / 哥伦比亚 胜者</td></tr>'
        '<tr><td>07-08 04:00</td><td>96</td><td>16强赛</td><td>瑞士 vs 哥伦比亚</td><td>阿根廷 / 埃及 胜者</td></tr>'
        '<tr><td>07-10 04:00</td><td>97</td><td>四分之一决赛</td><td>法国 vs 摩洛哥</td><td>西班牙 / 比利时 胜者</td></tr>'
        '</tbody></table></div></section>'
    )
    text = re.sub(
        r'<section class="section" id="future">.*?</section>',
        future_section,
        text,
        count=1,
        flags=re.S,
    )
    round16_section = (
        '<section class="section" id="round16"><h2>未来16强赛日程</h2><div class="card tableWrap"><table>'
        '<thead><tr><th>北京时间</th><th>场次</th><th>对阵</th><th>晋级路径</th></tr></thead><tbody>'
        '<tr><td>07-08 00:00</td><td>95</td><td>阿根廷 vs 埃及</td><td>瑞士 / 哥伦比亚 胜者</td></tr>'
        '<tr><td>07-08 04:00</td><td>96</td><td>瑞士 vs 哥伦比亚</td><td>阿根廷 / 埃及 胜者</td></tr>'
        '</tbody></table></div></section>'
    )
    text = re.sub(
        r'<section class="section" id="round16">.*?</section>',
        round16_section,
        text,
        count=1,
        flags=re.S,
    )
    if "葡萄牙 vs 西班牙</td><td><strong>0-1" not in text:
        insert = (
            "<tr><td>07-07</td><td>93</td><td>葡萄牙 vs 西班牙</td><td><strong>0-1</strong></td><td>西班牙胜</td><td>1-2</td><td>方向命中但0-1漏出比分池；强队优势可能到90+1才兑现，低比分正路必须与2球/3球主池并列。</td></tr>"
            "<tr><td>07-07</td><td>94</td><td>美国 vs 比利时</td><td><strong>1-4</strong></td><td>比利时胜</td><td>1-1</td><td>均势保护过重，低估比利时领先后利用美国压上形成的尾部放大；1-3/1-4须进入防大池。</td></tr>"
        )
        teams_match = re.search(r'(<section class="section" id="teams">.*?<tbody>)(.*?)(</tbody></table></div></section>)', text, flags=re.S)
        if teams_match:
            text = text[: teams_match.start(2)] + teams_match.group(2) + insert + text[teams_match.end(2) :]
    text = text.replace(
        "<td>07-11 03:00</td><td>98</td><td>西班牙</td><td>待产生</td><td>比利时</td><td>待产生</td>",
        "<td>07-11 03:00</td><td>98</td><td>西班牙</td><td>已入围</td><td>比利时</td><td>已入围</td>",
    )
    path.write_text(text, encoding="utf-8")


def patch_knockout_archive() -> None:
    path = ROOT / "knockout" / "index.html"
    text = path.read_text(encoding="utf-8")
    if "../20260708/" not in text:
        text = text.replace(
            '<div class="miniGrid">',
            '<div class="miniGrid"><a class="miniCard" href="../20260708/"><strong>20260708</strong><span>阿根廷/瑞士两场</span></a>',
            1,
        )
    path.write_text(text, encoding="utf-8")


def update_schedule_json_and_markdown() -> None:
    path = DATA_DIR / "knockout_schedule.json"
    payload = read_json(path)
    updates = {
        "89": {"home": ("加拿大", "Canada", "CAN"), "away": ("摩洛哥", "Morocco", "MAR"), "status": "已完赛：摩洛哥0-3晋级"},
        "90": {"home": ("巴拉圭", "Paraguay", "PAR"), "away": ("法国", "France", "FRA"), "status": "已完赛：法国0-1晋级"},
        "91": {"home": ("巴西", "Brazil", "BRA"), "away": ("挪威", "Norway", "NOR"), "status": "已完赛：挪威1-2晋级"},
        "92": {"home": ("墨西哥", "Mexico", "MEX"), "away": ("英格兰", "England", "ENG"), "status": "已完赛：英格兰2-3晋级"},
        "93": {"home": ("葡萄牙", "Portugal", "POR"), "away": ("西班牙", "Spain", "ESP"), "status": "已完赛：西班牙0-1晋级"},
        "94": {"home": ("美国", "United States", "USA"), "away": ("比利时", "Belgium", "BEL"), "status": "已完赛：比利时1-4晋级"},
        "95": {"home": ("阿根廷", "Argentina", "ARG"), "away": ("埃及", "Egypt", "EGY"), "status": "未开赛"},
        "96": {"home": ("瑞士", "Switzerland", "SUI"), "away": ("哥伦比亚", "Colombia", "COL"), "status": "未开赛"},
        "97": {"home": ("法国", "France", "FRA"), "away": ("摩洛哥", "Morocco", "MAR"), "status": "未开赛"},
        "98": {"home": ("西班牙", "Spain", "ESP"), "away": ("比利时", "Belgium", "BEL"), "status": "未开赛"},
        "99": {"home": ("挪威", "Norway", "NOR"), "away": ("英格兰", "England", "ENG"), "status": "未开赛"},
    }
    for match in payload.get("matches", []):
        item = updates.get(str(match.get("match_no")))
        if not item:
            continue
        home = item["home"]
        away = item["away"]
        match["home_team"], match["home_team_en"], match["home_code"] = home
        match["away_team"], match["away_team_en"], match["away_code"] = away
        match["status"] = item["status"]
    payload["last_updated"] = "2026-07-07"
    payload["update_note"] = "回填89-94赛果、95-99已确定对阵；100保留95/96胜者待定。"
    write_json(path, payload)

    headers = [
        "比赛ID", "场次编号", "阶段顺序", "轮次", "名义主队中文", "名义主队英文", "主队代码",
        "名义客队中文", "名义客队英文", "客队代码", "当地开球时间", "当地日期", "当地时间",
        "当地时区", "当地UTC偏移", "北京时间", "北京时间日期", "北京开球时间", "北京时间区",
        "北京UTC偏移", "比赛状态", "胜者晋级比赛ID", "备注"
    ]
    key_map = [
        "game_id", "match_no", "stage_order", "round", "home_team", "home_team_en", "home_code",
        "away_team", "away_team_en", "away_code", "kickoff_local", "local_date", "local_time",
        "local_timezone", "local_utc_offset", "kickoff_bjt", "beijing_date", "beijing_time",
        "beijing_timezone", "beijing_utc_offset", "status", "winner_advances_to", "note"
    ]

    def md_cell(value: Any) -> str:
        return str(value if value is not None else "").replace("|", "/")

    lines = [
        "# 2026 美加墨世界杯淘汰赛赛程表（中文版）",
        "> 说明：本表为 Codex 可读取的中文字段版。世界杯淘汰赛为中立场比赛，`名义主队` / `名义客队` 仅表示赛程源中的排列顺序，不代表真正主客场。2026-07-07 已回填 89-94 赛果和 95-99 已确定对阵。",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for match in payload.get("matches", []):
        lines.append("| " + " | ".join(md_cell(match.get(key)) for key in key_map) + " |")
    (ROOT / "2026世界杯淘汰赛赛程表_中文版_Codex.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_model_state() -> None:
    path = ROOT / "model_state.json"
    payload = read_json(path)
    payload["updatedAt"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    payload["calibration"] = {
        "latestReview": "20260707",
        "lesson": "葡萄牙0-1西班牙、美国1-4比利时：0-1和1-4都没有进入比分池，说明比分池既缺低比分末段兑现路径，也缺强客领先后反击放大的尾部路径。",
        "todayAdjustment": "07-08预测不做昨日大小球惯性外推；阿根廷场把2-0/1-0/2-1并列入池，瑞士vs哥伦比亚保留1-1/0-1/1-2，同时把0-2与2-1列为尾部防线。串关降比分权重，主用方向+总进球。",
    }
    payload.setdefault("weights", {})
    payload["weights"]["odds"] = 0.21
    payload["weights"]["elo"] = 0.18
    payload["weights"]["form"] = 0.15
    payload["weights"]["tactics"] = 0.17
    payload["weights"]["motivation"] = 0.16
    payload["weights"]["external"] = 0.09
    payload["weights"]["mystic"] = 0.04
    history_item = {
        "date": "20260707",
        "settled": 2,
        "directionHits": 1,
        "directionHitRate": "50%",
        "mainScoreHits": 0,
        "scorePoolHits": 0,
        "scorePoolHitRate": "0%",
        "totalGoalHits": 1,
        "totalGoalHitRate": "50%",
    }
    history = [item for item in payload.setdefault("history", []) if item.get("date") != "20260707"]
    history.append(history_item)
    payload["history"] = history
    write_json(path, payload)


def main() -> int:
    odds = load_world_cup_odds()
    results = build_results()
    lessons = build_lessons()
    predictions = prediction_payload(odds)
    parlay = build_parlay(predictions)

    write_json(DATA_DIR / "knockout_results_20260707.json", results)
    write_json(DATA_DIR / "model_review_lessons_20260707.json", lessons)
    write_json(DATA_DIR / "knockout_predictions_20260708.json", predictions)
    write_json(DATA_DIR / "round16_parlay_20260708.json", parlay)

    day_dir = ROOT / DATE
    day_dir.mkdir(exist_ok=True)
    page = render_prediction_page(predictions, lessons, parlay)
    (day_dir / "index.html").write_text(page, encoding="utf-8")
    (day_dir / f"predict_{DATE}.html").write_text(page, encoding="utf-8")
    (ROOT / "parlay" / "index.html").write_text(render_parlay_page(parlay), encoding="utf-8")

    patch_home_page()
    patch_knockout_archive()
    update_schedule_json_and_markdown()
    update_model_state()
    print("Updated 20260708 predictions, 20260707 review, parlay page, and model state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
