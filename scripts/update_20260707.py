#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATE = "20260707"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def esc(value: Any) -> str:
    import html

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


def score_total(score: str) -> int:
    left, right = re.split(r"[-:：]", score)
    return int(left) + int(right)


def get_world_cup_odds() -> dict[str, dict[str, Any]]:
    payload = read_json(DATA_DIR / f"{DATE}.json")
    return {
        str(item["id"]).lstrip("0"): item
        for item in payload.get("matches", [])
        if item.get("league") == "世界杯"
    }


def css() -> str:
    return """
:root{--bg:#081412;--card:#10211e;--panel:#132b27;--line:#23443e;--text:#e8f6f1;--muted:#9dbab2;--green:#58d68d;--blue:#6bbcff;--gold:#f4c95d;--red:#ff7f7f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.65}
header{padding:24px 18px 12px;max-width:1180px;margin:auto}h1{margin:0 0 14px;font-size:32px}nav{display:flex;gap:10px;flex-wrap:wrap}nav a{color:var(--text);text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:7px 10px;background:#0c1b18}
main{max-width:1180px;margin:auto;padding:0 18px 42px}.section{margin-top:22px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin-top:12px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px}.metric strong{display:block;color:var(--green);font-size:24px}.metric small,.muted{color:var(--muted)}
.tableWrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:760px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{color:var(--blue);font-weight:700}.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 8px;margin:2px;background:#0c1b18}.good{color:var(--green)}.warn{color:var(--gold)}.bad{color:var(--red)}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;margin-top:14px;overflow:hidden}summary{cursor:pointer;padding:15px 16px;display:grid;grid-template-columns:1fr auto 1.4fr;gap:12px;align-items:center}summary strong{color:var(--green);font-size:24px}.body{border-top:1px solid var(--line);padding:16px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:850px){.grid,.cols,summary{grid-template-columns:1fr}h1{font-size:26px}table{min-width:680px}}
"""


def build_results() -> dict[str, Any]:
    return {
        "date": "20260706",
        "stage": "knockout",
        "status": "90min_finished",
        "matches": [
            {
                "game_id": "53452517",
                "match_no": "91",
                "home_team": "巴西",
                "away_team": "挪威",
                "score": "1-2",
                "home_goals": 1,
                "away_goals": 2,
                "half_time_score": "0-1",
                "hafu_result": "负负",
                "winner_team": "挪威",
                "advance_team": "挪威",
                "prediction_main_score": "2-1",
                "prediction_backup_scores": ["2-0", "1-1"],
                "prediction_upset_score": "1-2",
                "review": "方向未中但爆冷比分命中。大比分/开放化的根因是模型把巴西控场优势过度转成胜面，却低估了挪威先手反击和领先后空间继续扩大的路径；淘汰赛强队一旦被迫压上，3球区间不能只服务于强队2-1，也要保留弱侧1-2/1-3。",
            },
            {
                "game_id": "53452519",
                "match_no": "92",
                "home_team": "墨西哥",
                "away_team": "英格兰",
                "score": "2-3",
                "home_goals": 2,
                "away_goals": 3,
                "half_time_score": "1-1",
                "hafu_result": "平负",
                "winner_team": "英格兰",
                "advance_team": "英格兰",
                "prediction_main_score": "0-1",
                "prediction_backup_scores": ["1-1", "1-2"],
                "prediction_upset_score": "1-0",
                "review": "方向和半全场命中，但5球比分漏出。原因是模型把墨西哥低节奏和受让保护理解成小比分保护，未同步处理英格兰早段被迫提速、墨西哥主场进球能力和淘汰赛末段追分导致的双向开放；强客胜叠加主队有进球路径时，总进球3/4必须扩成主池，2-3应进入备选。",
            },
        ],
    }


def build_lessons() -> dict[str, Any]:
    return {
        "date": "20260706",
        "headline": "07-06复盘：两场均打穿保守比分，弱侧进球与领先后开放路径需要上调",
        "summary": "巴西1-2挪威、墨西哥2-3英格兰说明16强后段不是单纯小比分淘汰赛。模型原本方向过于依赖强队控场和受让保护，对先手进球、落后追分、强队压上后给出的反击空间估计不足；后续需要把总进球3/4与弱侧进球共同纳入主池。",
        "lessons": [
            "大比分原因一：先手进球改变比赛结构。挪威先进球后，巴西必须压上，弱侧反击从观察项变成主路径，1-2不应只做爆冷尾部。",
            "大比分原因二：强队方向和双方进球不能拆开看。英格兰方向成立，但墨西哥主场和受让保护并不等于低比分，而是更像2-3/1-2的开放客胜。",
            "大比分原因三：淘汰赛末段追分放大尾部。落后方不再接受小负，70分钟后总进球3/4权重要高于小组赛。",
            "模型修正：强队胜面低于60%且对手具备稳定进球路径时，总进球2不再作为默认主线，必须同时检查3球和4球赔率低位。",
            "模型修正：半全场平负/负负命中率继续有效，但要与比分池联动；平负不只对应0-1，也应覆盖1-2、2-3。",
            "串关修正：二串一优先用方向/总进球组合，比分串只保留小注；三串一必须含一个防冷或大球腿，不能全部压保守小比分。",
        ],
        "weight_adjustments": {
            "underdog_first_goal_transition": 0.08,
            "both_teams_to_score_in_knockout": 0.07,
            "late_chasing_over_goals": 0.06,
            "favorite_control_score_suppression": -0.05,
            "hhad_low_score_protection": -0.04,
            "half_full_to_open_score_link": 0.05,
        },
    }


def prediction_payload(odds: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "date": DATE,
        "stage": "knockout",
        "review_source": "data/model_review_lessons_20260706.json",
        "matches": [
            {
                "game_id": "53452513",
                "match_no": "93",
                "round": "16强赛",
                "home_team": "葡萄牙",
                "away_team": "西班牙",
                "kickoff_bjt": "2026-07-07 03:00:00 +08:00",
                "venue": odds["93"].get("venue", ""),
                "model_version": "v8.3-open-score-btts-correction",
                "direction_90min": "away",
                "direction_text": "西班牙90分钟胜优先，主线1-2，防1-1/0-2",
                "half_time": "葡萄牙 0-1 西班牙",
                "half_time_pick": "away",
                "hafu_pick": "aa",
                "main_score": "1-2",
                "backup_scores": ["0-2", "1-1"],
                "upset_score": "2-1",
                "goals_range": "2-4球，核心3球",
                "advance_pick": "西班牙",
                "advance_probability_text": "90分钟：葡萄牙胜 22% / 平 27% / 西班牙胜 51%；最终晋级：葡萄牙 35% / 西班牙 65%",
                "core_view": "西班牙连续强势且客胜赔率低位，方向仍偏西班牙；但07-06复盘后不再把强队优势压成单一小比分。葡萄牙硬仗韧性和定位球足以贡献进球，主线从0-2修正为1-2，0-2作为西班牙控场零封保护，1-1用于半场或60分钟前打不开时防平。",
                "review_adjustment": "昨日两场都打穿保守比分，本场提高双方进球和3球区间权重。若西班牙早球，1-2/1-3升权；若半场0-0，1-1升权，西班牙方向降一档。",
                "score_matrix_top": [
                    {"score": "1-2", "probability": 0.17, "ev_signal": "+0.05", "label": "开放客胜主线"},
                    {"score": "0-2", "probability": 0.13, "ev_signal": "+0.03", "label": "西班牙控场"},
                    {"score": "1-1", "probability": 0.13, "ev_signal": "+0.03", "label": "防平保护"},
                    {"score": "2-1", "probability": 0.08, "ev_signal": "防冷", "label": "葡萄牙硬仗反杀"},
                ],
                "ev_table": [
                    {"market": "西班牙90分钟方向", "model_probability": 0.51, "fair_odds": 1.96, "ev_signal": "方向确认", "note": "赔率支持客胜，但不包装成高EV。"},
                    {"market": "比分：1-2 / 0-2 / 1-1", "model_probability": 0.43, "fair_odds": 2.33, "ev_signal": "+0.05", "note": "1-2与1-1同为赔率低位，优先保留双方进球。"},
                    {"market": "总进球：3球，防2球/4球", "model_probability": 0.58, "fair_odds": 1.72, "ev_signal": "+0.04", "note": "昨日复盘后3球优先，4球进观察池。"},
                    {"market": "半全场：负负 / 平负", "model_probability": 0.45, "fair_odds": 2.22, "ev_signal": "+0.03", "note": "西班牙可早段建立优势，也可下半场解决。"},
                ],
                "model_insights": [
                    {"title": "主线", "content": "西班牙胜方向优先，但比分从保守0-1上修到1-2。"},
                    {"title": "比分池", "content": "稳胆：1-2、0-2、1-1；防冷：2-1。"},
                    {"title": "串关", "content": "更适合做三串一第一腿的方向或总进球3球腿。"},
                ],
                "team_reading": [
                    "西班牙强在中前场压迫和连续制造高质量机会，客胜赔率低位与基本面一致。",
                    "葡萄牙面对强队不会完全失去进球路径，定位球和转换能支撑1球。",
                    "07-06复盘后，本场不再用纯小比分表达西班牙优势。"
                ],
                "triggers": [
                    "西班牙30分钟前进球：1-2和1-3升权，0-2保留。",
                    "半场0-0：1-1升权，西班牙胜方向降到小胜/加时脚本。",
                    "葡萄牙先进球：1-1与2-1升权，总进球3/4继续保留。"
                ],
                "odds_snapshot": odds["93"],
                "odds_source": "Sporttery calculator getMatchCalculatorV1, data/20260707.json",
            },
            {
                "game_id": "53452515",
                "match_no": "94",
                "round": "16强赛",
                "home_team": "美国",
                "away_team": "比利时",
                "kickoff_bjt": "2026-07-07 08:00:00 +08:00",
                "venue": odds["94"].get("venue", ""),
                "model_version": "v8.3-open-score-btts-correction",
                "direction_90min": "draw",
                "direction_text": "90分钟平局优先，主线1-1，防2-1/1-2",
                "half_time": "美国 1-1 比利时",
                "half_time_pick": "draw",
                "hafu_pick": "dd",
                "main_score": "1-1",
                "backup_scores": ["2-1", "1-2"],
                "upset_score": "0-1",
                "goals_range": "2-4球，核心2/3球",
                "advance_pick": "美国",
                "advance_probability_text": "90分钟：美国胜 35% / 平 31% / 比利时胜 34%；最终晋级：美国 52% / 比利时 48%",
                "core_view": "赔率把美国略置于低位，但双方差距很小。美国主场与体能有保护，比利时进攻质量仍能制造进球；07-06复盘后，受让/均势保护不再简单压小，1-1是主线，2-1和1-2并列保护，若早球出现可扩到2-2。",
                "review_adjustment": "昨日墨西哥2-3英格兰提醒：主队有进球路径时，客强或均势局会被拉开到3/5球。本场保持90分钟平局主线，但总进球从纯2球扩到2/3球并防2-2。",
                "score_matrix_top": [
                    {"score": "1-1", "probability": 0.16, "ev_signal": "+0.04", "label": "均势主线"},
                    {"score": "2-1", "probability": 0.13, "ev_signal": "+0.03", "label": "美国主场小胜"},
                    {"score": "1-2", "probability": 0.13, "ev_signal": "+0.03", "label": "比利时反击小胜"},
                    {"score": "2-2", "probability": 0.08, "ev_signal": "防大", "label": "早球开放"},
                ],
                "ev_table": [
                    {"market": "90分钟平局/美国不败", "model_probability": 0.66, "fair_odds": 1.52, "ev_signal": "+0.03", "note": "美国主场保护存在，但胜负差距很窄。"},
                    {"market": "比分：1-1 / 2-1 / 1-2", "model_probability": 0.42, "fair_odds": 2.38, "ev_signal": "+0.04", "note": "三条均势路径并列，比分串不宜重仓单点。"},
                    {"market": "总进球：2球 / 3球", "model_probability": 0.55, "fair_odds": 1.82, "ev_signal": "+0.03", "note": "2球最低，3球与昨日开放修正共同保留。"},
                    {"market": "半全场：平平", "model_probability": 0.29, "fair_odds": 3.45, "ev_signal": "+0.02", "note": "半场即可能互有进球，平平不等于0-0慢局。"},
                ],
                "model_insights": [
                    {"title": "主线", "content": "90分钟平局优先，美国最终晋级略高。"},
                    {"title": "比分池", "content": "稳胆：1-1、2-1、1-2；开放保护：2-2。"},
                    {"title": "串关", "content": "二串一可搭美国不败/总进球2-3，三串一里做波动腿。"},
                ],
                "team_reading": [
                    "美国主场和身体对抗带来下限，领先后有守住小胜的路径。",
                    "比利时进攻质量足够高，不适合被模型压成无进球客队。",
                    "均势局优先看1-1，再根据早球选择2-1、1-2或2-2。"
                ],
                "triggers": [
                    "半场1-1：1-1和2-2升权，胜负比分降权。",
                    "美国先进球：2-1升权，比利时追平能力仍保留1-1。",
                    "比利时先进球：1-2和1-1升权，美国主场后段反扑会推高总进球。"
                ],
                "odds_snapshot": odds["94"],
                "odds_source": "Sporttery calculator getMatchCalculatorV1, data/20260707.json",
            },
        ],
    }


def build_parlay(predictions: dict[str, Any]) -> dict[str, Any]:
    matches = {item["match_no"]: item for item in predictions["matches"]}
    def leg(no: str, score_pick: str, goals_pick: str, half_full_pick: str, note: str) -> dict[str, Any]:
        item = matches[no]
        odds = item["odds_snapshot"].get("odds", {})
        crs = odds.get("crs", {})
        ttg = odds.get("ttg", {})
        hafu = odds.get("hafu", {})
        score_odds = " / ".join(fmt_odds(crs.get(score)) for score in score_pick.split(" / "))
        goals_numbers = [int(text) for text in re.findall(r"(\d+)球", goals_pick)]
        goals_odds = " / ".join(fmt_odds(ttg.get(f"s{n}" if n < 7 else "s7")) for n in goals_numbers)
        hafu_keys = {"负负": "aa", "平负": "da", "平平": "dd", "胜胜": "hh", "胜平": "hd", "平胜": "dh"}
        half_odds = " / ".join(fmt_odds(hafu.get(hafu_keys.get(text.strip(), ""))) for text in half_full_pick.split(" / "))
        return {
            "match_no": no,
            "match": f"{item['home_team']} vs {item['away_team']}",
            "score_pick": score_pick,
            "score_odds": score_odds,
            "goals_pick": goals_pick,
            "goals_odds": goals_odds,
            "half_full_pick": half_full_pick,
            "half_full_odds": half_odds,
            "ev_signal": "+0.03",
            "note": note,
            "odds_updated_at": crs.get("updatedAt") or ttg.get("updatedAt") or hafu.get("updatedAt", "-"),
        }

    leg93 = leg("93", "1-2 / 0-2", "3球 / 2球", "负负 / 平负", "西班牙方向优先，昨日复盘后主防1-2。")
    leg94 = leg("94", "1-1 / 2-1", "2球 / 3球", "平平 / 平胜", "美国不败和平局保护，防早球开放。")
    return {
        "date": DATE,
        "stage": "round16_future_parlay",
        "headline": "07-07更新：复盘91/92后，串关从保守小比分切到方向+总进球双保护",
        "summary": "今日只有93/94两场世界杯，输出二串一为主；三串一采用93/94加下一比赛日95的预案，95待赔率更新后再确认。",
        "groups": [
            {
                "title": "主票：93-94二串一",
                "summary": "更稳的两场组合：西班牙方向/总进球3 + 美国不败/1-1保护。",
                "legs": [leg93, leg94],
            },
            {
                "title": "比分二串一",
                "summary": "波动较高，只适合小注参考。",
                "legs": [
                    {**leg93, "score_pick": "1-2", "score_odds": fmt_odds(matches["93"]["odds_snapshot"]["odds"]["crs"].get("1-2"))},
                    {**leg94, "score_pick": "1-1", "score_odds": fmt_odds(matches["94"]["odds_snapshot"]["odds"]["crs"].get("1-1"))},
                ],
            },
            {
                "title": "预案：93-95三串一",
                "summary": "第三腿先用阿根廷 vs 埃及的模型预案，待07-08赔率快照后更新。",
                "legs": [
                    leg93,
                    leg94,
                    {
                        "match_no": "95",
                        "match": "阿根廷 vs 埃及",
                        "score_pick": "2-1 / 2-0",
                        "score_odds": "-",
                        "goals_pick": "3球 / 2球",
                        "goals_odds": "-",
                        "half_full_pick": "胜胜 / 平胜",
                        "half_full_odds": "-",
                        "ev_signal": "待赔率",
                        "note": "阿根廷正路，但昨日复盘后保留埃及进球和3球路径。",
                    },
                ],
            },
        ],
        "odds_source": "Sporttery calculator getMatchCalculatorV1, data/20260707.json for match 93/94",
    }


def render_parlay_group(group: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{esc(item.get('match_no'))}</td><td>{esc(item.get('match'))}</td>"
        f"<td>{esc(item.get('score_pick'))}</td><td>{esc(item.get('score_odds'))}</td>"
        f"<td>{esc(item.get('goals_pick'))}</td><td>{esc(item.get('goals_odds'))}</td>"
        f"<td>{esc(item.get('half_full_pick'))}</td><td>{esc(item.get('half_full_odds'))}</td>"
        f"<td>{esc(item.get('ev_signal'))}</td><td>{esc(item.get('note'))}</td>"
        "</tr>"
        for item in group.get("legs", [])
    )
    return f"""<div class="card"><h3>{esc(group['title'])}</h3><p class="muted">{esc(group['summary'])}</p>
<div class="tableWrap"><table><thead><tr><th>场次</th><th>比赛</th><th>比分</th><th>比分赔率</th><th>总进球</th><th>进球赔率</th><th>半全场</th><th>半全场赔率</th><th>EV</th><th>说明</th></tr></thead><tbody>{rows}</tbody></table></div></div>"""


def render_prediction_page(predictions: dict[str, Any], lessons: dict[str, Any], parlay: dict[str, Any]) -> str:
    cards = []
    for item in predictions["matches"]:
        matrix = "".join(
            f"<tr><td>{esc(row['score'])}</td><td>{float(row['probability'])*100:.1f}%</td><td>{esc(row['ev_signal'])}</td><td>{esc(row['label'])}</td></tr>"
            for row in item["score_matrix_top"]
        )
        ev_rows = "".join(
            f"<tr><td>{esc(row['market'])}</td><td>{float(row['model_probability'])*100:.1f}%</td><td>{float(row['fair_odds']):.2f}</td><td>{esc(row['ev_signal'])}</td><td>{esc(row['note'])}</td></tr>"
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
<div class="card"><h3>判断口径</h3><p>{esc(item['core_view'])}</p><p class="muted">{esc(item['review_adjustment'])}</p></div>
<div class="cols"><div class="card"><h3>比分矩阵</h3><div class="tableWrap"><table><thead><tr><th>比分</th><th>概率</th><th>EV</th><th>标签</th></tr></thead><tbody>{matrix}</tbody></table></div></div>
<div class="card"><h3>EV 表</h3><div class="tableWrap"><table><thead><tr><th>市场</th><th>概率</th><th>公平赔率</th><th>EV</th><th>说明</th></tr></thead><tbody>{ev_rows}</tbody></table></div></div></div>
<div class="grid">{insights}</div>
<div class="cols"><div class="card"><h3>球队画像</h3><ul>{reading}</ul></div><div class="card"><h3>触发条件</h3><ul>{triggers}</ul></div></div>
<div class="card"><h3>赔率快照</h3><p class="muted">HAD {esc(odds['had']['home'])}/{esc(odds['had']['draw'])}/{esc(odds['had']['away'])}；TTG最低：3球 {esc(odds['ttg']['s3'])}，2球 {esc(odds['ttg']['s2'])}；比分低位参考：1-1 {esc(odds['crs'].get('1-1'))}，1-2 {esc(odds['crs'].get('1-2'))}，2-1 {esc(odds['crs'].get('2-1'))}。来源：{esc(item['odds_source'])}</p></div>
</div></details>"""
        )
    lesson_items = "".join(f"<li>{esc(text)}</li>" for text in lessons["lessons"])
    parlay_html = "".join(render_parlay_group(group) for group in parlay["groups"])
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>20260707 淘汰赛预测</title><style>{css()}</style></head>
<body><header><h1>20260707 淘汰赛预测</h1><nav><a href="../index.html">首页</a><a href="../parlay/">串关</a><a href="../knockout/">淘汰赛日期</a></nav></header><main>
<section class="section"><h2>昨日复盘与模型修正</h2><div class="card"><p><strong>{esc(lessons['headline'])}</strong></p><p>{esc(lessons['summary'])}</p><ul>{lesson_items}</ul></div></section>
<section class="section" id="parlay"><h2>二串一 / 三串一</h2><div class="card"><p><strong>{esc(parlay['headline'])}</strong></p><p>{esc(parlay['summary'])}</p><p class="muted">赔率来源：{esc(parlay['odds_source'])}</p></div>{parlay_html}</section>
<section class="section"><h2>今日比赛预测</h2>{''.join(cards)}</section>
</main></body></html>"""


def render_parlay_page(parlay: dict[str, Any]) -> str:
    groups = "".join(render_parlay_group(group) for group in parlay["groups"])
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>未来串关</title><style>{css()}</style></head>
<body><header><h1>未来串关</h1><nav><a href="../index.html">首页</a><a href="../20260707/">07-07预测</a><a href="../knockout/">淘汰赛日期</a></nav></header><main>
<section class="section"><h2>未来串关</h2><div class="card"><p><strong>{esc(parlay['headline'])}</strong></p><p>{esc(parlay['summary'])}</p><p class="muted">赔率来源：{esc(parlay['odds_source'])}</p></div>{groups}</section>
</main></body></html>"""


def patch_home_page() -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "<td>巴西 / 挪威 胜者</td><td>待产生</td><td>墨西哥 / 英格兰 胜者</td><td>待产生</td>",
        "<td>挪威</td><td>已入围</td><td>英格兰</td><td>已入围</td>",
    )
    text = text.replace(
        "<tr><td>07-06 04:00</td><td>91</td><td>16强赛</td><td>巴西 vs 挪威</td><td>墨西哥 / 英格兰 胜者</td></tr><tr><td>07-06 08:00</td><td>92</td><td>16强赛</td><td>墨西哥 vs 英格兰</td><td>巴西 / 挪威 胜者</td></tr>",
        "",
    )
    text = text.replace(
        "<tr><td>07-06 04:00</td><td>91</td><td>巴西 vs 挪威</td><td>墨西哥 / 英格兰 胜者</td></tr><tr><td>07-06 08:00</td><td>92</td><td>墨西哥 vs 英格兰</td><td>巴西 / 挪威 胜者</td></tr>",
        "",
    )
    insert = (
        "<tr><td>07-06</td><td>91</td><td>巴西 vs 挪威</td><td><strong>1-2</strong></td><td>挪威胜</td><td>2-1</td><td>方向未中但爆冷比分命中；巴西落后后压上，挪威反击空间被低估，3球区间应同时保留弱侧1-2。</td></tr>"
        "<tr><td>07-06</td><td>92</td><td>墨西哥 vs 英格兰</td><td><strong>2-3</strong></td><td>英格兰胜</td><td>0-1</td><td>方向和半全场命中但总进球漏大；墨西哥进球路径叠加强队提速，平负应覆盖1-2/2-3。</td></tr>"
    )
    marker = "</tbody></table></div></section>"
    idx = text.rfind(marker)
    if idx != -1 and "巴西 vs 挪威</td><td><strong>1-2" not in text:
        text = text[:idx] + insert + text[idx:]
    text = text.replace("07-06预测", "07-07预测")
    path.write_text(text, encoding="utf-8")


def patch_knockout_archive() -> None:
    path = ROOT / "knockout" / "index.html"
    text = path.read_text(encoding="utf-8")
    if "../20260707/" in text:
        return
    marker = '<div class="miniGrid">'
    replacement = (
        '<div class="miniGrid"><a class="miniCard" href="../20260707/">'
        "<strong>20260707</strong><span>葡萄牙/美国两场</span></a>"
    )
    text = text.replace(marker, replacement, 1)
    path.write_text(text, encoding="utf-8")


def update_model_state() -> None:
    path = ROOT / "model_state.json"
    payload = read_json(path)
    payload["updatedAt"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    payload["calibration"] = {
        "latestReview": "20260706",
        "lesson": "巴西1-2挪威、墨西哥2-3英格兰：淘汰赛16强后段出现开放比分，弱侧进球、先手进球后的比赛结构转换、落后追分导致的3/4球区间需要上调。",
        "todayAdjustment": "07-07预测修正：西班牙方向仍优先但改用1-2主线；美国-比利时走均势1-1并保留2-1/1-2/2-2。串关以方向+总进球为主，比分串降仓。",
    }
    payload["weights"]["tactics"] = 0.16
    payload["weights"]["form"] = 0.15
    payload["weights"]["odds"] = 0.23
    payload["weights"]["external"] = 0.08
    payload["weights"]["mystic"] = 0.04
    payload["weights"]["motivation"] = 0.16
    history_item = {
        "date": "20260706",
        "settled": 2,
        "directionHits": 1,
        "directionHitRate": "50%",
        "mainScoreHits": 0,
        "upsetScoreHits": 1,
        "totalGoalHits": 1,
        "totalGoalHitRate": "50%",
    }
    history = [item for item in payload.setdefault("history", []) if item.get("date") != "20260706"]
    history.append(history_item)
    payload["history"] = history
    write_json(path, payload)


def main() -> int:
    odds = get_world_cup_odds()
    results = build_results()
    lessons = build_lessons()
    predictions = prediction_payload(odds)
    parlay = build_parlay(predictions)

    write_json(DATA_DIR / "knockout_results_20260706.json", results)
    write_json(DATA_DIR / "model_review_lessons_20260706.json", lessons)
    write_json(DATA_DIR / "knockout_predictions_20260707.json", predictions)
    write_json(DATA_DIR / "round16_parlay_20260707.json", parlay)

    day_dir = ROOT / DATE
    day_dir.mkdir(exist_ok=True)
    page = render_prediction_page(predictions, lessons, parlay)
    (day_dir / "index.html").write_text(page, encoding="utf-8")
    (day_dir / f"predict_{DATE}.html").write_text(page, encoding="utf-8")
    (ROOT / "parlay" / "index.html").write_text(render_parlay_page(parlay), encoding="utf-8")

    patch_home_page()
    patch_knockout_archive()
    update_model_state()
    print("Updated 20260707 predictions, 20260706 review, parlay page, and model state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
