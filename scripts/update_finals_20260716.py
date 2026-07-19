from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DISCLAIMER = "以上仅为公开信息整理后的娱乐分析，不构成任何购彩建议，请理性参考。"
UPDATED_AT = "2026-07-16 10:30 +08:00"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def e(value) -> str:
    return html.escape(str(value))


CSS = """
:root{--bg:#061210;--card:#10241f;--panel:#15312a;--line:#2a574b;--text:#effcf7;--muted:#a1bdb4;--green:#58db96;--blue:#79cfff;--gold:#f3c45e;--red:#ff8982}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 15% 0,rgba(88,219,150,.16),transparent 28%),var(--bg);color:var(--text);font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.65}main{max-width:1180px;margin:auto;padding:34px 18px 48px}h1{font-size:clamp(30px,5vw,48px);margin:0}h2{color:var(--blue);margin:28px 0 12px}h3{margin:4px 0;color:var(--gold)}p{color:var(--muted)}a{color:var(--green)}.hero{display:flex;justify-content:space-between;gap:20px;align-items:flex-start}.chips{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}.chip{border:1px solid var(--line);background:#0c211c;border-radius:999px;padding:6px 10px;color:#a8ffda;text-decoration:none}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.card{background:linear-gradient(180deg,var(--card),#0a1c18);border:1px solid var(--line);border-radius:11px;padding:17px}.matchNo{color:var(--gold);font-weight:800}.teams{font-size:25px;font-weight:800;margin:6px 0}.core{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px 0}.metric{background:var(--panel);border-radius:8px;padding:9px}.metric strong{display:block;color:var(--green);font-size:18px}.scorepool{display:flex;gap:8px;flex-wrap:wrap}.score{border:1px solid var(--line);border-radius:8px;padding:8px 10px;background:#0b201b}.score.main{border-color:var(--gold);color:var(--gold)}.tableWrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:760px}th,td{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--blue);background:#0b201b}.hit{color:var(--green);font-weight:800}.miss{color:var(--red);font-weight:800}.sources li{margin:7px 0}.archive{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.archive a{color:var(--text);text-decoration:none}.archive a:hover{border-color:var(--green)}footer{margin-top:30px;color:var(--muted);font-size:13px}@media(max-width:800px){.hero,.grid{display:block}.grid .card{margin-bottom:14px}.core,.archive{grid-template-columns:1fr}table{min-width:680px}}
"""


SOURCES = {
    "third": [
        {"label": "FOX/FanDuel季军赛公开赔率", "url": "https://www.foxsports.com/stories/soccer/2026-world-cup-third-place-odds-france-england"},
        {"label": "Oddschecker法国—英格兰聚合赔率", "url": "https://www.oddschecker.com/football/world-cup/france-v-england/winner"},
        {"label": "AP半决赛赛果与决赛对阵", "url": "https://apnews.com/article/argentina-messi-spain-yamal-world-cup-final-55077ce5c4728c4207a39cc4aa8a41a1"},
    ],
    "final": [
        {"label": "DraftKings决赛开盘", "url": "https://dknetwork.draftkings.com/2026/07/15/world-cup-2026-spain-vs-argentina-opening-odds/"},
        {"label": "bet365决赛公开赔率", "url": "https://news.bet365.com/en-gb/article/spain-v-argentina-odds-la-roja-favourites-to-win-world-cup-final/2026071521303757251"},
        {"label": "Oddschecker西班牙—阿根廷聚合赔率", "url": "https://www.oddschecker.com/football/world-cup/spain-v-argentina/winner"},
    ],
}


MATCHES = [
    {
        "no": "103", "date": "20260719", "round": "季军赛", "home": "法国", "away": "英格兰",
        "kickoff": "07-19 05:00", "local": "07-18 17:00（迈阿密花园，EDT）",
        "direction": "法国胜，防平", "probability": "法国胜49% / 平26% / 英格兰胜25%",
        "main_score": "2-1", "goals": "3球主线，防2/4球", "final_pick": "法国获得季军",
        "analysis": "公开盘约为法国2.00、平3.60-3.90、英格兰3.60-3.70，法国优势清楚但不是碾压。季军赛轮换和动机波动通常高于决赛，两队半决赛均失利后更可能释放进攻；法国本届进攻产量与公开盘共同支持2-1主线，1-1负责吸收轮换与疲劳，2-0保留法国重新建立防守控制的路径。",
        "script": "法国先球时2-1/2-0升权；英格兰先球时1-1/2-1/2-2升权；若双方大幅轮换且前30分钟已有进球，4球路径上调。",
        "odds": "公开90分钟：法国约2.00，平3.60-3.90，英格兰3.60-3.70；法国晋级/获季军约1.53。公开比分低位：2-1约9.50、1-1约8.00、2-0约14.00。",
        "score_pool": [
            {"score": "2-1", "prob": 18, "role": "主比分", "reason": "法国进攻上限与市场一球优势"},
            {"score": "1-1", "prob": 15, "role": "前三保护", "reason": "轮换、疲劳与英格兰反击"},
            {"score": "2-0", "prob": 12, "role": "前三保护", "reason": "法国恢复控场后的零封路线"},
            {"score": "3-1", "prob": 10, "role": "开放尾部", "reason": "季军赛早球与追分状态"},
            {"score": "1-0", "prob": 9, "role": "小球保护", "reason": "双方体能下降后效率走低"},
            {"score": "1-2", "prob": 8, "role": "反向保护", "reason": "英格兰先手后的法国追分风险"},
        ],
        "sources": SOURCES["third"],
    },
    {
        "no": "104", "date": "20260720", "round": "决赛", "home": "西班牙", "away": "阿根廷",
        "kickoff": "07-20 03:00", "local": "07-19 15:00（纽约/新泽西，EDT）",
        "direction": "西班牙胜，重点防平", "probability": "西班牙胜45% / 平31% / 阿根廷胜24%",
        "main_score": "1-0", "goals": "1/2球主线，防3球", "final_pick": "西班牙夺冠（59%）",
        "analysis": "DraftKings开盘西班牙+115、平+200、阿根廷+285，2.5球小球-135；bet365与Oddschecker也一致把西班牙放在90分钟优势位。西班牙连续淘汰葡萄牙、比利时和法国，半决赛再次验证控球脱压与零封能力；阿根廷对英格兰的两个后程进球说明其反击与定位球不能被降为极端尾部。主线为西班牙1-0，1-1承担决赛谨慎与阿根廷后程韧性，2-0是西班牙领先后继续控制的第三路径。",
        "script": "半场0-0时1-0/1-1/0-0升权；西班牙先球时1-0/2-0升权；阿根廷先球时1-1/1-2进入核心；前30分钟早球才把2-1与3球抬进主层。",
        "odds": "公开90分钟约：西班牙2.15-2.35，平3.00-3.15，阿根廷3.50-3.85；2.5球以下约1.61-1.74；捧杯西班牙约1.62、阿根廷约2.30。",
        "score_pool": [
            {"score": "1-0", "prob": 18, "role": "主比分", "reason": "西班牙市场优势与零封控制"},
            {"score": "1-1", "prob": 17, "role": "前三保护", "reason": "决赛谨慎与阿根廷后程韧性"},
            {"score": "2-0", "prob": 13, "role": "前三保护", "reason": "西班牙领先后持续压制"},
            {"score": "2-1", "prob": 12, "role": "双方进球", "reason": "阿根廷反击得分但西班牙兑现优势"},
            {"score": "0-0", "prob": 11, "role": "锁局保护", "reason": "前60分钟互相压缩"},
            {"score": "0-1", "prob": 9, "role": "反向零封", "reason": "阿根廷定位球或反击先手"},
            {"score": "1-2", "prob": 8, "role": "反向尾部", "reason": "西班牙追分后暴露转换空间"},
        ],
        "sources": SOURCES["final"],
    },
]


def update_semifinal_result() -> None:
    path = DATA / "20260716.json"
    payload = load(path)
    match = payload["matches"][0]
    match["matchStatus"] = "Finished"
    match["sellStatus"] = 1
    match["result"] = {
        "homeGoals": 1, "awayGoals": 2, "status": "Finished",
        "source": "user-confirmed + AP/public match reports", "advanced": "阿根廷",
    }
    match["postReview"] = "英格兰1-2阿根廷：原完整比分池包含1-2，但主比分1-1及按概率排序的前三（1-1/2-1/1-0）未覆盖正确比分；90分钟方向、总进球主线和晋级方向均未中。根因是把英格兰轻微低赔与体能优势放大为主排序，阿根廷的反击、定位球和后程终结能力虽被识别，却排位过低。永久修正：强强淘汰赛赔率差小于约0.60时，具备顶级转换与末段得分能力的名义客队小胜比分必须进入前三，而不是只留在完整尾池。"
    save(path, payload)

    lesson = {
        "date": "20260716",
        "headline": "英格兰1-2阿根廷复盘：识别反向路线不等于完成正确排序",
        "summary": "完整比分池覆盖1-2，但主比分及前三池未中，方向、总进球与晋级也未中。模型把英格兰轻微赔率与体能优势放大，令阿根廷后程得分路径只停留在低权重保护层。",
        "metrics": {"settled": 1, "direction_hits": 0, "main_score_hits": 0, "top3_score_pool_hits": 0, "full_score_pool_hits": 1, "total_goal_hits": 0},
        "lessons": [
            "比分池是否包含正确答案与前三排序是否有效必须分开计分，避免用大池命中掩盖主排序失真。",
            "当强强淘汰赛HAD差距很小，且名义客队拥有顶级转换、定位球与末段终结能力时，0-1/1-2至少一个必须进入前三池。",
            "连续两场半决赛均由名义客队取胜只说明赔率轻优不可被机械放大，不应直接外推为决赛继续追客胜。",
            "季军赛提高轮换、动机和开放度权重；决赛则继续分离90分钟方向与最终捧杯概率。",
        ],
        "weight_adjustments": {"odds": -0.02, "tactics": 0.02, "top3_away_small_win_trigger": 0.08, "full_pool_credit": -0.05},
        "validation": {"match_no": "102", "actual_score": "1-2", "direction_hit": False, "main_score_hit": False, "top3_score_pool_hit": False, "full_score_pool_hit": True, "total_goals_hit": False},
    }
    save(DATA / "model_review_lessons_20260716.json", lesson)

    state_path = ROOT / "model_state.json"
    state = load(state_path)
    state["updatedAt"] = "2026-07-16T10:30:00+08:00"
    state["weights"] = {"odds": 0.20, "elo": 0.18, "form": 0.15, "tactics": 0.22, "motivation": 0.12, "external": 0.09, "mystic": 0.04}
    state["calibration"] = {
        "latestReview": "20260716",
        "lesson": "102完整池覆盖1-2但前三池遗漏，需把强强对话名义客队小胜从尾部保护提升到前三排序。",
        "todayAdjustment": "103法国2-1，防1-1/2-0；104西班牙1-0，防1-1/2-0。连续客胜只校正排序，不机械追客。",
    }
    history = [x for x in state.get("history", []) if x.get("date") != "20260716"]
    history.append({"date": "20260716", "settled": 1, "directionHits": 0, "directionHitRate": "0%", "mainScoreHits": 0, "mainScoreHitRate": "0%", "scorePoolHits": 0, "scorePoolHitRate": "0%", "fullScorePoolHits": 1, "totalGoalHits": 0, "totalGoalHitRate": "0%"})
    state["history"] = history
    save(state_path, state)


def update_schedule() -> None:
    path = DATA / "knockout_schedule.json"
    payload = load(path)
    for match in payload["matches"]:
        no = str(match.get("match_no"))
        if no == "102":
            match["status"] = "已完赛：阿根廷2-1晋级"
        elif no == "103":
            match.update({"home_team": "法国", "home_team_en": "France", "home_code": "FRA", "away_team": "英格兰", "away_team_en": "England", "away_code": "ENG", "status": "未开赛"})
        elif no == "104":
            match.update({"home_team": "西班牙", "home_team_en": "Spain", "home_code": "ESP", "away_team": "阿根廷", "away_team_en": "Argentina", "away_code": "ARG", "status": "未开赛"})
    payload["last_updated"] = "2026-07-16"
    payload["update_note"] = "半决赛102回填英格兰1-2阿根廷；季军赛法国vs英格兰，决赛西班牙vs阿根廷。"
    save(path, payload)


def daily_payload(match: dict) -> dict:
    is_third = match["no"] == "103"
    public = {"home": "2.00", "draw": "3.75", "away": "3.70"} if is_third else {"home": "2.25", "draw": "3.05", "away": "3.70"}
    return {
        "date": match["date"], "dateText": f"2026-{match['date'][4:6]}-{match['date'][6:]}",
        "source": "public-odds-composite", "fetchedAt": "2026-07-16T10:20:00+08:00", "lastUpdateTime": UPDATED_AT,
        "apiPoolCode": "public-had,total,correct-score",
        "matches": [{
            "id": match["no"], "matchNumStr": f"待定{match['no']}", "league": "世界杯", "leagueCode": "WCC",
            "groupName": match["round"], "kickoff": f"2026-{match['date'][4:6]}-{match['date'][6:]} {match['kickoff'].split()[-1]}:00",
            "matchDate": f"2026-{match['date'][4:6]}-{match['date'][6:]}", "matchStatus": "NotStarted",
            "home": match["home"], "away": match["away"],
            "prediction": {"totalGoals": "3" if is_third else "1/2", "scores": [x["score"].replace("-", ":") for x in match["score_pool"]], "upset": "1:2" if is_third else "0:1", "confidence": "中高", "candidates": ["3", "2", "4"] if is_third else ["1", "2", "3"]},
            "result": None, "review": match["analysis"], "postReview": None,
            "odds": {"had": {**public, "updatedAt": UPDATED_AT}, "ttg": {"line": "3.5", "under": "1.67", "over": "2.27", "updatedAt": UPDATED_AT} if is_third else {"line": "2.5", "under": "1.68", "over": "2.45", "updatedAt": UPDATED_AT}, "crs": {x["score"]: str(round(1 / (x["prob"] / 100), 2)) for x in match["score_pool"]}, "sourceNote": "体彩赔率未出，采用FOX/FanDuel、DraftKings、bet365与Oddschecker公开盘综合快照。"},
        }],
    }


def prediction_page(match: dict) -> str:
    scores = "".join(f"<span class='score {'main' if i == 0 else ''}'><strong>{e(x['score'])}</strong> · {x['prob']}%<br><small>{e(x['role'])}</small></span>" for i, x in enumerate(match["score_pool"]))
    source_items = "".join(f"<li><a href='{e(x['url'])}'>{e(x['label'])}</a></li>" for x in match["sources"])
    return f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{e(match['round'])} {e(match['home'])}vs{e(match['away'])}预测</title><style>{CSS}</style></head><body><main>
<header class='hero'><div><span class='matchNo'>{e(match['round'])} {e(match['no'])}｜北京时间 {e(match['kickoff'])}</span><h1>{e(match['home'])} vs {e(match['away'])}</h1><p>当地时间 {e(match['local'])}；体彩赔率未出，本页使用公开赔率综合快照。</p><div class='chips'><a class='chip' href='../index.html'>首页</a><a class='chip' href='../parlay/'>二串一</a><a class='chip' href='../accuracy/'>历史准确率</a></div></div></header>
<section class='card'><div class='core'><div class='metric'>90分钟<strong>{e(match['direction'])}</strong></div><div class='metric'>主比分<strong>{e(match['main_score'])}</strong></div><div class='metric'>总进球<strong>{e(match['goals'])}</strong></div></div><p><strong>最终判断：</strong>{e(match['final_pick'])}</p><p>{e(match['analysis'])}</p></section>
<h2>主比分与比分池</h2><section class='card'><div class='scorepool'>{scores}</div><p>准确率页面固定以主比分和概率排序前三进行赛后比对；完整池用于解释场景，不用大池命中替代前三命中。</p></section>
<h2>比赛脚本</h2><section class='card'><p>{e(match['script'])}</p><p><strong>公开赔率：</strong>{e(match['odds'])}</p></section>
<h2>公开来源</h2><section class='card'><ul class='sources'>{source_items}</ul></section><footer>{DISCLAIMER}</footer></main></body></html>"""


def write_match_outputs() -> None:
    for match in MATCHES:
        save(DATA / f"{match['date']}.json", daily_payload(match))
        save(DATA / f"final_stage_prediction_{match['no']}_20260716.json", {"date": match["date"], "stage": match["round"], "matches": [match], "generatedAt": UPDATED_AT, "source": "public odds composite; Sporttery not available"})
        page = prediction_page(match)
        folder = ROOT / match["date"]
        write(folder / "index.html", page)
        write(folder / f"predict_{match['date']}.html", page)


def review_page() -> str:
    lesson = load(DATA / "model_review_lessons_20260716.json")
    lis = "".join(f"<li>{e(x)}</li>" for x in lesson["lessons"])
    return f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>102 英格兰1-2阿根廷复盘</title><style>{CSS}</style></head><body><main><span class='matchNo'>半决赛102｜已结束</span><h1>英格兰 1-2 阿根廷</h1><div class='chips'><a class='chip' href='../index.html'>首页</a><a class='chip' href='../20260719/'>季军赛</a><a class='chip' href='../20260720/'>决赛</a></div><section class='card'><div class='core'><div class='metric'>方向/晋级<strong>未命中</strong></div><div class='metric'>主比分/前三池<strong>未命中</strong></div><div class='metric'>完整池<strong>覆盖1-2</strong></div></div><p>{e(lesson['summary'])}</p><ul>{lis}</ul></section><footer>{DISCLAIMER}</footer></main></body></html>"""


def score_norm(value: str) -> str:
    return str(value).replace(":", "-").strip()


def score_direction(score: str) -> str:
    try:
        a, b = [int(x) for x in score_norm(score).split("-")]
    except Exception:
        return ""
    return "主胜" if a > b else "平" if a == b else "客胜"


def total_goal_hit(prediction: str, actual: int) -> bool:
    values = {int(x) for x in re.findall(r"\d+", str(prediction))}
    return actual in values or (7 in values and actual >= 7)


def build_accuracy() -> tuple[dict, str]:
    special = {}
    for path in sorted(DATA.glob("*prediction*.json")):
        try:
            payload = load(path)
        except Exception:
            continue
        for match in payload.get("matches", []):
            no = str(match.get("no", match.get("id", ""))).lstrip("0") or "0"
            if match.get("main_score") and match.get("score_pool"):
                special[no] = {"main": score_norm(match["main_score"]), "pool": [score_norm(x["score"]) for x in match["score_pool"][:3]]}

    rows = []
    seen = set()
    for path in sorted(DATA.glob("2026????.json")):
        try:
            payload = load(path)
        except Exception:
            continue
        for match in payload.get("matches", []):
            result = match.get("result")
            if not result or result.get("homeGoals") is None or result.get("awayGoals") is None:
                continue
            if match.get("excludeFromModel") or result.get("excludeFromModel"):
                continue
            key = (path.stem, str(match.get("id")), match.get("home"), match.get("away"))
            if key in seen:
                continue
            seen.add(key)
            actual = f"{int(result['homeGoals'])}-{int(result['awayGoals'])}"
            pred = match.get("prediction") or {}
            no = str(match.get("id", "")).lstrip("0") or "0"
            if no in special:
                main, pool = special[no]["main"], special[no]["pool"]
            else:
                scores = [score_norm(x) for x in pred.get("scores", [])]
                main = scores[0] if scores else "—"
                candidates = scores + ([score_norm(pred["upset"])] if pred.get("upset") else [])
                pool = []
                for score in candidates:
                    if score not in pool:
                        pool.append(score)
                pool = pool[:3]
            main_hit = main == actual
            pool_hit = actual in pool
            direction_hit = score_direction(main) == score_direction(actual)
            goals_hit = total_goal_hit(pred.get("totalGoals", ""), int(result["homeGoals"]) + int(result["awayGoals"]))
            rows.append({"date": path.stem, "no": str(match.get("id", "")), "match": f"{match.get('home')} vs {match.get('away')}", "main_score": main, "top3_pool": pool, "actual": actual, "main_hit": main_hit, "top3_hit": pool_hit, "direction_hit": direction_hit, "total_goals_hit": goals_hit})

    total = len(rows)
    metrics = {
        "settled": total,
        "main_score_hits": sum(x["main_hit"] for x in rows),
        "top3_score_pool_hits": sum(x["top3_hit"] for x in rows),
        "main_direction_hits": sum(x["direction_hit"] for x in rows),
        "total_goal_hits": sum(x["total_goals_hit"] for x in rows),
    }
    for key in ("main_score", "top3_score_pool", "main_direction", "total_goal"):
        metrics[f"{key}_rate"] = f"{metrics[f'{key}_hits'] / total * 100:.1f}%" if total else "—"
    summary = {"updatedAt": UPDATED_AT, "method": "主比分取赛前主推；比分池取赛前概率排序前三。若早期记录仅有两项scores，则用upset补足第三项。赛果按90分钟比分比较；明确标记excludeFromModel的特殊比赛不进入模型准确率与校准。", "metrics": metrics, "matches": rows}
    save(DATA / "accuracy_summary_20260716.json", summary)

    table_rows = "".join(
        f"<tr><td>{e(x['date'])}</td><td>{e(x['no'])}</td><td>{e(x['match'])}</td><td>{e(x['main_score'])}<br><span class='{'hit' if x['main_hit'] else 'miss'}'>{'命中' if x['main_hit'] else '未中'}</span></td><td>{e(' / '.join(x['top3_pool']))}<br><span class='{'hit' if x['top3_hit'] else 'miss'}'>{'命中' if x['top3_hit'] else '未中'}</span></td><td><strong>{e(x['actual'])}</strong></td></tr>"
        for x in reversed(rows)
    )
    page = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>世界杯预测准确率</title><style>{CSS}</style></head><body><main><header class='hero'><div><h1>世界杯预测准确率</h1><p>汇总项目内全部已有赛果的世界杯预测记录；统一按90分钟正确比分结算。</p><div class='chips'><a class='chip' href='../index.html'>返回首页</a><span class='chip'>更新时间 {UPDATED_AT}</span></div></div></header><section class='card'><div class='core'><div class='metric'>已结算<strong>{total}场</strong></div><div class='metric'>主比分<strong>{metrics['main_score_hits']}/{total} · {metrics['main_score_rate']}</strong></div><div class='metric'>比分池前三<strong>{metrics['top3_score_pool_hits']}/{total} · {metrics['top3_score_pool_rate']}</strong></div></div><div class='core'><div class='metric'>主比分方向<strong>{metrics['main_direction_hits']}/{total} · {metrics['main_direction_rate']}</strong></div><div class='metric'>总进球<strong>{metrics['total_goal_hits']}/{total} · {metrics['total_goal_rate']}</strong></div><div class='metric'>结算口径<strong>90分钟</strong></div></div><p>{e(summary['method'])}</p></section><h2>逐场对比</h2><section class='card tableWrap'><table><thead><tr><th>日期</th><th>场次</th><th>对阵</th><th>主比分</th><th>比分池前三</th><th>正确比分</th></tr></thead><tbody>{table_rows}</tbody></table></section><footer>{DISCLAIMER}</footer></main></body></html>"""
    return summary, page


def write_hubs(accuracy: dict) -> None:
    third, final = MATCHES
    root_page = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>2026 世界杯决赛阶段预测</title><style>{CSS}</style></head><body><main><header class='hero'><div><h1>季军赛与冠亚军赛预测</h1><p>半决赛赛果：法国0-2西班牙；英格兰1-2阿根廷。体彩赔率尚未发布，当前结论使用公开赔率综合盘。</p><div class='chips'><span class='chip'>更新 {UPDATED_AT}</span><span class='chip'>半决赛已复盘</span><span class='chip'>103/104公开盘</span></div></div><a class='chip' href='./parlay/'>查看二串一 →</a></header><h2>两场核心结论</h2><section class='grid'><a class='card' href='./20260719/' style='color:inherit;text-decoration:none'><span class='matchNo'>季军赛103｜07-19 05:00</span><div class='teams'>法国 vs 英格兰</div><div class='core'><div class='metric'>90分钟<strong>法国胜，防平</strong></div><div class='metric'>主比分<strong>2-1</strong></div><div class='metric'>总进球<strong>3球</strong></div></div><p>前三比分：2-1 / 1-1 / 2-0。公开盘法国约2.00，优势明确但需防轮换波动。</p></a><a class='card' href='./20260720/' style='color:inherit;text-decoration:none'><span class='matchNo'>决赛104｜07-20 03:00</span><div class='teams'>西班牙 vs 阿根廷</div><div class='core'><div class='metric'>90分钟<strong>西班牙胜，防平</strong></div><div class='metric'>主比分<strong>1-0</strong></div><div class='metric'>捧杯<strong>西班牙59%</strong></div></div><p>前三比分：1-0 / 1-1 / 2-0。公开盘一致支持西班牙与2.5球以下。</p></a></section><h2>半决赛复盘</h2><section class='grid'><a class='card' href='./20260715/' style='color:inherit;text-decoration:none'><h3>法国0-2西班牙</h3><p>总进球命中，方向与比分池漏掉0-2；已增加顶级名义客队零封触发器。</p></a><a class='card' href='./20260716/' style='color:inherit;text-decoration:none'><h3>英格兰1-2阿根廷</h3><p>完整池有1-2，但主比分及前三池未中；修正反向小胜排序权重。</p></a></section><h2>功能入口</h2><section class='archive'><a class='card' href='./accuracy/'><strong>历史准确率</strong><p>{accuracy['metrics']['settled']}场逐场比较主比分、前三池与正确比分。</p></a><a class='card' href='./parlay/'><strong>二串一</strong><p>胜平负、总进球、两组比分组合。</p></a><a class='card' href='./knockout/'><strong>淘汰赛归档</strong><p>半决赛复盘及决赛阶段入口。</p></a><a class='card' href='./group/'><strong>小组赛归档</strong><p>历史每日预测页面。</p></a></section><footer>{DISCLAIMER}</footer></main></body></html>"""
    write(ROOT / "index.html", root_page)

    parlay = {
        "date": "20260716", "stage": "final_stage_two_leg", "title": "季军赛+决赛二串一",
        "source": "public odds composite; Sporttery not yet available",
        "combinations": {
            "win_draw_loss": ["103 法国胜", "104 西班牙胜"],
            "total_goals": ["103 总进球3球", "104 总进球1/2球"],
            "correct_score_two_options": [
                ["103 法国2-1英格兰", "104 西班牙1-0阿根廷"],
                ["103 法国1-1英格兰", "104 西班牙1-1阿根廷"],
            ],
        },
        "risk": "精确比分二串一波动极高；季军赛轮换和决赛早球都会显著改变比赛脚本。",
        "disclaimer": DISCLAIMER,
    }
    save(DATA / "final_stage_parlay_20260716.json", parlay)
    parlay_page = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>世界杯决赛阶段二串一</title><style>{CSS}</style></head><body><main><h1>季军赛 + 决赛二串一</h1><p>体彩赔率未出，按公开赔率与复盘后模型生成；所有选项均按90分钟赛果。</p><div class='chips'><a class='chip' href='../index.html'>首页</a><a class='chip' href='../accuracy/'>历史准确率</a></div><section class='grid'><div class='card'><h3>胜平负二串一</h3><p><strong>法国胜 × 西班牙胜</strong></p><p>防守版：法国胜或平 × 西班牙胜或平。</p></div><div class='card'><h3>总进球二串一</h3><p><strong>法国—英格兰 3球 × 西班牙—阿根廷 1/2球</strong></p><p>季军赛防2/4球；决赛防3球。</p></div><div class='card'><h3>比分二串一 A</h3><p><strong>法国2-1英格兰 × 西班牙1-0阿根廷</strong></p><p>两场主比分组合。</p></div><div class='card'><h3>比分二串一 B</h3><p><strong>法国1-1英格兰 × 西班牙1-1阿根廷</strong></p><p>两场平局保护组合。</p></div></section><section class='card'><p class='miss'>精确比分二串一波动极高，不用完整比分池命中替代主推组合的真实表现。</p></section><footer>{DISCLAIMER}</footer></main></body></html>"""
    write(ROOT / "parlay" / "index.html", parlay_page)

    knockout_page = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>2026 世界杯淘汰赛归档</title><style>{CSS}</style></head><body><main><h1>淘汰赛决赛阶段</h1><p>两场半决赛已结束；103/104使用公开赔率预测。</p><div class='chips'><a class='chip' href='../index.html'>首页</a><a class='chip' href='../accuracy/'>历史准确率</a></div><section class='card tableWrap'><table><thead><tr><th>轮次</th><th>北京时间</th><th>对阵</th><th>状态/预测</th><th>入口</th></tr></thead><tbody><tr><td>半决赛101</td><td>已结束</td><td>法国0-2西班牙</td><td>西班牙晋级</td><td><a href='../20260715/'>复盘</a></td></tr><tr><td>半决赛102</td><td>已结束</td><td>英格兰1-2阿根廷</td><td>阿根廷晋级</td><td><a href='../20260716/'>复盘</a></td></tr><tr><td>季军赛103</td><td>07-19 05:00</td><td>法国 vs 英格兰</td><td>法国胜；2-1</td><td><a href='../20260719/'>预测</a></td></tr><tr><td>决赛104</td><td>07-20 03:00</td><td>西班牙 vs 阿根廷</td><td>西班牙胜；1-0</td><td><a href='../20260720/'>预测</a></td></tr></tbody></table></section><footer>{DISCLAIMER}</footer></main></body></html>"""
    write(ROOT / "knockout" / "index.html", knockout_page)


def main() -> None:
    update_semifinal_result()
    update_schedule()
    write_match_outputs()
    review = review_page()
    folder = ROOT / "20260716"
    write(folder / "index.html", review)
    write(folder / "predict_20260716.html", review)
    write(folder / "review.html", review)
    accuracy, accuracy_page = build_accuracy()
    write(ROOT / "accuracy" / "index.html", accuracy_page)
    write_hubs(accuracy)
    print(json.dumps({"updated": ["102 review", "103 prediction", "104 prediction", "parlay", "accuracy", "homepage"], "accuracy": accuracy["metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
