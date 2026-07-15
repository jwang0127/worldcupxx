#!/usr/bin/env python3
from __future__ import annotations

from update_semifinals_20260712 import DATA, ROOT, DISCLAIMER, css, esc, load, page, save
from refresh_102_odds_20260714 import main as refresh_102


def main() -> None:
    # First regenerate 102 from the latest Sporttery file with the new 0-2 lesson.
    refresh_102()

    p101 = DATA / "20260715.json"
    daily101 = load(p101)
    match101 = daily101["matches"][0]
    match101["matchStatus"] = "Finished"
    match101["result"] = {"homeGoals":0,"awayGoals":2,"status":"Finished","source":"user-confirmed + public match reports","advanced":"西班牙"}
    match101["postReview"] = "法国0-2西班牙：总进球2球命中；90分钟方向、主比分和晋级方向均未中，原比分池也遗漏0-2。模型过度依赖法国轻微低赔和进攻上限，低估西班牙连续不败、控球脱压和零封客胜路径。永久修正：当名义客队具备顶级防守与控球能力时，即使HAD略处下风，也必须把0-1/0-2与1-2并列纳入反向核心池。"
    save(p101, daily101)

    schedule_path = DATA / "knockout_schedule.json"
    schedule = load(schedule_path)
    for m in schedule["matches"]:
        no = str(m["match_no"])
        if no == "101": m["status"] = "已完赛：西班牙0-2晋级"
        elif no == "103": m.update(home_team="法国",home_team_en="France",home_code="FRA",away_team="英格兰/阿根廷负者",away_team_en="Loser of England/Argentina",away_code="")
        elif no == "104": m.update(home_team="西班牙",home_team_en="Spain",home_code="ESP",away_team="英格兰/阿根廷胜者",away_team_en="Winner of England/Argentina",away_code="")
    schedule["last_updated"] = "2026-07-15"
    schedule["update_note"] = "半决赛101回填法国0-2西班牙；西班牙进入决赛、法国进入季军赛；102预测按最新竞彩与101复盘重新生成。"
    save(schedule_path, schedule)

    lesson = {
        "date":"20260715","headline":"法国0-2西班牙复盘：轻微低赔不能覆盖顶级客队零封路径",
        "summary":"2球总进球命中，但方向、主比分、晋级和比分池均未覆盖0-2。竞彩0-2赛前赔率15.00并非不可解释尾部，模型却只保留了0-1与1-2，错误地把西班牙的反向结果绑定为必须双方进球。",
        "metrics":{"settled":1,"direction_hits":0,"main_score_hits":0,"score_pool_hits":0,"total_goal_hits":1},
        "lessons":[
            "名义客队若具备顶级控球脱压、连续不败和零封能力，0-1与0-2必须同时进入反向核心池。",
            "HAD轻微主队低赔只表示边际优势，不能压掉赔率合理的客队零封比分；0-2赔率15.00应被视为可审计保护而非极端尾部。",
            "强队进攻名气不能替代实际破局能力评估；面对能稳定绕过压迫的对手，要提高战术与防守结构权重。",
            "这条修正用于102阿根廷路径：保留1-2之外，将0-1/0-2单列为核心反向保护，但不机械照搬昨日赛果。",
        ],
        "weight_adjustments":{"odds":-0.02,"tactics":0.02,"elite_away_clean_sheet_trigger":0.08,"both_teams_score_assumption":-0.05},
        "validation":{"match_no":"101","actual_score":"0-2","direction_hit":False,"main_score_hit":False,"score_pool_hit":False,"total_goals_hit":True},
    }
    save(DATA / "model_review_lessons_20260715.json", lesson)

    state = load(ROOT / "model_state.json")
    state["updatedAt"] = "2026-07-15T11:00:00+08:00"
    state["weights"] = {"odds":0.22,"elo":0.18,"form":0.15,"tactics":0.20,"motivation":0.12,"external":0.09,"mystic":0.04}
    state["calibration"] = {"latestReview":"20260715","lesson":"法国0-2暴露顶级名义客队零封胜漏池：0-1/0-2不能被轻微主队低赔和双方进球假设压掉。","todayAdjustment":"102最新竞彩2.38/2.70/2.95：主1-1；英格兰2-1/1-0；阿根廷0-1/0-2/1-2；晋级英格兰52%。"}
    state["history"] = [x for x in state["history"] if x.get("date") != "20260715"]
    state["history"].append({"date":"20260715","settled":1,"directionHits":0,"directionHitRate":"0%","mainScoreHits":0,"mainScoreHitRate":"0%","scorePoolHits":0,"scorePoolHitRate":"0%","totalGoalHits":1,"totalGoalHitRate":"100%"})
    save(ROOT / "model_state.json", state)

    m102 = load(DATA / "semifinal_prediction_102_20260715.json")["matches"][0]
    review_html = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>101 法国0-2西班牙复盘</title><style>{css()}</style></head><body><header><h1>半决赛101复盘｜法国0-2西班牙</h1><nav><a href='../index.html'>首页</a><a href='../20260716/'>明日102预测</a></nav></header><main><section class='card'><div class='grid'><div class='metric'>赛果<strong>0-2</strong><small>西班牙90分钟晋级</small></div><div class='metric'>总进球<strong>命中2球</strong><small>方向未中</small></div><div class='metric'>比分池<strong>未覆盖0-2</strong><small>0-2赛前赔率15.00</small></div><div class='metric'>永久修正<strong>客队零封触发器</strong><small>0-1/0-2并列审计</small></div></div><p>{esc(lesson['summary'])}</p><ul>{''.join(f'<li>{esc(x)}</li>' for x in lesson['lessons'])}</ul></section><footer>{DISCLAIMER}</footer></main></body></html>"""
    folder101 = ROOT / "20260715"
    (folder101 / "index.html").write_text(review_html, encoding="utf-8")
    (folder101 / "predict_20260715.html").write_text(review_html, encoding="utf-8")
    (folder101 / "review.html").write_text(review_html, encoding="utf-8")

    archive_extra = f"<section class='card'><h2>最新复盘：法国0-2西班牙</h2><p>{esc(lesson['summary'])}</p><ul>{''.join(f'<li>{esc(x)}</li>' for x in lesson['lessons'])}</ul><p><b>淘汰赛路径：</b>西班牙进入决赛，法国进入季军赛；等待102英格兰—阿根廷确定对手。</p></section>"
    (ROOT / "knockout" / "index.html").write_text(page("2026 世界杯淘汰赛归档", "西班牙已进入决赛；明日102预测已按101复盘和最新竞彩重新生成。", [m102], archive_extra), encoding="utf-8")

    single_extra = "<section class='card'><h2>明日单场组合</h2><div class='cols'><div class='panel'><h3>主线</h3><p>90分钟：英格兰胜，重点防平</p><p>总进球：2球，防1/3球</p></div><div class='panel'><h3>比分与反向</h3><p>主1-1；英格兰2-1/1-0</p><p class='red'>阿根廷0-1/0-2/1-2</p></div></div><p class='gold'>法国0-2教训已应用：顶级名义客队的0-1/0-2零封路线不可再省略。</p></section>"
    (ROOT / "parlay" / "index.html").write_text(page("明日半决赛102预测组合", "101已结束，不再生成无效两场串；本页只保留102胜平负、总进球、比分和爆冷组合。", [m102], single_extra), encoding="utf-8")

    outright = {"date":"20260715","source":"post-101 bracket model + Sporttery 102 full pools + public outright hierarchy","updatedAt":"2026-07-15 11:00 +08:00","odds":[{"team":"西班牙","decimal":1.69,"model_probability":0.59},{"team":"英格兰","decimal":4.55,"model_probability":0.22},{"team":"阿根廷","decimal":5.26,"model_probability":0.19}],"method":"西班牙已进决赛；英格兰/阿根廷概率由102晋级率与对西班牙的条件决赛胜率组合。模型公平价，不是庄家实时报价。","note":DISCLAIMER}
    save(DATA / "outright_odds_20260715.json", outright)
    save(DATA / "outright_odds_20260714.json", outright)
    print("101 reviewed; Spain final path, 102 regenerated, archive/parlay/outright updated")


if __name__ == "__main__":
    main()
