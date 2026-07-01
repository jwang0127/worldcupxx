#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DAY = ROOT / "20260702"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def odds_for(match: dict[str, Any], market: str, key: str) -> str:
    value = ((match.get("odds") or {}).get(market) or {}).get(key)
    return "-" if value in (None, "") else str(value)


def odds_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_odds(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"


def score_total(score: str) -> int | None:
    left, sep, right = str(score).partition("-")
    if not sep:
        left, sep, right = str(score).partition(":")
    if not sep:
        return None
    try:
        return int(left.strip()) + int(right.strip())
    except ValueError:
        return None


def product_odds(rows: list[dict[str, Any]]) -> float | None:
    product = 1.0
    for row in rows:
        odd = row.get("odds")
        if odd is None:
            return None
        product *= float(odd)
    return product


def half_result_label(direction: str) -> str:
    return {"home": "半场主胜", "draw": "半场平", "away": "半场客胜"}.get(direction, direction)


def half_result_implied_odds(match: dict[str, Any], half_direction: str) -> float | None:
    hafu = ((match.get("odds") or {}).get("hafu") or {})
    prefix = {"home": "h", "draw": "d", "away": "a"}.get(half_direction, "d")
    implied_probability = 0.0
    for suffix in ("h", "d", "a"):
        odd = odds_float(hafu.get(prefix + suffix))
        if odd and odd > 0:
            implied_probability += 1 / odd
    if implied_probability <= 0:
        return None
    return 1 / implied_probability


def refreshed_odds_by_no() -> dict[str, dict[str, Any]]:
    payload = read_json(DATA / "20260702.json")
    return {str(item["id"]).lstrip("0"): item for item in payload.get("matches", [])}


def result_payload() -> dict[str, Any]:
    return {
        "date": "20260701",
        "stage": "knockout",
        "status": "90min_finished",
        "matches": [
            {
                "game_id": "53452561",
                "match_no": "77",
                "home_team": "科特迪瓦",
                "away_team": "挪威",
                "score": "1-2",
                "home_goals": 1,
                "away_goals": 2,
                "prediction_main_score": "1-1",
                "prediction_backup_scores": ["1-2", "0-1"],
                "review": "方向命中挪威晋级，小胜比分在保护池内；模型对90分钟平局权重略重，强队临门终结权重需要上调。",
            },
            {
                "game_id": "53452543",
                "match_no": "78",
                "home_team": "法国",
                "away_team": "瑞典",
                "score": "3-0",
                "home_goals": 3,
                "away_goals": 0,
                "prediction_main_score": "2-1",
                "prediction_backup_scores": ["1-0", "1-1"],
                "review": "方向命中但低估法国拉开比分能力；强队早段领先后，大球和零封穿盘权重需要提高。",
            },
            {
                "game_id": "53452563",
                "match_no": "79",
                "home_team": "墨西哥",
                "away_team": "厄瓜多尔",
                "score": "2-0",
                "home_goals": 2,
                "away_goals": 0,
                "prediction_main_score": "1-1",
                "prediction_backup_scores": ["0-1", "1-0"],
                "review": "低比分判断接近，但主场强队控制力被低估；窄差对抗里仍要保留主队2-0/2-1拉开线。",
            },
        ],
    }


def lessons_payload() -> dict[str, Any]:
    return {
        "date": "20260701",
        "headline": "7月1日三场复盘：强队正路和大球权重上调，平局保护降一档。",
        "summary": "挪威1-2、法国3-0、墨西哥2-0验证了淘汰赛强队只要先打开局面，比分会从小胜扩展到2-3球区间；但挪威小胜也说明冷门/反击线不能删除，只是不能把平局放得过重。",
        "lessons": [
            "强队赔率低于1.30且总进球3球赔率接近2球时，主比分优先给2-0、3-0、3-1，而不是默认1球小胜。",
            "强队早进球触发大球上修：半场领先时，3球和4球比分池同步升权。",
            "中等优势队仍需冷门保护：比利时-塞内加尔这类2.00附近主胜盘，平局和客队反击比分必须保留。",
            "昨日两个零封提示：面对终结效率偏弱的下风方，强队零封概率上调，但非洲球队身体反击场景仍作为冷门触发条件。",
        ],
        "weight_adjustment": {
            "favorite_big_win": "+0.06",
            "draw_protection": "-0.04",
            "underdog_counter_upset": "+0.03",
            "clean_sheet_for_elite_favorite": "+0.03",
        },
    }


def prediction_payload() -> dict[str, Any]:
    odds = refreshed_odds_by_no()
    matches = [
        {
            "game_id": "53452565",
            "match_no": "80",
            "round": "32强赛",
            "home_team": "英格兰",
            "away_team": "刚果(金)",
            "kickoff_bjt": "2026-07-02 00:00:00 +08:00",
            "model_version": "v4-knockout-review-big-goals",
            "direction_text": "英格兰90分钟胜",
            "half_time_pick": "home",
            "main_score": "3-0",
            "backup_scores": ["2-0", "3-1"],
            "upset_score": "1-1",
            "goals_range": "2-4球",
            "advance_pick": "英格兰",
            "advance_probability_text": "英格兰 73% / 刚果(金) 27%",
            "core_view": "英格兰纸面强度、阵容深度和定位球质量都占优；昨日法国3-0提醒模型不要把顶级强队机械压成小胜。冷门只来自刚果(金)前30分钟守住后，用身体对抗和反击制造一次高质量机会。",
            "score_matrix_top": [
                {"score": "3-0", "probability": 0.156, "ev_signal": "+0.05", "label": "主比分"},
                {"score": "2-0", "probability": 0.148, "ev_signal": "+0.04", "label": "稳胜零封"},
                {"score": "2-1", "probability": 0.112, "ev_signal": "+0.02", "label": "刚果反击进球"},
                {"score": "3-1", "probability": 0.098, "ev_signal": "+0.02", "label": "大球上修"},
                {"score": "1-1", "probability": 0.073, "ev_signal": "-0.01", "label": "冷门拖住"},
                {"score": "4-0", "probability": 0.061, "ev_signal": "-0.01", "label": "早球放大"},
            ],
            "ev_table": [
                {"market": "英格兰90分钟胜", "model_probability": 0.68, "fair_odds": 1.47, "ev_signal": "+0.04", "note": "正路明确，但不追极端穿盘"},
                {"market": "总进球3+", "model_probability": 0.55, "fair_odds": 1.82, "ev_signal": "+0.05", "note": "2球与3球赔率接近，强队上调大球"},
                {"market": "英格兰零封", "model_probability": 0.49, "fair_odds": 2.04, "ev_signal": "+0.03", "note": "昨日法国/墨西哥零封后升权"},
                {"market": "冷门平局", "model_probability": 0.18, "fair_odds": 5.56, "ev_signal": "保护", "note": "半场0-0时再上修"},
            ],
            "triggers": [
                "英格兰30分钟内进球：3-0、4-0、3-1升权，大球优先。",
                "半场0-0：2-0降为主线，1-1冷门保护升权。",
                "刚果(金)连续制造反击或定位球：2-1、1-1同步升权。",
            ],
            "team_reading": [
                "英格兰适合用边路和定位球压制，领先后替补深度能继续放大比分。",
                "刚果(金)的冷门路径不是控场，而是低位抗住后打转换和二点球。",
            ],
            "odds_snapshot": odds.get("80", {}),
        },
        {
            "game_id": "53452555",
            "match_no": "81",
            "round": "32强赛",
            "home_team": "比利时",
            "away_team": "塞内加尔",
            "kickoff_bjt": "2026-07-02 04:00:00 +08:00",
            "model_version": "v4-knockout-review-big-goals",
            "direction_text": "比利时小胜，防平/防客胜",
            "half_time_pick": "draw",
            "main_score": "2-1",
            "backup_scores": ["1-1", "1-2"],
            "upset_score": "0-1",
            "goals_range": "2-3球",
            "advance_pick": "比利时",
            "advance_probability_text": "比利时 54% / 塞内加尔 46%",
            "core_view": "这场不是纯强弱盘，主胜接近2.00且比分赔率1-1最低，说明市场对塞内加尔抗衡很重视。昨日强队拉开比分让2-1成为主线，但冷门保护不能降太多。",
            "score_matrix_top": [
                {"score": "2-1", "probability": 0.151, "ev_signal": "+0.04", "label": "主比分"},
                {"score": "1-1", "probability": 0.143, "ev_signal": "+0.04", "label": "最高保护"},
                {"score": "1-2", "probability": 0.096, "ev_signal": "+0.02", "label": "塞内加尔反击冷门"},
                {"score": "1-0", "probability": 0.088, "ev_signal": "+0.01", "label": "比利时小胜"},
                {"score": "2-2", "probability": 0.074, "ev_signal": "-0.01", "label": "大球平局"},
                {"score": "0-1", "probability": 0.069, "ev_signal": "保护", "label": "低比分冷门"},
            ],
            "ev_table": [
                {"market": "双方进球", "model_probability": 0.57, "fair_odds": 1.75, "ev_signal": "+0.05", "note": "2-1/1-1/1-2共同指向"},
                {"market": "总进球2-3", "model_probability": 0.62, "fair_odds": 1.61, "ev_signal": "+0.04", "note": "不追4球以上"},
                {"market": "比利时晋级", "model_probability": 0.54, "fair_odds": 1.85, "ev_signal": "+0.02", "note": "90分钟优势有限"},
                {"market": "塞内加尔不败保护", "model_probability": 0.39, "fair_odds": 2.56, "ev_signal": "冷门", "note": "非洲身体对抗和转换是核心风险"},
            ],
            "triggers": [
                "比利时先入球：2-1/2-0升权，但塞内加尔追平能力仍保留。",
                "半场0-0：1-1成为主线，0-1冷门保护升权。",
                "塞内加尔边路冲击持续成功：1-2和2-2升权。",
            ],
            "team_reading": [
                "比利时控球和中前场经验更好，但防线回追速度是风险点。",
                "塞内加尔适合打强度和纵深，若先手进球，比赛会快速转向冷门脚本。",
            ],
            "odds_snapshot": odds.get("81", {}),
        },
        {
            "game_id": "53452553",
            "match_no": "82",
            "round": "32强赛",
            "home_team": "美国",
            "away_team": "波黑",
            "kickoff_bjt": "2026-07-02 08:00:00 +08:00",
            "model_version": "v4-knockout-review-big-goals",
            "direction_text": "美国90分钟胜",
            "half_time_pick": "home",
            "main_score": "3-1",
            "backup_scores": ["2-0", "2-1"],
            "upset_score": "1-1",
            "goals_range": "3-4球",
            "advance_pick": "美国",
            "advance_probability_text": "美国 67% / 波黑 33%",
            "core_view": "美国主场气质和进攻速度明显占优，竞彩总进球3球赔率最低，且昨日强队零封/大比分给了上修依据。波黑的冷门路径主要是定位球或美国压上后的身后球。",
            "score_matrix_top": [
                {"score": "3-1", "probability": 0.145, "ev_signal": "+0.05", "label": "主比分"},
                {"score": "2-1", "probability": 0.132, "ev_signal": "+0.04", "label": "稳胜"},
                {"score": "2-0", "probability": 0.121, "ev_signal": "+0.03", "label": "零封线"},
                {"score": "3-0", "probability": 0.104, "ev_signal": "+0.02", "label": "强队放大"},
                {"score": "1-1", "probability": 0.071, "ev_signal": "保护", "label": "冷门平局"},
                {"score": "2-2", "probability": 0.058, "ev_signal": "-0.01", "label": "大球冷门"},
            ],
            "ev_table": [
                {"market": "美国90分钟胜", "model_probability": 0.63, "fair_odds": 1.59, "ev_signal": "+0.04", "note": "正路优先"},
                {"market": "总进球3+", "model_probability": 0.59, "fair_odds": 1.69, "ev_signal": "+0.06", "note": "今日大球最清晰的一场"},
                {"market": "美国-1方向", "model_probability": 0.48, "fair_odds": 2.08, "ev_signal": "+0.03", "note": "2-0/3-1/3-0覆盖"},
                {"market": "波黑进球", "model_probability": 0.43, "fair_odds": 2.33, "ev_signal": "保护", "note": "定位球风险不可删"},
            ],
            "triggers": [
                "美国先入球：3-1、3-0、4-1升权，大球优先。",
                "波黑先入球：2-1/2-2升权，美国胜仍保留但穿盘降权。",
                "半场0-0：2-0/1-0升权，3-1降为次线。",
            ],
            "team_reading": [
                "美国速度和主场环境优势明显，适合把比赛推到3球区间。",
                "波黑身体和定位球有破门点，但持续抵抗美国边路冲击难度较高。",
            ],
            "odds_snapshot": odds.get("82", {}),
        },
    ]
    return {
        "date": "20260702",
        "stage": "knockout",
        "source": "manual-review-plus-sporttery-odds",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "review_basis": "昨日赛果：科特迪瓦1-2挪威、法国3-0瑞典、墨西哥2-0厄瓜多尔。",
        "matches": matches,
    }


CSS = """
:root{--bg:#06120f;--panel:#102528;--soft:#0b201d;--line:#1f4a43;--text:#e9fff8;--muted:#9bb8b0;--green:#33e28a;--blue:#7dd3fc;--orange:#ffad4d;--red:#ff5a63}
*{box-sizing:border-box}body{margin:0;font-family:"Microsoft YaHei",Arial,sans-serif;background:#05110f;color:var(--text)}a{color:inherit;text-decoration:none}
body:before{content:"";position:fixed;inset:0;background:linear-gradient(135deg,#04120f 0%,#092225 48%,#061324 100%);z-index:-2}
header,main{max-width:1180px;margin:auto;padding:24px 18px}header{position:sticky;top:0;background:rgba(3,12,11,.92);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);z-index:5}
h1{margin:0 0 10px;font-size:clamp(28px,5vw,42px);letter-spacing:0}nav{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}nav a,.buttonLink{padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:#0b201d;color:#8fffd0}
.section{margin:24px 0 36px}.section h2{color:var(--blue);font-size:25px;margin:0 0 12px}.card,.panel{border:1px solid var(--line);border-radius:8px;background:rgba(12,32,33,.96);box-shadow:0 16px 36px rgba(0,0,0,.22);padding:18px;margin:14px 0}
.heroGrid,.coreGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}@media(max-width:850px){.heroGrid,.coreGrid{grid-template-columns:1fr}}
.metric{background:#071817;border:1px solid #1f4a43;border-radius:8px;padding:14px}.metric strong{display:block;color:var(--green);font-size:24px;margin-top:4px}.metric small{display:block;color:var(--muted);margin-top:5px;line-height:1.5}
.muted{color:var(--muted)}.adv{color:var(--orange);font-weight:900}.tableWrap{overflow-x:auto}table{width:100%;border-collapse:collapse;min-width:760px}th,td{padding:11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:#8fffd0;background:#09211e}
ul{line-height:1.8}.scoreTag{display:inline-block;margin:4px 8px 4px 0;padding:8px 12px;border-radius:8px;border:1px solid #2ecf7a;background:#0d3028;color:#a8ffd6;font-weight:800}.danger{border-color:var(--red);color:#ffd2b0;background:#331415}
.matchDetails{border:1px solid var(--line);border-radius:8px;background:rgba(7,24,23,.96);overflow:hidden;margin:16px 0}.matchDetails summary{cursor:pointer;list-style:none;display:grid;grid-template-columns:minmax(180px,1fr) 110px minmax(240px,1fr);gap:12px;align-items:center;padding:16px 18px;border-bottom:1px solid var(--line)}.matchDetails summary::-webkit-details-marker{display:none}.matchDetails summary span{font-size:22px;font-weight:800;color:var(--blue)}.matchDetails summary strong{font-size:30px;color:var(--green)}.matchDetails summary em{font-style:normal;color:var(--muted);line-height:1.5}.matchBody{border:0;border-top:1px solid var(--line);border-radius:0;margin:0;box-shadow:none}@media(max-width:850px){.matchDetails summary{grid-template-columns:1fr}.matchDetails summary strong{font-size:28px}}
"""


def rows(items: list[dict[str, Any]]) -> str:
    return "".join(
        f"<tr><td>{esc(i['score'])}</td><td>{float(i['probability']) * 100:.1f}%</td><td>{esc(i['ev_signal'])}</td><td>{esc(i['label'])}</td></tr>"
        for i in items
    )


def ev_rows(items: list[dict[str, Any]]) -> str:
    return "".join(
        f"<tr><td>{esc(i['market'])}</td><td>{float(i['model_probability']) * 100:.1f}%</td><td>{float(i['fair_odds']):.2f}</td><td>{esc(i['ev_signal'])}</td><td>{esc(i['note'])}</td></tr>"
        for i in items
    )


def bullets(items: list[str]) -> str:
    return "".join(f"<li>{esc(item)}</li>" for item in items)


def odds_row(item: dict[str, Any]) -> str:
    match = item.get("odds_snapshot") or {}
    return (
        "<tr>"
        f"<td>{esc(item['home_team'])} vs {esc(item['away_team'])}</td>"
        f"<td>{esc(odds_for(match, 'had', 'home'))}</td>"
        f"<td>{esc(odds_for(match, 'had', 'draw'))}</td>"
        f"<td>{esc(odds_for(match, 'had', 'away'))}</td>"
        f"<td>{esc(odds_for(match, 'ttg', 's2'))}</td>"
        f"<td>{esc(odds_for(match, 'ttg', 's3'))}</td>"
        f"<td>{esc(odds_for(match, 'ttg', 's4'))}</td>"
        "</tr>"
    )


def render_parlay_table(title: str, rows: list[dict[str, Any]], note: str) -> str:
    body = "".join(
        "<tr>"
        f"<td>{esc(row['match'])}</td><td>{esc(row['pick'])}</td><td>{fmt_odds(row.get('odds'))}</td>"
        f"<td>{esc(row.get('updated_at', '-'))}</td></tr>"
        for row in rows
    )
    return f"""
    <div class="card">
      <h3>{esc(title)}</h3>
      <p class="muted">{esc(note)}</p>
      <div class="tableWrap"><table><thead><tr><th>比赛</th><th>选择</th><th>赔率</th><th>赔率更新时间</th></tr></thead><tbody>{body}</tbody></table></div>
      <p><strong>三串一理论乘积赔率：{esc(fmt_odds(product_odds(rows)))}</strong></p>
    </div>"""


def render_parlay_section(predictions: dict[str, Any]) -> str:
    matches = predictions.get("matches", [])
    if len(matches) != 3:
        return ""

    score_rows: list[dict[str, Any]] = []
    goals_rows: list[dict[str, Any]] = []
    half_rows: list[dict[str, Any]] = []
    for item in matches:
        odds_match = item.get("odds_snapshot") or {}
        odds = odds_match.get("odds") or {}
        if not odds.get("crs") or not odds.get("ttg") or not odds.get("hafu"):
            return ""
        match_label = f"{item['home_team']} vs {item['away_team']}"
        score_pick = str(item["main_score"])
        total_pick = score_total(score_pick)
        ttg_key = "s7" if total_pick is not None and total_pick >= 7 else f"s{total_pick}"
        half_pick = str(item.get("half_time_pick", "draw"))

        crs = odds.get("crs") or {}
        ttg = odds.get("ttg") or {}
        hafu = odds.get("hafu") or {}
        score_rows.append({"match": match_label, "pick": score_pick, "odds": odds_float(crs.get(score_pick)), "updated_at": crs.get("updatedAt", "-")})
        goals_rows.append({"match": match_label, "pick": f"总进球 {total_pick}", "odds": odds_float(ttg.get(ttg_key)), "updated_at": ttg.get("updatedAt", "-")})
        half_rows.append({"match": match_label, "pick": half_result_label(half_pick), "odds": half_result_implied_odds(odds_match, half_pick), "updated_at": hafu.get("updatedAt", "-")})

    return f"""
  <section class="section" id="parlay">
    <h2>今日三串一</h2>
    {render_parlay_table("比分三串一", score_rows, "按每场主比分选择，赔率来自网站比分市场。")}
    {render_parlay_table("总进球数三串一", goals_rows, "按每场主比分折算总进球数，赔率来自网站总进球市场。")}
    {render_parlay_table("半场胜平负三串一", half_rows, "按每场半场方向选择；赔率由网站半全场赔率池折算为半场主胜/平/客胜隐含赔率。")}
  </section>"""


def card(item: dict[str, Any]) -> str:
    return f"""
<details class="matchDetails" open>
  <summary>
    <span>{esc(item['match_no'])} {esc(item['home_team'])} vs {esc(item['away_team'])}</span>
    <strong>{esc(item['main_score'])}</strong>
    <em>{esc(item['direction_text'])}；{esc(item['goals_range'])}；晋级：{esc(item['advance_pick'])}</em>
  </summary>
  <div class="card matchBody">
    <div class="heroGrid">
      <div class="metric">北京时间<strong>{esc(item['kickoff_bjt'].replace(' +08:00',''))}</strong><small>{esc(item['round'])}</small></div>
      <div class="metric">晋级概率<strong class="adv">{esc(item['advance_probability_text'])}</strong><small>90分钟方向：{esc(item['direction_text'])}</small></div>
      <div class="metric">比分池<strong>{esc(item['main_score'])}</strong><small>{esc(' / '.join(item['backup_scores']))}；冷门 {esc(item['upset_score'])}</small></div>
    </div>
    <p>{esc(item['core_view'])}</p>
    <div>
      <span class="scoreTag">{esc(item['main_score'])}</span>
      {''.join(f'<span class="scoreTag">{esc(s)}</span>' for s in item['backup_scores'])}
      <span class="scoreTag danger">{esc(item['upset_score'])}</span>
    </div>
    <div class="coreGrid">
      <div class="panel"><h3>球队画像</h3><ul>{bullets(item['team_reading'])}</ul></div>
      <div class="panel"><h3>触发条件</h3><ul>{bullets(item['triggers'])}</ul></div>
      <div class="panel"><h3>操作口径</h3><p>强队盘优先看正路和大球上修；比利时场冷门保护最高；半场0-0时统一降低大比分权重。</p></div>
    </div>
    <div class="card">
      <h3>比分矩阵</h3>
      <div class="tableWrap"><table><thead><tr><th>比分</th><th>概率</th><th>EV信号</th><th>标签</th></tr></thead><tbody>{rows(item['score_matrix_top'])}</tbody></table></div>
    </div>
    <div class="card">
      <h3>市场 EV / 大球 / 冷门</h3>
      <div class="tableWrap"><table><thead><tr><th>市场</th><th>模型概率</th><th>公平赔率</th><th>信号</th><th>说明</th></tr></thead><tbody>{ev_rows(item['ev_table'])}</tbody></table></div>
    </div>
  </div>
</details>"""


def render_page(predictions: dict[str, Any], lessons: dict[str, Any]) -> str:
    match_cards = "".join(card(item) for item in predictions["matches"])
    lesson_items = bullets(lessons["lessons"])
    odds_rows = "".join(odds_row(item) for item in predictions["matches"])
    parlay = render_parlay_section(predictions)
    parlay_nav = '<a href="#parlay">三串一</a>' if parlay else ""
    embedded = json.dumps(predictions, ensure_ascii=False, indent=2)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>20260702 淘汰赛预测</title><style>{CSS}</style></head>
<body>
<header>
  <h1>20260702 淘汰赛预测</h1>
  <nav><a href="../index.html">首页</a><a href="../knockout/">淘汰赛归档</a><a href="#review">复盘修正</a><a href="#odds">赔率快照</a>{parlay_nav}</nav>
</header>
<main>
  <section class="section" id="review">
    <h2>昨日复盘与模型修正</h2>
    <div class="card">
      <p><strong>{esc(lessons['headline'])}</strong></p>
      <p>{esc(lessons['summary'])}</p>
      <ul>{lesson_items}</ul>
    </div>
  </section>
  <section class="section" id="odds">
    <h2>竞彩赔率快照</h2>
    <div class="card tableWrap"><table><thead><tr><th>比赛</th><th>主胜</th><th>平</th><th>客胜</th><th>2球</th><th>3球</th><th>4球</th></tr></thead><tbody>{odds_rows}</tbody></table></div>
  </section>
  {parlay}
  <section class="section">
    <h2>今日三场预测</h2>
    {match_cards}
  </section>
  <script id="prediction-data" type="application/json">{embedded}</script>
</main>
</body>
</html>
"""


def update_archive() -> None:
    path = ROOT / "knockout" / "index.html"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    card_html = '<a class="miniCard" href="../20260702/"><strong>20260702</strong><span>英格兰/比利时/美国三场</span></a>'
    if "20260702" in text:
        return
    marker = '<div class="miniGrid">'
    text = text.replace(marker, marker + card_html, 1)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    results = result_payload()
    lessons = lessons_payload()
    predictions = prediction_payload()

    write_json(DATA / "knockout_results_20260701.json", results)
    write_json(DATA / "model_review_lessons_20260701.json", lessons)
    write_json(DATA / "knockout_predictions_20260702.json", predictions)

    DAY.mkdir(exist_ok=True)
    page = render_page(predictions, lessons)
    (DAY / "index.html").write_text(page, encoding="utf-8")
    (DAY / "predict_20260702.html").write_text(page, encoding="utf-8")
    update_archive()

    print("Synced 20260701 results and generated 20260702 predictions.")
    print(DATA / "knockout_results_20260701.json")
    print(DATA / "model_review_lessons_20260701.json")
    print(DATA / "knockout_predictions_20260702.json")
    print(DAY / "predict_20260702.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
