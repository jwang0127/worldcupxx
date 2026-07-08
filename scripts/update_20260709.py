#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATE = "20260709"


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def wc_match(date: str, match_no: str) -> dict[str, Any] | None:
    payload = read_json(DATA_DIR / f"{date}.json", {})
    for match in payload.get("matches", []):
        if str(match.get("id", "")).lstrip("0") == str(match_no):
            if match.get("leagueCode") == "WCC" or "世界杯" in str(match.get("league", "")):
                return match
    return None


def odds_value(match: dict[str, Any] | None, market: str, key: str, fallback: str = "-") -> str:
    if not match:
        return fallback
    value = (((match.get("odds") or {}).get(market) or {}).get(key))
    return fallback if value in (None, "") else str(value)


def score_odds(match: dict[str, Any] | None, scores: list[str]) -> str:
    return " / ".join(odds_value(match, "crs", score.replace(":", "-")) for score in scores)


def goals_odds(match: dict[str, Any] | None, goals: list[str]) -> str:
    return " / ".join(odds_value(match, "ttg", f"s{goal}") for goal in goals)


def hafu_odds(match: dict[str, Any] | None, picks: list[str]) -> str:
    return " / ".join(odds_value(match, "hafu", pick) for pick in picks)


def build_results() -> dict[str, Any]:
    return {
        "date": "20260708",
        "stage": "knockout",
        "status": "90min_finished",
        "matches": [
            {
                "game_id": "53452521",
                "match_no": "95",
                "home_team": "阿根廷",
                "away_team": "埃及",
                "score": "3-2",
                "home_goals": 3,
                "away_goals": 2,
                "decisive_moment": "伤停补时阿根廷进球",
                "winner_team": "阿根廷",
                "advance_team": "阿根廷",
                "prediction_main_score": "2-0",
                "prediction_backup_scores": ["1-0", "2-1"],
                "prediction_upset_score": "1-1",
                "in_score_pool": False,
                "review": "方向命中但比分池漏掉3-2。根因不是强队低赔一定大胜，而是埃及抗压和反击破门路径被低估；阿根廷领先后没有完全收住，埃及进球迫使比赛进入补时再提速。后续强弱差明显但弱队具备进球路径时，必须把2-1旁边的3-2/3-1作为尾部，而不是只放3-0。",
            },
            {
                "game_id": "53452523",
                "match_no": "96",
                "home_team": "瑞士",
                "away_team": "哥伦比亚",
                "score": "0-0",
                "penalty_score": "瑞士点球4-1",
                "home_goals": 0,
                "away_goals": 0,
                "winner_team": "瑞士",
                "advance_team": "瑞士",
                "prediction_main_score": "1-1",
                "prediction_backup_scores": ["0-1", "1-2"],
                "prediction_upset_score": "2-1",
                "in_score_pool": False,
                "review": "晋级方向和90分钟比分均偏差，0-0未入池。根因是模型把哥伦比亚方向和2球低位转成了至少一球，而没有给淘汰赛高强度对抗、两队互相忌惮、点球可接受路径足够权重。后续均衡局必须把0-0作为低节奏保护，且90分钟不败与最终晋级要拆开。",
            },
        ],
    }


def build_lessons() -> dict[str, Any]:
    return {
        "date": "20260708",
        "headline": "07-08复盘：3-2与0-0同时漏池，问题是比分池结构不完整，不是追大或追小",
        "summary": "阿根廷3-2说明强队优势可能被弱队进球路径放大为尾段大球；瑞士0-0点球晋级说明均衡淘汰赛可能长时间锁死。模型修正必须按结构触发：强弱差+弱队能进球时补3-2/3-1；均衡局+双方可接受加时点球时补0-0。不能因为昨天有大比分就追大，也不能因为昨天有0-0就压小。",
        "lessons": [
            "强队低赔不是直接推大胜；若弱队有反击、定位球或抗压后仍能进球的证据，比分池必须同时覆盖2-1、3-1、3-2。",
            "均衡淘汰赛的0-0必须独立检查：胜平负方向偏一方，不代表90分钟一定有进球。",
            "90分钟方向和最终晋级拆开：瑞士0-0后点球晋级证明平局保护不是晋级方向失败。",
            "串关继续降低精确比分权重，主线用方向、总进球区间、半全场节奏；比分串只做小权重观察。",
            "赔率只提供校准，不直接决定结论；需要同时看实力、伤停、体能、淘汰赛动机、对抗结构和尾部触发条件。",
        ],
        "weight_adjustments": {
            "strong_favorite_weak_side_goal_tail": 0.08,
            "goalless_knockout_lock": 0.09,
            "penalty_path_separation": 0.07,
            "market_odds_direct_inference": -0.05,
            "yesterday_score_pattern_inertia": -0.10,
            "exact_score_parlay_weight": -0.06,
        },
    }


def build_prediction(match_no: str, source_date: str | None, data: dict[str, Any]) -> dict[str, Any]:
    odds_match = wc_match(source_date, match_no) if source_date else None
    return {
        **data,
        "match_no": match_no,
        "odds_source": f"Sporttery data/{source_date}.json" if odds_match else "Sporttery odds not open yet; schedule/model placeholder",
        "score_odds": score_odds(odds_match, data["score_pool"]),
        "goals_odds": goals_odds(odds_match, data["goals_pick"]),
        "hafu_odds": hafu_odds(odds_match, data["hafu_pick"]),
        "had_snapshot": (odds_match or {}).get("odds", {}).get("had") if odds_match else None,
        "ttg_snapshot": (odds_match or {}).get("odds", {}).get("ttg") if odds_match else None,
    }


def build_predictions() -> dict[str, Any]:
    rows = [
        build_prediction(
            "97",
            "20260710",
            {
                "round": "四分之一决赛",
                "kickoff_bjt": "2026-07-10 04:00",
                "home_team": "法国",
                "away_team": "摩洛哥",
                "direction_90min": "法国胜优先，防平",
                "advance_pick": "法国",
                "main_score": "2-0",
                "score_pool": ["2:0", "2:1", "1:0", "1:1", "3:1"],
                "tail_scores": ["3:1", "0:0"],
                "goals_pick": ["2", "3"],
                "goals_range": "2-3球，防1球",
                "hafu_pick": ["hh", "dh"],
                "confidence": "中高",
                "rationale": "法国实力、阵容深度和转换效率仍高于摩洛哥，1.42主胜只是方向校准，不能直接推出穿盘。摩洛哥连续淘汰赛韧性强，能把节奏拖窄，所以比分池保留1-0/1-1/0-0；若法国先入球，摩洛哥压上后3-1进入尾部。",
                "injury_note": "本地伤停源未给出新增硬伤停；按阵容完整但淘汰赛体能消耗加权。",
            },
        ),
        build_prediction(
            "98",
            "20260711",
            {
                "round": "四分之一决赛",
                "kickoff_bjt": "2026-07-11 03:00",
                "home_team": "西班牙",
                "away_team": "比利时",
                "direction_90min": "西班牙不败，主胜略优",
                "advance_pick": "西班牙",
                "main_score": "2-1",
                "score_pool": ["2:1", "1:1", "3:1", "2:2", "3:2"],
                "tail_scores": ["3:2", "1:3"],
                "goals_pick": ["3", "4"],
                "goals_range": "3球主线，防4球",
                "hafu_pick": ["dh", "hh"],
                "confidence": "中",
                "rationale": "西班牙控球与压迫稳定性更好，但比利时上一轮1-4说明其领先后反击尾部不能被忽略。本场不是机械追大，而是两队攻击质量和落后方压上结构共同支持3球主线；比分池补3-2，避免再次漏掉强队险胜高比分。",
                "injury_note": "本地伤停源未给出新增硬伤停；比利时进攻尾部按状态上修，防守稳定性不盲目上修。",
            },
        ),
        build_prediction(
            "99",
            None,
            {
                "round": "四分之一决赛",
                "kickoff_bjt": "2026-07-12 05:00",
                "home_team": "挪威",
                "away_team": "英格兰",
                "direction_90min": "英格兰不败，防90分钟平",
                "advance_pick": "英格兰",
                "main_score": "1-2",
                "score_pool": ["1:2", "1:1", "0:1", "2:2", "2:3"],
                "tail_scores": ["2:3", "0:0"],
                "goals_pick": ["2", "3"],
                "goals_range": "2-3球，防0-0",
                "hafu_pick": ["da", "dd"],
                "confidence": "中",
                "rationale": "挪威已经证明能通过高点、反击和早段冲击打穿强队控制，不能把英格兰实力优势简单转成零封。英格兰整体深度和淘汰赛管理更优，最终晋级略优；比分池同时保留1-1/2-2和2-3，吸收昨日3-2尾部课题。",
                "injury_note": "7月12日官方竞彩赔率未开放，伤停按本地外部源无新增硬伤停处理，临场需复核。",
            },
        ),
        build_prediction(
            "100",
            None,
            {
                "round": "四分之一决赛",
                "kickoff_bjt": "2026-07-12 09:00",
                "home_team": "阿根廷",
                "away_team": "瑞士",
                "direction_90min": "阿根廷胜优先，强防平",
                "advance_pick": "阿根廷",
                "main_score": "1-0",
                "score_pool": ["1:0", "2:0", "1:1", "0:0", "2:1"],
                "tail_scores": ["0:0", "3:2"],
                "goals_pick": ["1", "2"],
                "goals_range": "1-2球，防3球尾部",
                "hafu_pick": ["dh", "dd"],
                "confidence": "中",
                "rationale": "阿根廷连续出现2-2、3-2，说明其强势并不等于稳零封；瑞士0-0晋级说明低位防守、拖入加时点球的路径真实存在。本场不能追昨日阿根廷大球，主线反而回到阿根廷小胜和瑞士锁局：1-0/2-0为正路，1-1/0-0为核心保护，3-2只作阿根廷被迫二次提速尾部。",
                "injury_note": "7月12日官方竞彩赔率未开放；阿根廷补时大战和瑞士点球大战均计入体能折损。",
            },
        ),
    ]
    return {
        "date": DATE,
        "stage": "quarterfinals",
        "review_source": "data/model_review_lessons_20260708.json",
        "matches": rows,
    }


def leg(pred: dict[str, Any], score_pick: str, goals_pick: str, half_pick: str, note: str) -> dict[str, Any]:
    return {
        "match_no": pred["match_no"],
        "match": f"{pred['home_team']} vs {pred['away_team']}",
        "direction": pred["direction_90min"],
        "score_pick": score_pick,
        "score_odds": pred["score_odds"],
        "goals_pick": goals_pick,
        "goals_odds": pred["goals_odds"],
        "half_full_pick": half_pick,
        "half_full_odds": pred["hafu_odds"],
        "note": note,
    }


def build_parlay(predictions: dict[str, Any]) -> dict[str, Any]:
    m = {item["match_no"]: item for item in predictions["matches"]}
    return {
        "date": DATE,
        "stage": "quarterfinal_parlay",
        "headline": "四分之一决赛串关：方向/总进球优先，精确比分降权",
        "summary": "97-100四场覆盖二串一、三串一和四场观察。97/98有竞彩实时赔率；99/100官方赔率未开放，先按模型占位，临场赔率出来后必须复核。",
        "groups": [
            {
                "title": "二串一主线",
                "summary": "用赔率已开放的97/98做主线，降低比分依赖。",
                "legs": [
                    leg(m["97"], "2-0 / 2-1", "2 / 3球", "胜胜 / 平胜", "法国方向清晰但防摩洛哥拖窄。"),
                    leg(m["98"], "2-1 / 1-1", "3 / 4球", "平胜 / 胜胜", "西班牙不败，防比利时反击扩大总进球。"),
                ],
            },
            {
                "title": "三串一稳健",
                "summary": "方向加总进球混合，第三腿选英格兰不败，不做单一比分重仓。",
                "legs": [
                    leg(m["97"], "2-0 / 1-0", "2球", "胜胜 / 平胜", "法国小胜或零封。"),
                    leg(m["98"], "2-1 / 3-1", "3球", "平胜 / 胜胜", "西班牙强侧，防尾部。"),
                    leg(m["99"], "1-2 / 1-1", "2 / 3球", "平负 / 平平", "英格兰晋级优先，但挪威有进球路径。"),
                ],
            },
            {
                "title": "三串一防冷",
                "summary": "吸收0-0和3-2漏池教训，专门覆盖低节奏与尾段二次提速。",
                "legs": [
                    leg(m["98"], "2-2 / 3-2", "4 / 5球", "平胜", "比利时尾部不能删。"),
                    leg(m["99"], "2-2 / 2-3", "4 / 5球", "平负", "挪威先进球或英格兰后程反超。"),
                    leg(m["100"], "1-1 / 0-0", "0 / 1 / 2球", "平平", "瑞士锁局与点球路径必须覆盖。"),
                ],
            },
        ],
        "odds_source": "Sporttery live files for 97/98; 99/100 odds pending",
    }


def css() -> str:
    return """
:root{--bg:#071310;--card:#10221f;--panel:#132b26;--line:#24483f;--text:#eefbf6;--muted:#9ab7ae;--green:#58d68d;--blue:#73c7ff;--gold:#f2c15a}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.65}
header,main{max-width:1180px;margin:auto;padding:20px 18px}h1{margin:0 0 12px;font-size:30px;letter-spacing:0}nav{display:flex;gap:10px;flex-wrap:wrap}nav a{color:var(--text);text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:7px 10px;background:#0c1b18}
.section{margin-top:22px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin-top:12px}.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px}.metric strong{display:block;color:var(--green);font-size:22px}.muted{color:var(--muted)}.warn{color:var(--gold)}
.tableWrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:760px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{color:var(--blue)}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;margin-top:14px;overflow:hidden}summary{cursor:pointer;padding:15px 16px;display:grid;grid-template-columns:1fr auto 1.4fr;gap:12px;align-items:center}summary strong{color:var(--green);font-size:24px}.body{border-top:1px solid var(--line);padding:16px}
@media(max-width:900px){.grid,.cols,summary{grid-template-columns:1fr}h1{font-size:25px}table{min-width:680px}}
"""


def render_parlay_group(group: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{esc(item['match_no'])}</td><td>{esc(item['match'])}</td><td>{esc(item['direction'])}</td>"
        f"<td>{esc(item['score_pick'])}</td><td>{esc(item['score_odds'])}</td>"
        f"<td>{esc(item['goals_pick'])}</td><td>{esc(item['goals_odds'])}</td>"
        f"<td>{esc(item['half_full_pick'])}</td><td>{esc(item['half_full_odds'])}</td><td>{esc(item['note'])}</td>"
        "</tr>"
        for item in group["legs"]
    )
    return f"""<div class="card"><h3>{esc(group['title'])}</h3><p class="muted">{esc(group['summary'])}</p>
<div class="tableWrap"><table><thead><tr><th>场次</th><th>比赛</th><th>方向</th><th>比分</th><th>比分赔率</th><th>总进球</th><th>进球赔率</th><th>半全场</th><th>半全场赔率</th><th>说明</th></tr></thead><tbody>{rows}</tbody></table></div></div>"""


def render_prediction_page(predictions: dict[str, Any], lessons: dict[str, Any], parlay: dict[str, Any]) -> str:
    lesson_items = "".join(f"<li>{esc(item)}</li>" for item in lessons["lessons"])
    cards = []
    for item in predictions["matches"]:
        score_rows = "".join(f"<tr><td>{esc(score)}</td><td>{esc('尾部' if score in item['tail_scores'] else '核心')}</td></tr>" for score in item["score_pool"])
        cards.append(
            f"""<details open><summary><span>{esc(item['match_no'])} {esc(item['home_team'])} vs {esc(item['away_team'])}</span><strong>{esc(item['main_score'])}</strong><em>{esc(item['direction_90min'])} / 晋级 {esc(item['advance_pick'])}</em></summary>
<div class="body">
<div class="grid">
<div class="panel metric">时间<strong>{esc(item['kickoff_bjt'])}</strong><small>{esc(item['round'])}</small></div>
<div class="panel metric">总进球<strong>{esc(item['goals_range'])}</strong><small>候选 {esc(' / '.join(item['goals_pick']))}</small></div>
<div class="panel metric">半全场<strong>{esc(' / '.join(item['hafu_pick']))}</strong><small>赔率 {esc(item['hafu_odds'])}</small></div>
<div class="panel metric">置信<strong>{esc(item['confidence'])}</strong><small>{esc(item['odds_source'])}</small></div>
</div>
<div class="card"><h3>综合判断</h3><p>{esc(item['rationale'])}</p><p class="muted">{esc(item['injury_note'])}</p></div>
<div class="cols"><div class="card"><h3>比分池</h3><div class="tableWrap"><table><thead><tr><th>比分</th><th>层级</th></tr></thead><tbody>{score_rows}</tbody></table></div></div>
<div class="card"><h3>赔率快照</h3><p>HAD：{esc(item['had_snapshot'])}</p><p>TTG：{esc(item['ttg_snapshot'])}</p><p>比分赔率：{esc(item['score_odds'])}</p><p>总进球赔率：{esc(item['goals_odds'])}</p></div></div>
</div></details>"""
        )
    parlay_html = "".join(render_parlay_group(group) for group in parlay["groups"])
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>20260709 四强席位预测</title><style>{css()}</style></head>
<body><header><h1>20260709 四分之一决赛预测</h1><nav><a href="../index.html">首页</a><a href="../parlay/">串关</a><a href="../knockout/">淘汰赛日历</a></nav></header><main>
<section class="section"><h2>昨日复盘与模型修正</h2><div class="card"><p><strong>{esc(lessons['headline'])}</strong></p><p>{esc(lessons['summary'])}</p><ul>{lesson_items}</ul></div></section>
<section class="section" id="parlay"><h2>二串一 / 三串一</h2><div class="card"><p><strong>{esc(parlay['headline'])}</strong></p><p>{esc(parlay['summary'])}</p><p class="muted">赔率来源：{esc(parlay['odds_source'])}</p></div>{parlay_html}</section>
<section class="section"><h2>未来四场预测</h2>{''.join(cards)}</section>
<footer class="section muted">以上仅为公开信息整理后的娱乐分析，不构成任何购彩建议，请理性参考。</footer>
</main></body></html>"""


def render_parlay_page(parlay: dict[str, Any]) -> str:
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>未来串关</title><style>{css()}</style></head>
<body><header><h1>未来串关</h1><nav><a href="../index.html">首页</a><a href="../20260709/">07-09预测</a><a href="../knockout/">淘汰赛日历</a></nav></header><main>
<section class="section"><h2>二串一 / 三串一</h2><div class="card"><p><strong>{esc(parlay['headline'])}</strong></p><p>{esc(parlay['summary'])}</p><p class="muted">赔率来源：{esc(parlay['odds_source'])}</p></div>{''.join(render_parlay_group(g) for g in parlay['groups'])}</section>
<footer class="section muted">以上仅为公开信息整理后的娱乐分析，不构成任何购彩建议，请理性参考。</footer>
</main></body></html>"""


def update_schedule() -> None:
    path = DATA_DIR / "knockout_schedule.json"
    payload = read_json(path, {})
    for match in payload.get("matches", []):
        no = str(match.get("match_no"))
        if no == "95":
            match["status"] = "已完赛：阿根廷3-2晋级"
        elif no == "96":
            match["status"] = "已完赛：瑞士0-0，点球4-1晋级"
        elif no == "100":
            match["home_team"] = "阿根廷"
            match["home_team_en"] = "Argentina"
            match["home_code"] = "ARG"
            match["away_team"] = "瑞士"
            match["away_team_en"] = "Switzerland"
            match["away_code"] = "SUI"
            match["status"] = "未开赛"
    payload["last_updated"] = "2026-07-09"
    payload["update_note"] = "回填95-96赛果；100更新为阿根廷 vs 瑞士；生成97-100四分之一决赛预测。"
    write_json(path, payload)
    update_schedule_markdown(payload)


def update_schedule_markdown(payload: dict[str, Any]) -> None:
    headers = [
        "比赛ID", "场次编号", "阶段顺序", "轮次", "名义主队中文", "名义主队英文", "主队代码",
        "名义客队中文", "名义客队英文", "客队代码", "当地开球时间", "当地日期", "当地时间",
        "当地时区", "北京时间", "北京时间日期", "北京时间开球时间", "比赛状态", "胜者晋级比赛ID", "备注",
    ]
    keys = [
        "game_id", "match_no", "stage_order", "round", "home_team", "home_team_en", "home_code",
        "away_team", "away_team_en", "away_code", "kickoff_local", "local_date", "local_time",
        "local_timezone", "kickoff_bjt", "beijing_date", "beijing_time", "status", "winner_advances_to", "note",
    ]

    def cell(value: Any) -> str:
        return str("" if value is None else value).replace("|", "/")

    lines = [
        "# 2026 世界杯淘汰赛赛程表（中文版）",
        "> 2026-07-09 更新：回填 95-96 赛果；100 确认为阿根廷 vs 瑞士；97-100 已生成四分之一决赛预测。",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for match in payload.get("matches", []):
        lines.append("| " + " | ".join(cell(match.get(key)) for key in keys) + " |")
    (ROOT / "2026世界杯淘汰赛赛程表_中文版_Codex.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_20260712_placeholder(predictions: dict[str, Any]) -> dict[str, Any]:
    selected = [item for item in predictions["matches"] if item["match_no"] in {"99", "100"}]
    matches = []
    for item in selected:
        matches.append(
            {
                "id": item["match_no"].zfill(3),
                "matchNumStr": f"待定{item['match_no']}",
                "league": "世界杯",
                "leagueCode": "WCC",
                "kickoff": item["kickoff_bjt"].replace(" +08:00", "") + ":00",
                "matchDate": "2026-07-12",
                "matchStatus": "OddsPending",
                "home": item["home_team"],
                "away": item["away_team"],
                "prediction": {
                    "totalGoals": "/".join(item["goals_pick"]),
                    "scores": item["score_pool"][:2],
                    "upset": item["score_pool"][2],
                    "confidence": item["confidence"],
                },
                "result": None,
                "review": "Sporttery odds not open yet; placeholder generated from knockout schedule, strength model, review lessons, and injury/fitness assumptions.",
                "odds": {"had": None, "ttg": None, "hhad": None, "crs": None, "hafu": None},
            }
        )
    return {
        "date": "20260712",
        "dateText": "2026-07-12",
        "source": "schedule-model-placeholder",
        "fetchedAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "apiPoolCode": "ttg,had,hhad,crs,hafu",
        "matches": matches,
    }


def update_model_state() -> None:
    path = ROOT / "model_state.json"
    payload = read_json(path, {})
    payload["updatedAt"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    payload["calibration"] = {
        "latestReview": "20260708",
        "lesson": "阿根廷3-2与瑞士0-0均未入比分池：强弱差局要补强队被迫二次提速的3-2/3-1尾部，均衡淘汰赛要补0-0锁局和点球路径。",
        "todayAdjustment": "97-100四场不按昨日大小球惯性外推；法国场主2-0防1-1，西班牙场主2-1防3-2，挪威-英格兰防平与2-3，阿根廷-瑞士主小胜并强防0-0/1-1。",
    }
    history = [item for item in payload.setdefault("history", []) if item.get("date") != "20260708"]
    history.append(
        {
            "date": "20260708",
            "settled": 2,
            "directionHits": 1,
            "directionHitRate": "50%",
            "mainScoreHits": 0,
            "scorePoolHits": 0,
            "scorePoolHitRate": "0%",
            "totalGoalHits": 0,
            "totalGoalHitRate": "0%",
        }
    )
    payload["history"] = history
    write_json(path, payload)


def patch_home() -> None:
    path = ROOT / "index.html"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    marker = '<section class="section" id="future">'
    replacement = """<section class="section" id="future"><h2>未来四强席位赛程</h2><div class="card tableWrap"><table><thead><tr><th>北京时间</th><th>场次</th><th>轮次</th><th>对阵</th><th>预测</th></tr></thead><tbody>
<tr><td>07-10 04:00</td><td>97</td><td>四分之一决赛</td><td>法国 vs 摩洛哥</td><td>法国晋级，2-0 / 2-1，防1-1</td></tr>
<tr><td>07-11 03:00</td><td>98</td><td>四分之一决赛</td><td>西班牙 vs 比利时</td><td>西班牙晋级，2-1 / 3-1，防3-2</td></tr>
<tr><td>07-12 05:00</td><td>99</td><td>四分之一决赛</td><td>挪威 vs 英格兰</td><td>英格兰晋级，1-2 / 1-1，防2-3</td></tr>
<tr><td>07-12 09:00</td><td>100</td><td>四分之一决赛</td><td>阿根廷 vs 瑞士</td><td>阿根廷晋级，1-0 / 2-0，防0-0/1-1</td></tr>
</tbody></table></div></section>"""
    start = text.find(marker)
    if start >= 0:
        end = text.find("</section>", start)
        if end >= 0:
            text = text[:start] + replacement + text[end + len("</section>") :]
    else:
        text = text.replace("</main>", replacement + "\n</main>")
    text = text.replace("07-08预测", "07-09预测")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    results = build_results()
    lessons = build_lessons()
    predictions = build_predictions()
    parlay = build_parlay(predictions)

    write_json(DATA_DIR / "knockout_results_20260708.json", results)
    write_json(DATA_DIR / "model_review_lessons_20260708.json", lessons)
    write_json(DATA_DIR / "knockout_predictions_20260709.json", predictions)
    write_json(DATA_DIR / "quarterfinal_parlay_20260709.json", parlay)
    write_json(DATA_DIR / "20260712.json", build_20260712_placeholder(predictions))

    day_dir = ROOT / DATE
    day_dir.mkdir(exist_ok=True)
    page = render_prediction_page(predictions, lessons, parlay)
    (day_dir / "index.html").write_text(page, encoding="utf-8")
    (day_dir / f"predict_{DATE}.html").write_text(page, encoding="utf-8")
    for daily in ["20260710", "20260711", "20260712"]:
        daily_dir = ROOT / daily
        daily_dir.mkdir(exist_ok=True)
        (daily_dir / "index.html").write_text(page, encoding="utf-8")
        (daily_dir / f"predict_{daily}.html").write_text(page, encoding="utf-8")
    (ROOT / "parlay").mkdir(exist_ok=True)
    (ROOT / "parlay" / "index.html").write_text(render_parlay_page(parlay), encoding="utf-8")

    update_schedule()
    update_model_state()
    patch_home()
    print("Updated 20260709 quarterfinal predictions, review, parlay, schedule, and model state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
