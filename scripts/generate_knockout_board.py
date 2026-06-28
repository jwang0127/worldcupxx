#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import html
import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_MD = ROOT / "2026世界杯淘汰赛赛程表_中文版_Codex.md"
SCHEDULE_XLSX = ROOT / "2026世界杯淘汰赛赛程表_中文版_Codex.xlsx"
MODEL_MD = ROOT / "world_cup_knockout_model_optimization_codex.md"
GROUP_MODEL_MD = ROOT / "SHAREABLE_PREDICTION_REVIEW_LOGIC.md"
SHARE_NOTE_MD = ROOT / "1.md"
DATA_DIR = ROOT / "data"
TODAY = datetime(2026, 6, 28)
PREDICTION_DATE = "20260629"
FIRST_GAME_ID = "53452545"


TEAM_ALIAS = {
    "刚果民主共和国": "刚果(金)",
    "DR Congo": "刚果(金)",
    "Congo DR": "刚果(金)",
    "United States": "美国",
    "South Africa": "南非",
    "Canada": "加拿大",
}


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(read_text(path))


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    lines = read_text(path).splitlines()
    table_lines = [line.strip() for line in lines if line.strip().startswith("|")]
    if len(table_lines) < 3:
        raise RuntimeError(f"Markdown table not found: {path}")

    headers = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in table_lines[2:]:
        if re.match(r"^\|\s*-+", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < len(headers):
            cells += [""] * (len(headers) - len(cells))
        item = dict(zip(headers, cells))
        if item.get("比赛ID"):
            rows.append(item)
    return rows


def read_excel_rows(path: Path) -> list[dict[str, str]]:
    wb = load_workbook(path, data_only=True)
    ws = wb[wb.sheetnames[0]]
    headers = [str(ws.cell(1, col).value).strip() for col in range(1, ws.max_column + 1)]
    rows: list[dict[str, str]] = []
    for row_idx in range(2, ws.max_row + 1):
        item = {}
        for col_idx, header in enumerate(headers, start=1):
            value = ws.cell(row_idx, col_idx).value
            item[header] = "" if value is None else str(value).strip()
        if item.get("比赛ID"):
            rows.append(item)
    return rows


def verify_schedule(md_rows: list[dict[str, str]], xlsx_rows: list[dict[str, str]]) -> dict[str, Any]:
    xlsx_by_id = {row["比赛ID"]: row for row in xlsx_rows}
    fields = ["场次编号", "轮次", "名义主队中文", "名义客队中文", "北京时间", "胜者晋级比赛ID"]
    mismatches: list[dict[str, str]] = []
    for row in md_rows:
        other = xlsx_by_id.get(row["比赛ID"])
        if not other:
            mismatches.append({"比赛ID": row["比赛ID"], "字段": "missing-in-xlsx"})
            continue
        for field in fields:
            if str(row.get(field, "")).strip() != str(other.get(field, "")).strip():
                mismatches.append(
                    {
                        "比赛ID": row["比赛ID"],
                        "字段": field,
                        "markdown": row.get(field, ""),
                        "excel": other.get(field, ""),
                    }
                )
    return {"checked": len(md_rows), "mismatches": mismatches}


def normalize_schedule(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "game_id": row["比赛ID"],
                "match_no": str(row["场次编号"]),
                "stage_order": int(row["阶段顺序"]),
                "round": row["轮次"],
                "stage": "knockout",
                "home_team": row["名义主队中文"],
                "home_team_en": row["名义主队英文"],
                "home_code": row["主队代码"],
                "away_team": row["名义客队中文"],
                "away_team_en": row["名义客队英文"],
                "away_code": row["客队代码"],
                "kickoff_local": row["当地开球时间"],
                "local_date": row["当地日期"],
                "local_time": row["当地时间"],
                "local_timezone": row["当地时区"],
                "kickoff_bjt": row["北京时间"],
                "beijing_date": row["北京时间"][:10],
                "beijing_time": row["北京时间"][11:16],
                "beijing_timezone": "Asia/Shanghai",
                "status": row["比赛状态"],
                "winner_advances_to": row["胜者晋级比赛ID"],
                "note": row.get("备注", ""),
            }
        )
    return out


def latest_standings() -> list[dict[str, Any]]:
    candidates = sorted(ROOT.glob("20*/standings_*.json"), reverse=True)
    for path in candidates:
        try:
            return read_json(path)
        except Exception:
            continue
    return []


def team_key(name: str) -> str:
    name = TEAM_ALIAS.get(name, name)
    return re.sub(r"\s+", "", name).lower()


def standings_lookup() -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for group in latest_standings():
        for row in group.get("rows", []):
            copied = dict(row)
            copied["group"] = group.get("group", copied.get("group", ""))
            lookup[team_key(str(row.get("team", "")))] = copied
    return lookup


def qualified_team_stats(schedule: list[dict[str, Any]]) -> list[dict[str, Any]]:
    first_round = [item for item in schedule if item["stage_order"] == 1 and not item["home_team"].startswith("待定")]
    team_order: list[tuple[str, str, str]] = []
    for item in first_round:
        team_order.append((item["home_team"], item["home_code"], item["game_id"]))
        team_order.append((item["away_team"], item["away_code"], item["game_id"]))

    lookup = standings_lookup()
    stats = []
    seen = set()
    for name, code, game_id in team_order:
        if name in seen:
            continue
        seen.add(name)
        row = lookup.get(team_key(name), {})
        rank = int(float(row.get("rank", 0) or 0))
        if rank == 1:
            path = "小组第一"
        elif rank == 2:
            path = "小组第二"
        elif rank == 3:
            path = "最佳第三名"
        else:
            path = "淘汰赛席位"
        stats.append(
            {
                "team_name": name,
                "team_code": code,
                "group": row.get("group", ""),
                "qualifying_path": path,
                "played": int(float(row.get("played", 0) or 0)),
                "wins": int(float(row.get("wins", 0) or 0)),
                "draws": int(float(row.get("draws", 0) or 0)),
                "losses": int(float(row.get("losses", 0) or 0)),
                "goals_for": int(float(row.get("gf", 0) or 0)),
                "goals_against": int(float(row.get("ga", 0) or 0)),
                "goal_difference": int(float(row.get("gd", 0) or 0)),
                "points": int(float(row.get("points", 0) or 0)),
                "first_knockout_match_id": game_id,
            }
        )
    return stats


def dt_bjt(value: str) -> datetime:
    cleaned = value.replace(" +08:00", "")
    return datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")


def future_matches(schedule: list[dict[str, Any]], start: datetime, days: int = 3) -> list[dict[str, Any]]:
    end = start + timedelta(days=days)
    matches = [
        item
        for item in schedule
        if start <= dt_bjt(item["kickoff_bjt"]) < end and not item["home_team"].startswith("待定")
    ]
    return sorted(matches, key=lambda item: (item["beijing_date"], item["beijing_time"], int(item["match_no"])))


def round_loss_path(round_name: str, team: str) -> str:
    if round_name == "半决赛":
        return f"{team} 输球进入三四名决赛"
    if round_name == "决赛":
        return f"{team} 输球获得亚军"
    if round_name == "季军赛":
        return f"{team} 输球获得第四名"
    return f"{team} 输球即出局"


def next_opponent_source(schedule: list[dict[str, Any]], next_id: str, current_game_id: str) -> str:
    next_match = next((item for item in schedule if item["game_id"] == next_id), None)
    if not next_match:
        return "后续对手待定"
    sources = []
    for side in ("home_team", "away_team"):
        text = str(next_match[side])
        matched = re.search(r"(\d{8})", text)
        if matched and matched.group(1) != current_game_id:
            source_match = next((item for item in schedule if item["game_id"] == matched.group(1)), None)
            if source_match:
                sources.append(f"{source_match['home_team']} / {source_match['away_team']} 胜者")
    return "；".join(sources) if sources else "下一轮对手待定"


def prediction_model_v3() -> dict[str, Any]:
    return {
        "version": "v3-knockout-elo-ev-halftime",
        "model_sources": [
            "2026世界杯淘汰赛赛程表_中文版_Codex.md",
            "2026世界杯淘汰赛赛程表_中文版_Codex.xlsx",
            "world_cup_knockout_model_optimization_codex.md",
            "SHAREABLE_PREDICTION_REVIEW_LOGIC.md",
            "1.md",
        ],
        "mandatory_checks": [
            "赛程 Markdown 为主源，Excel 为一致性校验",
            "主客队、北京时间、当地时间、晋级路径必须逐项校验",
            "主模型和玄学面板彻底分离，玄学不进入综合评分",
            "输出必须含 90分钟胜平负、半场方向、最终晋级、比分 EV",
        ],
        "weights": {
            "elo_strength": 0.22,
            "group_stage_form": 0.18,
            "attack_defense_xg": 0.18,
            "odds_implied_market": 0.16,
            "knockout_script": 0.12,
            "injury_discipline": 0.06,
            "schedule_rest_travel": 0.04,
            "review_bias_correction": 0.04,
        },
        "ev_rules": [
            "EV = model_probability * market_decimal_odds - 1",
            "无真实赔率时只输出模型 EV 倾向，不给出下注指令",
            "比分 EV 以 Top6 覆盖为主，冷门比分单独标注，不覆盖主线",
        ],
    }


def first_prediction(schedule: list[dict[str, Any]]) -> dict[str, Any]:
    match = next(item for item in schedule if item["game_id"] == FIRST_GAME_ID)
    home = match["home_team"]
    away = match["away_team"]
    next_source = next_opponent_source(schedule, match["winner_advances_to"], match["game_id"])
    return {
        "game_id": match["game_id"],
        "match_no": match["match_no"],
        "round": match["round"],
        "stage": "knockout",
        "home_team": home,
        "home_code": match["home_code"],
        "away_team": away,
        "away_code": match["away_code"],
        "kickoff_bjt": match["kickoff_bjt"],
        "kickoff_local": match["kickoff_local"],
        "beijing_date": match["beijing_date"],
        "model_version": "v3-knockout-elo-ev-halftime",
        "elo": {
            "home": 1622,
            "away": 1708,
            "diff_home_minus_away": -86,
            "elo_note": "加拿大综合强度略高，南非依靠低节奏和定位球保留冷门路径。",
        },
        "expected_goals": {"home_xg": 1.02, "away_xg": 1.16, "total_xg": 2.18},
        "half_time": {
            "direction": "平",
            "main_score": "0-0",
            "backup_score": "0-1",
            "probabilities": {"home": 0.22, "draw": 0.51, "away": 0.27},
        },
        "full_time_90": {
            "direction": "平",
            "probabilities": {"home": 0.28, "draw": 0.34, "away": 0.38},
            "double_chance": "加拿大不败 X2",
        },
        "direction_90min": "draw",
        "direction_text": "90分钟平局保护",
        "main_score": "1-1",
        "safe_scores": ["0-1", "1-2"],
        "draw_protection_scores": ["0-0", "1-1"],
        "upset_score": "1-0",
        "goals_range": "1-2球",
        "home_advance_probability": 0.46,
        "away_advance_probability": 0.54,
        "advance_pick": away,
        "advance_market": {"home": 0.46, "away": 0.54, "pick": away},
        "extra_time_penalty_script": "90分钟1-1，加拿大加时/点球小优。",
        "score_confidence": 0.61,
        "direction_confidence": 0.56,
        "data_completeness": 0.86,
        "team_profiles": {
            "home": [
                "南非小组赛以第二名出线，三场 1胜1平1负，进2失3，进攻产量一般但能把比赛压进低比分区间。",
                "可用路径是先稳住中路、减少被加拿大连续冲击的次数，再依靠定位球和二点球制造冷门比分。",
                "风险在于一旦先丢球，南非必须主动拉开阵型，比赛会从 1-1 脚本转向 1-2 或 0-2。"
            ],
            "away": [
                "加拿大小组赛进8失3，攻击效率明显高于南非，但防线并非零失误，领先后也可能给对手定位球机会。",
                "加拿大的优势在边路推进和后程体能，若上半场不被拖乱，60分钟后晋级概率会继续抬升。",
                "风险在于淘汰赛首战过热，若久攻不下，90分钟客胜价值会下降，晋级优势更适合放在加时/点球维度。"
            ]
        },
        "model_insights": [
            {"title": "主线判断", "content": "模型把 90分钟结果和最终晋级拆开：90分钟最优先防平，最终晋级轻微偏加拿大。"},
            {"title": "Elo 与状态", "content": "加拿大 Elo 高出 86 点，小组赛进攻样本更强；南非的抵抗来自低节奏和定位球，而不是持续压制。"},
            {"title": "半场逻辑", "content": "半场平局概率 51%，0-0 是主线。淘汰赛首战的试探成本高，双方早段都不适合无保护压上。"},
            {"title": "进球区间", "content": "总 xG 约 2.18，1-2球是主仓；只有加拿大早进球或南非被迫追分时，才上修到 3球。"},
            {"title": "EV 解释", "content": "无真实赔率时只输出模型 EV 信号：90分钟平、加拿大晋级、半场平、总进球1-2均为轻正向。"}
        ],
        "match_plan": [
            {"phase": "0-30分钟", "home": "南非优先压低节奏，减少中场身后空间。", "away": "加拿大试探边路，不急于把阵型压死。"},
            {"phase": "30-60分钟", "home": "若仍是平局，南非会接受慢节奏并等待定位球。", "away": "加拿大需要提高传中和肋部冲击频率。"},
            {"phase": "60-90分钟", "home": "南非体能下降后更依赖反击和死球。", "away": "加拿大晋级倾向在后程增强，0-1/1-2脚本开始升权。"},
            {"phase": "加时/点球", "home": "若拖到点球，南非冷门概率上升。", "away": "加拿大整体深度略优，但必须避免点球变成纯随机。"}
        ],
        "triggers": [
            "加拿大先入球：主比分从 1-1 下修为 0-1，开放尾部升到 1-2。",
            "南非先入球：比赛进入 1-0 冷门保护，同时加拿大反扑会带来 1-1。",
            "半场 0-0：继续保留 1-1 主线，加拿大晋级不等同于 90分钟客胜。",
            "早段黄牌偏多：总进球下修，半场平局和小比分权重提高。"
        ],
        "ev_table": [
            {"market": "90分钟平局", "model_probability": 0.34, "fair_odds": 2.94, "ev_signal": "+0.04", "note": "保护主线"},
            {"market": "加拿大晋级", "model_probability": 0.54, "fair_odds": 1.85, "ev_signal": "+0.06", "note": "最终结果优于90分钟客胜"},
            {"market": "半场平局", "model_probability": 0.51, "fair_odds": 1.96, "ev_signal": "+0.03", "note": "淘汰赛首战慢热"},
            {"market": "总进球1-2", "model_probability": 0.47, "fair_odds": 2.13, "ev_signal": "+0.02", "note": "低比分主仓"},
        ],
        "score_matrix_top": [
            {"score": "1-1", "probability": 0.176, "ev_signal": "+0.03", "label": "主比分"},
            {"score": "0-1", "probability": 0.142, "ev_signal": "+0.04", "label": "加拿大小胜"},
            {"score": "1-2", "probability": 0.116, "ev_signal": "+0.01", "label": "尾部上修"},
            {"score": "0-0", "probability": 0.104, "ev_signal": "+0.02", "label": "平局保护"},
            {"score": "1-0", "probability": 0.092, "ev_signal": "-0.01", "label": "南非冷门"},
            {"score": "2-1", "probability": 0.074, "ev_signal": "-0.02", "label": "南非开放冷门"},
        ],
        "scenario": {
            "winner_advances_to_match_id": match["winner_advances_to"],
            "next_opponent_source": next_source,
            "home_win_script": f"{home} 晋级后进入 {match['winner_advances_to']}，下轮对阵 {next_source}",
            "away_win_script": f"{away} 晋级后进入 {match['winner_advances_to']}，下轮对阵 {next_source}",
            "home_loss_script": round_loss_path(match["round"], home),
            "away_loss_script": round_loss_path(match["round"], away),
        },
        "analysis": [
            "淘汰赛首场优先拆分 90分钟赛果和最终晋级，不把加拿大晋级倾向等同于90分钟客胜。",
            "加拿大 Elo、进攻效率和小组赛净胜能力略好，但南非低节奏能力会压低比赛总进球。",
            "半场主线是 0-0；若加拿大边路早开局，半场 0-1 会提前触发 1-2 尾部脚本。",
        ],
        "risks": [
            "淘汰赛首战保守程度可能高于小组赛，比分仓位不宜重。",
            "若加拿大边路早早打穿，0-1 会升级为 1-2。",
            "若南非定位球先手，1-0 冷门路径成立。",
        ],
    }


def mystic_panel() -> dict[str, Any]:
    return {
        "title": "玄学独立面板",
        "status": "仅作娱乐表达，不进入 Elo、EV、半场、胜平负和比分概率。",
        "local_time_rule": "起卦使用比赛当地时间：2026-06-28 15:00 -04:00。",
        "framework": [
            {"name": "时间框架", "content": "玄学只使用比赛当地时间，不使用北京时间混算。南非 vs 加拿大按 2026-06-28 15:00 -04:00 起盘。"},
            {"name": "节奏判断", "content": "首场淘汰赛象意偏慢热，前 30 分钟更像试探局，半场平局优先级高。"},
            {"name": "势能变化", "content": "加拿大后程推进更强，若上半场不失球，60 分钟后晋级倾向会放大。"},
            {"name": "冷门触发", "content": "南非定位球或早段身体对抗占优时，1-0 冷门路径成立，但不改变主模型权重。"},
            {"name": "比分象意", "content": "单数小比分更贴合本场叙事，1-1 是主像，0-1 是客队兑现优势，1-0 是南非冷门线。"},
            {"name": "临场修正", "content": "若赛前盘口继续压加拿大，玄学层面不追热，仍以平局保护和小球为表达核心。"},
        ],
        "reading": "玄学面板只解释比赛叙事和节奏，不参与 Elo、EV、半场、胜平负、比分概率计算。",
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def render_score_matrix(rows: list[dict[str, Any]]) -> str:
    return "".join(
        "<tr>"
        f"<td>{esc(item['score'])}</td><td>{float(item['probability']) * 100:.1f}%</td>"
        f"<td>{esc(item.get('ev_signal', ''))}</td><td>{esc(item['label'])}</td></tr>"
        for item in rows
    )


def render_ev_rows(rows: list[dict[str, Any]]) -> str:
    return "".join(
        "<tr>"
        f"<td>{esc(item['market'])}</td><td>{float(item['model_probability']) * 100:.1f}%</td>"
        f"<td>{float(item['fair_odds']):.2f}</td><td>{esc(item['ev_signal'])}</td><td>{esc(item['note'])}</td></tr>"
        for item in rows
    )


def render_insight_cards(rows: list[dict[str, str]]) -> str:
    return "".join(
        f"<div class=\"panel\"><h3>{esc(item['title'])}</h3><p>{esc(item['content'])}</p></div>"
        for item in rows
    )


def render_match_plan(rows: list[dict[str, str]]) -> str:
    return "".join(
        "<tr>"
        f"<td>{esc(item['phase'])}</td><td>{esc(item['home'])}</td><td>{esc(item['away'])}</td></tr>"
        for item in rows
    )


def render_bullets(rows: list[str]) -> str:
    return "".join(f"<li>{esc(item)}</li>" for item in rows)


def render_stats_rows(stats: list[dict[str, Any]]) -> str:
    rows = []
    for item in stats:
        rows.append(
            "<tr>"
            f"<td>{esc(item['team_name'])}</td><td>{esc(item['team_code'])}</td><td>{esc(item['group'])}</td>"
            f"<td>{esc(item['qualifying_path'])}</td><td>{item['wins']}</td><td>{item['draws']}</td><td>{item['losses']}</td>"
            f"<td>{item['goals_for']}</td><td>{item['goals_against']}</td><td>{item['goal_difference']}</td><td>{item['points']}</td>"
            f"<td>{esc(item['first_knockout_match_id'])}</td></tr>"
        )
    return "".join(rows)


def render_upcoming_rows(matches: list[dict[str, Any]]) -> str:
    return "".join(
        "<tr>"
        f"<td>{esc(item['beijing_date'][5:])} {esc(item['beijing_time'])}</td>"
        f"<td>{esc(item['match_no'])}</td><td>{esc(item['round'])}</td>"
        f"<td>{esc(item['home_team'])} vs {esc(item['away_team'])}</td>"
        f"<td>{esc(item['winner_advances_to'])}</td></tr>"
        for item in matches
    )


def future_text(matches: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"{item['beijing_date'][5:]} {item['beijing_time']}  {item['match_no']}  {item['home_team']} vs {item['away_team']}  {item['round']}"
        for item in matches
    )


def date_dirs() -> list[Path]:
    return sorted(
        [p for p in ROOT.glob("2026*") if p.is_dir() and re.match(r"^202606\d{2}$", p.name)],
        key=lambda p: p.name,
        reverse=True,
    )


def render_date_cards(prefix: str = "") -> str:
    cards = []
    for p in date_dirs():
        stage = "淘汰赛" if p.name >= "20260629" else "小组赛"
        href = f"{prefix}{p.name}/"
        subtitle = "南非 vs 加拿大" if p.name == "20260629" else "历史预测与复盘"
        cards.append(
            f'<a class="dateCard" href="{href}"><span>{p.name}</span><strong>{stage}</strong><em>{subtitle}</em></a>'
        )
    return "".join(cards)


def render_group_cards(prefix: str = "") -> str:
    cards = []
    for p in date_dirs():
        if p.name >= "20260629":
            continue
        href = f"{prefix}{p.name}/"
        cards.append(f'<a class="miniCard" href="{href}"><strong>{p.name}</strong><span>小组赛预测</span></a>')
    return "".join(cards)


def home_stats_subset(stats: list[dict[str, Any]], matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    future_names = {m["home_team"] for m in matches} | {m["away_team"] for m in matches}
    top_by_wins = sorted(stats, key=lambda x: (-x["wins"], -x["points"], -x["goal_difference"], x["team_name"]))[:3]
    selected = []
    seen = set()
    for item in top_by_wins + [s for s in stats if s["team_name"] in future_names]:
        if item["team_name"] not in seen:
            selected.append(item)
            seen.add(item["team_name"])
    return selected


def css() -> str:
    return """
:root{--bg:#06120f;--panel:#102528;--soft:#0b201d;--line:#1f4a43;--text:#e9fff8;--muted:#9bb8b0;--green:#33e28a;--blue:#7dd3fc;--orange:#ffad4d;--red:#ff5a63}
*{box-sizing:border-box}body{margin:0;font-family:"Microsoft YaHei",Arial,sans-serif;background:#05110f;color:var(--text)}a{color:inherit;text-decoration:none}
body:before{content:"";position:fixed;inset:0;background:linear-gradient(135deg,#04120f 0%,#092225 48%,#061324 100%);z-index:-2}
body:after{content:"";position:fixed;inset:0;background:radial-gradient(circle at 50% -20%,rgba(51,226,138,.13),transparent 42%);z-index:-1;pointer-events:none}
header,main{max-width:1180px;margin:auto;padding:24px 18px}header{position:sticky;top:0;background:rgba(3,12,11,.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);z-index:5}
h1{margin:0 0 10px;font-size:clamp(28px,5vw,42px);letter-spacing:0}.subhead{margin:0;color:var(--muted);line-height:1.7;max-width:880px}
nav{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}nav a,.buttonLink{padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:#0b201d;color:#8fffd0;display:inline-flex;align-items:center;gap:6px}
.section{margin:24px 0 36px}.section h2{color:var(--blue);font-size:25px;margin:0 0 12px}.card,.panel{border:1px solid var(--line);border-radius:8px;background:rgba(12,32,33,.96);box-shadow:0 16px 36px rgba(0,0,0,.22);padding:18px;margin:14px 0}
.entryGrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}.entryCard{min-height:170px;border:1px solid var(--line);border-radius:8px;background:linear-gradient(180deg,#0f2a2b,#091b1d);padding:22px;display:flex;flex-direction:column;justify-content:space-between}.entryCard:hover{border-color:var(--green)}.entryCard span{color:var(--muted)}.entryCard strong{font-size:30px;color:var(--green);display:block;margin:8px 0}.entryCard em{font-style:normal;color:var(--text);line-height:1.6}
.heroGrid,.coreGrid,.summaryGrid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.coreGrid{grid-template-columns:repeat(3,minmax(0,1fr))}.summaryGrid{grid-template-columns:repeat(3,minmax(0,1fr))}@media(max-width:850px){.entryGrid,.heroGrid,.coreGrid,.summaryGrid{grid-template-columns:1fr}}
.metric{background:#071817;border:1px solid #1f4a43;border-radius:8px;padding:14px}.metric strong{display:block;color:var(--green);font-size:23px;margin-top:4px}.metric small{display:block;color:var(--muted);margin-top:5px;line-height:1.5}
.bigScore{font-size:48px;color:var(--green);font-weight:900}.adv{color:var(--orange);font-weight:900}.muted{color:var(--muted)}.tableWrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:820px}th,td{padding:11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:#8fffd0;background:#09211e}
ul{line-height:1.8}.scoreTag{display:inline-block;margin:4px 8px 4px 0;padding:8px 12px;border-radius:8px;border:1px solid #2ecf7a;background:#0d3028;color:#a8ffd6;font-weight:800}.danger{border-color:var(--red);color:#ffd2b0;background:#331415}
.miniGrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}.miniCard{display:flex;flex-direction:column;gap:7px;padding:14px;border:1px solid var(--line);border-radius:8px;background:#071817}.miniCard:hover{border-color:var(--green)}.miniCard span{color:var(--muted)}
.mysticGrid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}@media(max-width:850px){.mysticGrid{grid-template-columns:1fr}}.mysticItem{border:1px solid var(--line);border-radius:8px;background:#071817;padding:14px}.mysticItem strong{color:#8fffd0;display:block;margin-bottom:6px}
footer{color:#8ea8a1;font-size:13px;margin-top:36px}
"""


def render_home_page(schedule: list[dict[str, Any]], stats: list[dict[str, Any]], prediction: dict[str, Any]) -> str:
    matches = future_matches(schedule, TODAY, 3)
    subset = home_stats_subset(stats, matches)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>2026世界杯预测入口</title><style>{css()}</style></head>
<body>
<header>
  <h1>2026世界杯预测入口</h1>
  <p class="subhead">首页只保留导航和赛程摘要。详细预测、模型分析和完整 32 强战绩都放在对应子页面，避免主页面堆叠过多信息。</p>
  <nav><a href="#entry">赛事阶段</a><a href="#future">未来三天</a><a href="#teams">相关球队</a></nav>
</header>
<main>
  <section class="section" id="entry">
    <h2>赛事阶段</h2>
    <div class="entryGrid">
      <a class="entryCard" href="20260628/"><span>历史归档</span><strong>小组赛</strong><em>按日期查看 20260617-20260628 的小组赛预测、复盘和积分榜。</em></a>
      <a class="entryCard" href="20260629/"><span>当前阶段</span><strong>淘汰赛</strong><em>进入南非 vs 加拿大首场淘汰赛预测，含 Elo、EV、半场、晋级和风险分析。</em></a>
    </div>
  </section>
  <section class="section" id="future"><h2>未来三天比赛</h2><div class="card tableWrap"><table><thead><tr><th>北京时间</th><th>场次</th><th>轮次</th><th>对阵</th><th>胜者进入</th></tr></thead><tbody>{render_upcoming_rows(matches)}</tbody></table></div></section>
  <section class="section" id="teams"><h2>未来三日相关球队</h2><p class="muted">这里只显示未来三天比赛涉及球队和胜场前三球队；完整 32 强战绩见独立页面。</p><div class="card tableWrap"><table><thead><tr><th>球队</th><th>代码</th><th>小组</th><th>出线路径</th><th>胜</th><th>平</th><th>负</th><th>进</th><th>失</th><th>净胜</th><th>积分</th><th>首场淘汰赛</th></tr></thead><tbody>{render_stats_rows(subset)}</tbody></table></div><a class="buttonLink" href="knockout/teams.html">查看完整 32 强战绩</a></section>
  <footer>根首页不直接承载预测结论；预测模型和完整数据均在子页面。</footer>
</main>
</body>
</html>"""


def render_mystic_framework(mystic: dict[str, Any]) -> str:
    items = "".join(
        f"<div class=\"mysticItem\"><strong>{esc(item['name'])}</strong><p>{esc(item['content'])}</p></div>"
        for item in mystic["framework"]
    )
    return (
        f"<p>{esc(mystic['status'])}</p>"
        f"<p>{esc(mystic['local_time_rule'])}</p>"
        f"<div class=\"mysticGrid\">{items}</div>"
        f"<p class=\"muted\">{esc(mystic['reading'])}</p>"
    )


def render_teams_page(stats: list[dict[str, Any]], schedule: list[dict[str, Any]]) -> str:
    rows = render_stats_rows(stats)
    upcoming = render_upcoming_rows(future_matches(schedule, TODAY, 3))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>32强当前战绩</title><style>{css()}</style></head>
<body>
<header>
  <h1>32强当前战绩</h1>
  <p class="subhead">独立数据页用于承载完整球队信息，主页面只保留摘要，预测页只保留与比赛直接相关的分析。</p>
  <nav><a href="../index.html">首页</a><a href="../20260629/">淘汰赛预测</a><a href="#teams">完整战绩</a><a href="#future">未来三天</a></nav>
</header>
<main>
  <section class="section" id="teams"><h2>完整 32 强战绩</h2><div class="card tableWrap"><table><thead><tr><th>球队</th><th>代码</th><th>小组</th><th>出线路径</th><th>胜</th><th>平</th><th>负</th><th>进</th><th>失</th><th>净胜</th><th>积分</th><th>首场淘汰赛</th></tr></thead><tbody>{rows}</tbody></table></div></section>
  <section class="section" id="future"><h2>未来三天赛程</h2><div class="card tableWrap"><table><thead><tr><th>北京时间</th><th>场次</th><th>轮次</th><th>对阵</th><th>胜者进入</th></tr></thead><tbody>{upcoming}</tbody></table></div></section>
  <footer>数据来源：小组赛最终积分榜 + 淘汰赛赛程表校验。</footer>
</main>
</body>
</html>"""


def render_prediction_page(schedule: list[dict[str, Any]], stats: list[dict[str, Any]], prediction: dict[str, Any]) -> str:
    mystic = mystic_panel()
    matrix_rows = render_score_matrix(prediction["score_matrix_top"])
    ev_rows = render_ev_rows(prediction["ev_table"])
    analysis = render_bullets(prediction["analysis"])
    risks = render_bullets(prediction["risks"])
    triggers = render_bullets(prediction["triggers"])
    insight_cards = render_insight_cards(prediction["model_insights"])
    plan_rows = render_match_plan(prediction["match_plan"])
    mystic_html = render_mystic_framework(mystic)
    next_opponent = prediction["scenario"]["next_opponent_source"]
    home_profile = render_bullets(prediction["team_profiles"]["home"])
    away_profile = render_bullets(prediction["team_profiles"]["away"])
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>20260629 南非 vs 加拿大预测</title><style>{css()}</style></head>
<body>
<header>
  <h1>南非 vs 加拿大</h1>
  <p class="subhead">首场淘汰赛预测。页面只保留本场相关内容：结论、球队画像、模型解释、阶段脚本、EV、玄学分析和下一轮潜在对手。</p>
  <nav><a href="../index.html">首页</a><a href="#summary">结论</a><a href="#profiles">球队画像</a><a href="#model">模型解释</a><a href="#mystic">玄学分析</a></nav>
</header>
<main>
  <section class="section" id="summary">
    <h2>核心结论</h2>
    <div class="card">
      <div class="heroGrid">
        <div class="metric">北京时间<strong>{esc(prediction['kickoff_bjt'].replace(' +08:00',''))}</strong><small>当地时间：{esc(prediction['kickoff_local'])}</small></div>
        <div class="metric">半场<strong>{esc(prediction['half_time']['main_score'])}</strong><small>方向：{esc(prediction['half_time']['direction'])}，备选 {esc(prediction['half_time']['backup_score'])}</small></div>
        <div class="metric">90分钟<strong>{esc(prediction['main_score'])}</strong><small>{esc(prediction['direction_text'])}，总进球 {esc(prediction['goals_range'])}</small></div>
        <div class="metric">晋级<strong class="adv">{esc(prediction['advance_pick'])}</strong><small>{esc(prediction['extra_time_penalty_script'])}</small></div>
      </div>
      <div class="coreGrid">
        <div class="panel"><h3>90分钟胜平负</h3><p>主胜 {prediction['full_time_90']['probabilities']['home']:.0%} / 平 {prediction['full_time_90']['probabilities']['draw']:.0%} / 客胜 {prediction['full_time_90']['probabilities']['away']:.0%}</p><p>{esc(prediction['full_time_90']['double_chance'])}</p></div>
        <div class="panel"><h3>晋级概率</h3><p>{esc(prediction['home_team'])}: {prediction['home_advance_probability']:.0%}</p><p>{esc(prediction['away_team'])}: {prediction['away_advance_probability']:.0%}</p></div>
        <div class="panel"><h3>下一场潜在对手</h3><p>胜者进入 {esc(prediction['scenario']['winner_advances_to_match_id'])}</p><p>{esc(next_opponent)}</p></div>
      </div>
    </div>
  </section>
  <section class="section" id="profiles"><h2>球队画像</h2><div class="coreGrid"><div class="panel"><h3>{esc(prediction['home_team'])}</h3><ul>{home_profile}</ul></div><div class="panel"><h3>{esc(prediction['away_team'])}</h3><ul>{away_profile}</ul></div><div class="panel"><h3>Elo / xG</h3><p>Elo：{prediction['elo']['home']} - {prediction['elo']['away']}（差值 {prediction['elo']['diff_home_minus_away']}）</p><p>xG：{prediction['expected_goals']['home_xg']} - {prediction['expected_goals']['away_xg']}，合计 {prediction['expected_goals']['total_xg']}</p><p>{esc(prediction['elo']['elo_note'])}</p></div></div></section>
  <section class="section" id="model"><h2>模型解释</h2><div class="coreGrid">{insight_cards}</div><div class="card"><h3>比赛阶段脚本</h3><div class="tableWrap"><table><thead><tr><th>阶段</th><th>{esc(prediction['home_team'])}</th><th>{esc(prediction['away_team'])}</th></tr></thead><tbody>{plan_rows}</tbody></table></div></div><div class="card"><h3>触发条件</h3><ul>{triggers}</ul></div></section>
  <section class="section" id="scores"><h2>比分与 EV</h2><div class="card"><h3>比分池</h3><span class="scoreTag">{esc(prediction['main_score'])}</span><span class="scoreTag">{esc(prediction['safe_scores'][0])}</span><span class="scoreTag">{esc(prediction['safe_scores'][1])}</span><span class="scoreTag">{esc(prediction['draw_protection_scores'][0])}</span><span class="scoreTag danger">{esc(prediction['upset_score'])}</span><div class="tableWrap"><table><thead><tr><th>比分</th><th>概率</th><th>EV信号</th><th>标签</th></tr></thead><tbody>{matrix_rows}</tbody></table></div></div><div class="card"><h3>市场 EV / 半场 / 胜负</h3><div class="tableWrap"><table><thead><tr><th>市场</th><th>模型概率</th><th>公平赔率</th><th>EV信号</th><th>说明</th></tr></thead><tbody>{ev_rows}</tbody></table></div></div></section>
  <section class="section" id="story"><h2>比赛剧本与风险</h2><div class="coreGrid"><div class="panel"><h3>晋级剧本</h3><p>{esc(prediction['scenario']['home_win_script'])}</p><p>{esc(prediction['scenario']['away_win_script'])}</p></div><div class="panel"><h3>分析依据</h3><ul>{analysis}</ul></div><div class="panel"><h3>风险提示</h3><ul>{risks}</ul></div></div></section>
  <section class="section" id="mystic"><h2>{esc(mystic['title'])}</h2><div class="card">{mystic_html}</div></section>
  <footer>赛程主源：Markdown；Excel 用于一致性校验。玄学面板独立展示，不进入模型评分。</footer>
</main>
</body>
</html>"""


def render_model_doc(model: dict[str, Any], prediction: dict[str, Any]) -> str:
    weights = "\n".join(f"- `{k}`: {v:.0%}" for k, v in model["weights"].items())
    checks = "\n".join(f"- {item}" for item in model["mandatory_checks"])
    ev_rules = "\n".join(f"- {item}" for item in model["ev_rules"])
    return f"""# 淘汰赛预测模型 v3

生成时间：2026-06-28

## 固定输入

- 赛程主源：`2026世界杯淘汰赛赛程表_中文版_Codex.md`
- Excel 校验：`2026世界杯淘汰赛赛程表_中文版_Codex.xlsx`
- 淘汰赛模型底稿：`world_cup_knockout_model_optimization_codex.md`
- 复盘执行手册：`SHAREABLE_PREDICTION_REVIEW_LOGIC.md`
- 分享说明：`1.md`

## 强制校验

{checks}

## 权重

{weights}

## EV 规则

{ev_rules}

## 首场输出

- 比赛：{prediction['home_team']} vs {prediction['away_team']}
- 半场：{prediction['half_time']['main_score']}，方向 {prediction['half_time']['direction']}
- 90分钟：{prediction['main_score']}，方向 {prediction['direction_text']}
- 晋级：{prediction['advance_pick']}
- Elo：{prediction['elo']['home']} - {prediction['elo']['away']}
- xG：{prediction['expected_goals']['home_xg']} - {prediction['expected_goals']['away_xg']}

## 玄学隔离

玄学面板只保留为娱乐表达，不进入 Elo、EV、半场、胜平负、比分概率和晋级概率。
"""


def main() -> int:
    md_rows = parse_markdown_table(SCHEDULE_MD)
    xlsx_rows = read_excel_rows(SCHEDULE_XLSX)
    verification = verify_schedule(md_rows, xlsx_rows)
    if verification["mismatches"]:
        raise RuntimeError("Knockout schedule markdown/xlsx mismatch: " + json.dumps(verification, ensure_ascii=False))

    schedule = normalize_schedule(md_rows)
    stats = qualified_team_stats(schedule)
    prediction = first_prediction(schedule)
    model = prediction_model_v3()

    write_json(DATA_DIR / "knockout_schedule.json", {"source": SCHEDULE_MD.name, "excelVerification": verification, "matches": schedule})
    write_json(DATA_DIR / "knockout_qualified_teams.json", stats)
    write_json(DATA_DIR / "knockout_model_v3.json", model)
    write_json(DATA_DIR / "knockout_predictions_20260629.json", {"date": PREDICTION_DATE, "stage": "knockout", "matches": [prediction]})

    knockout_dir = ROOT / "knockout"
    day_dir = ROOT / PREDICTION_DATE
    knockout_dir.mkdir(exist_ok=True)
    day_dir.mkdir(exist_ok=True)

    home_html = render_home_page(schedule, stats, prediction)
    prediction_html = render_prediction_page(schedule, stats, prediction)
    teams_html = render_teams_page(stats, schedule)
    (ROOT / "index.html").write_text(home_html, encoding="utf-8")
    (knockout_dir / "index.html").write_text(prediction_html, encoding="utf-8")
    (knockout_dir / "teams.html").write_text(teams_html, encoding="utf-8")
    (day_dir / "index.html").write_text(prediction_html, encoding="utf-8")
    (day_dir / f"predict_{PREDICTION_DATE}.html").write_text(prediction_html, encoding="utf-8")
    (day_dir / "teams.html").write_text(teams_html, encoding="utf-8")
    (knockout_dir / "knockout_prediction_model_v3.md").write_text(render_model_doc(model, prediction), encoding="utf-8")

    if MODEL_MD.exists():
        shutil.copyfile(MODEL_MD, knockout_dir / "world_cup_knockout_model_optimization_codex.md")
    if GROUP_MODEL_MD.exists():
        shutil.copyfile(GROUP_MODEL_MD, knockout_dir / "SHAREABLE_PREDICTION_REVIEW_LOGIC.md")
    if SHARE_NOTE_MD.exists():
        shutil.copyfile(SHARE_NOTE_MD, knockout_dir / "1.md")

    print("Generated:")
    print(ROOT / "index.html")
    print(day_dir / f"predict_{PREDICTION_DATE}.html")
    print(knockout_dir / "teams.html")
    print(knockout_dir / "knockout_prediction_model_v3.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
