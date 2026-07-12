#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DISCLAIMER = "以上仅为公开信息整理后的娱乐分析，不构成任何购彩建议，请理性参考。"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def esc(value):
    return html.escape(str(value), quote=True)


def set_result(date: str, no: str, score: tuple[int, int], review: str, extra=None):
    path = DATA / f"{date}.json"
    payload = load(path)
    for match in payload["matches"]:
        if str(match.get("id", "")).lstrip("0") == no:
            match["matchStatus"] = "Finished"
            match["result"] = {"homeGoals": score[0], "awayGoals": score[1], "status": "Finished", "source": "user-confirmed"}
            if extra:
                match["result"].update(extra)
            match["postReview"] = review
            break
    save(path, payload)


def css():
    return """
:root{--bg:#071310;--card:#10221f;--panel:#142b27;--line:#285046;--text:#effbf7;--muted:#9dbab1;--green:#62d899;--gold:#f3c45e;--blue:#72c8ff;--red:#ff8580}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:'Microsoft YaHei','PingFang SC',Arial,sans-serif;line-height:1.65}header,main{max-width:1180px;margin:auto;padding:20px}nav{display:flex;gap:9px;flex-wrap:wrap}nav a{color:var(--text);text-decoration:none;border:1px solid var(--line);padding:6px 10px;border-radius:8px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:14px 0}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px}.metric strong{display:block;color:var(--green);font-size:22px}.muted{color:var(--muted)}.gold{color:var(--gold)}.red{color:var(--red)}table{border-collapse:collapse;width:100%}th,td{text-align:left;vertical-align:top;padding:9px;border-bottom:1px solid var(--line)}th{color:var(--blue)}.tableWrap{overflow:auto}.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 8px;margin:3px}footer{color:var(--muted);margin-top:22px}@media(max-width:820px){.grid,.cols{grid-template-columns:1fr}table{min-width:680px}}
"""


def match_card(m):
    odds = m["odds"]
    rows = "".join(f"<tr><td>{esc(x['score'])}</td><td>{x['prob']}%</td><td>{esc(x['role'])}</td><td>{esc(x['reason'])}</td></tr>" for x in m["score_pool"])
    sources = "".join(f"<li><a href='{esc(x['url'])}'>{esc(x['label'])}</a></li>" for x in m["sources"])
    return f"""<section class='card'><h2>{m['no']} {m['home']} vs {m['away']}</h2>
<div class='grid'><div class='metric'>北京时间<strong>{m['kickoff']}</strong><small>当地时间 {m['local']}</small></div><div class='metric'>90分钟<strong>{m['direction']}</strong><small>{m['probability']}</small></div><div class='metric'>主比分<strong>{m['main_score']}</strong><small>总进球 {m['goals']}</small></div><div class='metric'>最终晋级<strong>{m['advance']}</strong><small>{m['advance_prob']}</small></div></div>
<div class='cols'><div class='panel'><h3>模型判断</h3><p>{m['analysis']}</p><p><b>比赛脚本：</b>{m['script']}</p></div><div class='panel'><h3>赔率快照</h3><p>{odds}</p><p class='muted'>赔率只用于概率校准，抓取时间与来源均保留；临场变化需重新审计。</p></div></div>
<div class='tableWrap'><table><thead><tr><th>比分</th><th>模型概率</th><th>角色</th><th>场景</th></tr></thead><tbody>{rows}</tbody></table></div>
<p><b>爆冷：</b><span class='red'>{m['upset']}</span>　<b>半全场：</b>{m['hafu']}　<b>体能/伤停：</b>{m['fitness']}</p>
<details><summary>数据与赔率来源</summary><ul>{sources}</ul></details></section>"""


def page(title, intro, matches, extra=""):
    cards = "".join(match_card(m) for m in matches)
    return f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{esc(title)}</title><style>{css()}</style></head><body><header><h1>{esc(title)}</h1><p>{esc(intro)}</p><nav><a href='../knockout/'>淘汰赛归档</a><a href='../parlay/'>两场串关</a></nav></header><main>{extra}{cards}<footer>{DISCLAIMER}</footer></main></body></html>"""


def main():
    homepage_before = hashlib.sha256((ROOT / "index.html").read_bytes()).hexdigest()

    reviews = {
        "97": "法国2-0摩洛哥：方向、2球和2-0主比分全中。强队控场且对手进攻受限时，零封小胜应高于泛化的淘汰赛平局保护。",
        "98": "西班牙2-1比利时：方向、3球和2-1主比分全中。均衡强强对话仍可由更稳定一方在末段兑现，2-1应保留为核心小胜路径。",
        "99": "挪威1-1英格兰，英格兰加时2-1晋级：90分钟平局保护与最终晋级命中，主比分1-2未中。淘汰赛必须持续分离90分钟与晋级市场。",
        "100": "阿根廷1-1瑞士，阿根廷加时后3-1晋级：1-1防冷与晋级方向命中，主线小胜未中。锁局型对手拖入加时后，强队的体能和替补深度仍可能拉开最终比分。",
    }
    set_result("20260710", "97", (2, 0), reviews["97"])
    set_result("20260711", "98", (2, 1), reviews["98"])
    set_result("20260712", "99", (1, 1), reviews["99"], {"extraTimeScore": "1-2", "advanced": "英格兰"})
    set_result("20260712", "100", (1, 1), reviews["100"], {"extraTimeScore": "3-1", "advanced": "阿根廷", "inferenceNote": "用户未明示90分钟比分；依据进入加时及公开赛况按1-1归档"})

    schedule_path = DATA / "knockout_schedule.json"
    schedule = load(schedule_path)
    updates = {
        "97": ("已完赛：法国2-0晋级",), "98": ("已完赛：西班牙2-1晋级",),
        "99": ("已完赛：1-1，英格兰加时2-1晋级",), "100": ("已完赛：1-1，阿根廷加时后3-1晋级",),
        "101": ("未开赛", "法国", "France", "FRA", "西班牙", "Spain", "ESP"),
        "102": ("未开赛", "英格兰", "England", "ENG", "阿根廷", "Argentina", "ARG"),
        "103": ("未开赛", "法国/西班牙负者", "Loser of France/Spain", "", "英格兰/阿根廷负者", "Loser of England/Argentina", ""),
        "104": ("未开赛", "法国/西班牙胜者", "Winner of France/Spain", "", "英格兰/阿根廷胜者", "Winner of England/Argentina", ""),
    }
    for m in schedule["matches"]:
        no = str(m["match_no"])
        if no in updates:
            u = updates[no]
            m["status"] = u[0]
            if len(u) > 1:
                m.update(home_team=u[1], home_team_en=u[2], home_code=u[3], away_team=u[4], away_team_en=u[5], away_code=u[6])
    schedule["last_updated"] = "2026-07-12"
    schedule["update_note"] = "四分之一决赛全部回填；四强确认为法国、西班牙、英格兰、阿根廷；半决赛101/102对阵已落位。"
    save(schedule_path, schedule)

    sporttery = load(DATA / "20260715.json")["matches"][0]
    o = sporttery["odds"]
    matches = [
        {"no":"101","home":"法国","away":"西班牙","kickoff":"07-15 03:00","local":"07-14 15:00（阿灵顿）","direction":"法国胜，防平","probability":"法国胜45% / 平30% / 西班牙胜25%","main_score":"2-1","goals":"2/3球","advance":"法国","advance_prob":"法国60% / 西班牙40%","upset":"西班牙1-0或1-2","hafu":"平胜 / 胜胜，防平负","fitness":"法国多休一天；西班牙末段消耗较大，临场首发待复核。","analysis":"竞彩2.26/3.10/2.75与公开盘均把法国放在轻微优势位。法国本届攻击上限更高，西班牙则以控球和低失球压缩波动。四分之一决赛验证两队都能在90分钟兑现，因此不机械追平，主线放在法国2-1，保留1-1和西班牙偷球路径。","script":"半场僵持时1-1与平胜升权；法国先球则2-0/2-1升权；西班牙先球则1-1/1-2进入核心。","odds":f"竞彩HAD {o['had']['home']}/{o['had']['draw']}/{o['had']['away']}；总进球2球 {o['ttg']['s2']}、3球 {o['ttg']['s3']}；比分1-1 {o['crs']['1-1']}、2-1 {o['crs']['2-1']}、1-2 {o['crs']['1-2']}；更新时间 {o['had']['updatedAt']}。公开盘：法国+135、平+225、西班牙+215，法国晋级-145。","score_pool":[{"score":"2-1","prob":17,"role":"主推","reason":"法国进攻上限与末段深度"},{"score":"1-1","prob":16,"role":"稳健保护","reason":"强强对话互相压缩"},{"score":"1-0","prob":12,"role":"小球保护","reason":"法国控场零封"},{"score":"1-2","prob":11,"role":"爆冷","reason":"西班牙控球后程兑现"},{"score":"2-0","prob":9,"role":"尾部","reason":"法国早球后控制"},{"score":"0-1","prob":8,"role":"冷门尾部","reason":"西班牙低比分偷球"}],"sources":[{"label":"中国竞彩官方接口快照","url":"https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c&poolCode=ttg,had,hhad,crs,hafu"},{"label":"DraftKings Network开盘信息","url":"https://dknetwork.draftkings.com/2026/07/11/world-cup-2026-france-vs-spain-opening-odds/"},{"label":"BetUS半决赛赔率页","url":"https://www.betus.com.pa/sportsbook/fifa/world-cup/france-vs-spain/"}]},
        {"no":"102","home":"英格兰","away":"阿根廷","kickoff":"07-16 03:00","local":"07-15 15:00（亚特兰大）","direction":"平局优先，阿根廷不败","probability":"英格兰胜30% / 平34% / 阿根廷胜36%","main_score":"1-1","goals":"2/3球","advance":"阿根廷","advance_prob":"英格兰45% / 阿根廷55%","upset":"英格兰2-1","hafu":"平平 / 平负，防胜胜","fitness":"两队均打加时；阿根廷下半区最后出赛，恢复时间更短。","analysis":"102竞彩细项尚未开盘，模型不填造赔率。英格兰连续两轮暴露防线但有替补深度，阿根廷两轮都靠后程和加时提升强度。双方加时消耗叠加，90分钟平局权重上调；阿根廷关键球能力略优，最终晋级小幅倾向阿根廷。","script":"0-0半场时1-1/0-1升权；英格兰先球则2-1和2-2升权；阿根廷先球则0-1/1-2升权。","odds":"中国竞彩接口截至2026-07-12 11:58未返回20260716场次；仅使用赛程、已确认赛果、公开球队表现与四强市场排序，待开盘后复核。","score_pool":[{"score":"1-1","prob":18,"role":"主推","reason":"双方加时消耗与淘汰赛控制"},{"score":"1-2","prob":14,"role":"客胜主线","reason":"阿根廷后程关键球"},{"score":"2-1","prob":13,"role":"爆冷","reason":"英格兰替补深度和定位球"},{"score":"0-1","prob":10,"role":"小球保护","reason":"阿根廷低比分管理"},{"score":"2-2","prob":9,"role":"尾部","reason":"双方防线均有失球路径"},{"score":"0-0","prob":7,"role":"锁局保护","reason":"体能导致前段保守"}],"sources":[{"label":"AP：阿根廷与瑞士90分钟1-1及半决赛路径","url":"https://apnews.com/article/d47ccb4ac5b3af67eca1f82228155174"},{"label":"Oddschecker半决赛赛程市场页","url":"https://www.oddschecker.com/football/world-cup/france-v-spain/winner"},{"label":"项目竞彩接口（102暂未开盘）","url":"https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c&poolCode=ttg,had,hhad,crs,hafu"}]},
    ]

    review = {"date":"20260712","stage":"quarterfinal_review","results":[{"match_no":k,"review":v} for k,v in reviews.items()],"metrics":{"settled":4,"direction_hits":4,"direction_hit_rate":"100%","main_score_hits":2,"main_score_hit_rate":"50%","score_pool_hits":4,"score_pool_hit_rate":"100%","total_goal_hits":3,"total_goal_hit_rate":"75%"},"model_changes":["90分钟与晋级继续拆分计分；99/100证明两者可同时正确。","强强对话不因淘汰赛自动追平：97/98均在90分钟由优势方兑现。","连续加时球队的恢复时间单独进入半决赛体能项；102双方加时，阿根廷少一天恢复。","比分池维持主线、平局保护、小胜、爆冷与尾部五层，不用昨日大小球机械外推。"]}
    save(DATA / "model_review_lessons_20260712.json", review)

    state = load(ROOT / "model_state.json")
    state["updatedAt"] = "2026-07-12T12:00:00+08:00"
    state["weights"] = {"odds":0.22,"elo":0.18,"form":0.14,"tactics":0.18,"motivation":0.13,"external":0.11,"mystic":0.04}
    state["calibration"] = {"latestReview":"20260712","lesson":"八强方向4/4、主比分2/4、比分池4/4、总进球3/4；继续拆分90分钟与晋级，强强对话不机械追平，连续加时恢复差单列。","todayAdjustment":"101法国轻优主2-1防1-1/1-2；102双方加时且阿根廷少休一天，90分钟主1-1，晋级阿根廷小幅领先。"}
    state["history"] = [x for x in state["history"] if x.get("date") != "20260712"]
    state["history"].append({"date":"20260712","settled":4,"directionHits":4,"directionHitRate":"100%","mainScoreHits":2,"mainScoreHitRate":"50%","scorePoolHits":4,"scorePoolHitRate":"100%","totalGoalHits":3,"totalGoalHitRate":"75%"})
    save(ROOT / "model_state.json", state)

    for m in matches:
        payload = {"date":"20260715" if m["no"]=="101" else "20260716","stage":"semifinal","matches":[m],"generatedAt":"2026-07-12 12:00 +08:00"}
        save(DATA / f"semifinal_prediction_{m['no']}_20260712.json", payload)
        if m["no"] == "102":
            save(DATA / "20260716.json", {"date":"20260716","dateText":"2026-07-16","source":"schedule-model-odds-pending","fetchedAt":"2026-07-12T11:58:00+08:00","apiPoolCode":"ttg,had,hhad,crs,hafu","matches":[{"id":"102","matchNumStr":"待定102","league":"世界杯","leagueCode":"WCC","kickoff":"2026-07-16 03:00:00","matchDate":"2026-07-16","matchStatus":"OddsPending","home":"英格兰","away":"阿根廷","prediction":{"totalGoals":"2/3","scores":["1:1","1:2","2:1","0:1","2:2","0:0"],"upset":"2:1","confidence":"中低"},"result":None,"review":"Sporttery 20260716未开盘；按已确认赛程、八强赛果、体能与模型经验生成，占位赔率不得视为实时盘。","odds":{"had":None,"ttg":None,"hhad":None,"crs":None,"hafu":None}}]})
        folder = ROOT / payload["date"]
        folder.mkdir(exist_ok=True)
        text = page(f"世界杯半决赛 {m['no']}", "四强确认后的独立赛前预测；90分钟方向与最终晋级分开。", [m])
        (folder / "index.html").write_text(text, encoding="utf-8")
        (folder / f"predict_{payload['date']}.html").write_text(text, encoding="utf-8")

    parlay = {"date":"20260712","stage":"semifinal_two_leg","title":"半决赛两场串","legs":[{"match_no":"101","match":"法国 vs 西班牙","win_draw_loss":"法国胜，防平","total_goals":"2/3球","scores":"2-1 / 1-1 / 1-0","upset":"西班牙1-2","confidence":"中"},{"match_no":"102","match":"英格兰 vs 阿根廷","win_draw_loss":"平局优先，阿根廷不败","total_goals":"2/3球","scores":"1-1 / 1-2 / 2-1","upset":"英格兰2-1","confidence":"中低；竞彩待开盘"}],"combination":{"main":"101法国胜或平 + 102平或阿根廷胜","goals":"101 2/3球 + 102 2/3球","scores":"101 2-1/1-1 + 102 1-1/1-2","upset":"101西班牙1-2 + 102英格兰2-1"},"risk":"两场均为高强度半决赛，精确比分波动大；102赔率未开盘，必须临场复核。","disclaimer":DISCLAIMER}
    save(DATA / "semifinal_parlay_20260712.json", parlay)
    parlay_html = f"""<section class='card'><h2>两场串关模型组合</h2><div class='cols'><div class='panel'><h3>主线</h3><p>{parlay['combination']['main']}</p><p>总进球：{parlay['combination']['goals']}</p></div><div class='panel'><h3>比分 / 爆冷</h3><p>{parlay['combination']['scores']}</p><p class='red'>{parlay['combination']['upset']}</p></div></div><p class='gold'>{parlay['risk']}</p></section>"""
    (ROOT / "parlay" / "index.html").write_text(page("世界杯半决赛两场串", "包含胜平负、总进球、比分与爆冷四层组合。", matches, parlay_html), encoding="utf-8")

    review_html = "".join(f"<li><b>{k}</b> {v}</li>" for k,v in reviews.items())
    archive_intro = f"<section class='card'><h2>四分之一决赛归档与模型复盘</h2><ul>{review_html}</ul><p><b>本轮：</b>方向4/4、主比分2/4、比分池4/4、总进球3/4。</p></section>"
    knockout = page("2026 世界杯淘汰赛归档", "四分之一决赛已全部归档；四强与半决赛路径已确认。", matches, archive_intro)
    (ROOT / "knockout" / "index.html").write_text(knockout, encoding="utf-8")

    outright = {"date":"20260712","source":"semifinal bracket model calibrated by Sporttery 101 and public market hierarchy","updatedAt":"2026-07-12 12:00 +08:00","odds":[{"team":"法国","decimal":2.45,"model_probability":0.39},{"team":"阿根廷","decimal":4.00,"model_probability":0.24},{"team":"西班牙","decimal":4.50,"model_probability":0.21},{"team":"英格兰","decimal":5.50,"model_probability":0.16}],"method":"法国-西班牙使用竞彩与公开盘；英格兰-阿根廷竞彩未开盘，按模型晋级率与公开四强市场排序归一化。赔率为模型公平价展示，不是庄家实时报价。","note":DISCLAIMER}
    save(DATA / "outright_odds_20260712.json", outright)

    homepage_after = hashlib.sha256((ROOT / "index.html").read_bytes()).hexdigest()
    if homepage_before != homepage_after:
        raise RuntimeError("首页发生变化，违反用户要求")
    print("updated semifinal predictions, review, bracket, parlay; root homepage unchanged")


if __name__ == "__main__":
    main()
