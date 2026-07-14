#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from update_semifinals_20260712 import DATA, ROOT, DISCLAIMER, load, save, page


def main() -> None:
    daily_path = DATA / "20260716.json"
    daily = load(daily_path)
    raw = daily["matches"][0]
    if str(raw.get("id")) != "102" or raw.get("home") != "英格兰" or raw.get("away") != "阿根廷":
        raise RuntimeError("102赛程或主客队不匹配")
    odds = raw["odds"]
    required = ("had", "hhad", "ttg", "crs", "hafu")
    if any(not odds.get(pool) for pool in required):
        raise RuntimeError("102竞彩全池尚未完整")

    m102 = {
        "no":"102", "home":"英格兰", "away":"阿根廷",
        "kickoff":"07-16 03:00", "local":"07-15 15:00（亚特兰大）",
        "direction":"英格兰胜，重点防平",
        "probability":"英格兰胜38% / 平32% / 阿根廷胜30%",
        "main_score":"1-1", "goals":"2球主线，防1/3球",
        "advance":"英格兰", "advance_prob":"英格兰53% / 阿根廷47%",
        "upset":"阿根廷0-1或1-2",
        "hafu":"胜胜 / 平平 / 平胜，防负负",
        "fitness":"两队八强均打加时；阿根廷更晚结束且少休息约4小时，体能项小幅偏英格兰。",
        "analysis":"竞彩HAD 2.35/2.75/2.94把英格兰放在轻微优势位，归一化约38%/32%/30%；2球赔率2.95最低，1-1赔率5.00明显最低，说明市场核心仍是低比分均衡局。新盘纠正了旧模型对阿根廷方向的轻微偏置：90分钟主线仍是1-1，但胜负分支改为英格兰2-1/1-0优先，最终晋级小幅转向英格兰。比分尾部1-3（28.00）、0-3（40.00）和1-4（110.00）已审计，但因低总进球与双方保守脚本冲突，暂不进入展示池；只有早球叠加追分状态才临场升权。",
        "script":"半场0-0时1-1、1-0、0-0升权；英格兰先球时2-1/1-0升权；阿根廷先球时1-1/1-2/0-1升权；前30分钟出现进球才把3球及2-2抬进主保护层。",
        "odds":f"竞彩HAD {odds['had']['home']}/{odds['had']['draw']}/{odds['had']['away']}；总进球1球 {odds['ttg']['s1']}、2球 {odds['ttg']['s2']}、3球 {odds['ttg']['s3']}；比分1-1 {odds['crs']['1-1']}、2-1 {odds['crs']['2-1']}、1-0 {odds['crs']['1-0']}、0-1 {odds['crs']['0-1']}、1-2 {odds['crs']['1-2']}、0-0 {odds['crs']['0-0']}；半全场胜胜 {odds['hafu']['hh']}、平平 {odds['hafu']['dd']}、平胜 {odds['hafu']['dh']}；竞彩最后更新时间 {daily.get('lastUpdateTime')}。",
        "score_pool":[
            {"score":"1-1","prob":20,"role":"主推","reason":"竞彩最低比分价，平局与2球主线重合"},
            {"score":"2-1","prob":15,"role":"英格兰胜主线","reason":"英格兰轻优且对手有进球能力"},
            {"score":"1-0","prob":12,"role":"小球保护","reason":"英格兰方向叠加低总进球"},
            {"score":"0-1","prob":11,"role":"反向保护","reason":"阿根廷关键球与低比分管理"},
            {"score":"1-2","prob":10,"role":"爆冷","reason":"阿根廷后程反击或定位球"},
            {"score":"0-0","prob":9,"role":"锁局保护","reason":"双方加时消耗与半决赛谨慎"},
            {"score":"2-2","prob":7,"role":"尾部","reason":"只在早球或追分状态升权"},
        ],
        "sources":[
            {"label":"中国竞彩官方102全池赔率（2026-07-14抓取）","url":"https://webapi.sporttery.cn/gateway/uniform/football/getMatchCalculatorV1.qry?channel=c&poolCode=ttg,had,hhad,crs,hafu"},
            {"label":"FIFA英格兰—阿根廷半决赛赛前页","url":"https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/england-v-argentina-live-stream-team-news-tickets-and-more"},
            {"label":"DraftKings开盘：英格兰+155，阿根廷+205","url":"https://dknetwork.draftkings.com/2026/07/12/world-cup-2026-argentina-vs-england-opening-odds-2/"},
        ],
    }

    raw["prediction"] = {"totalGoals":"2", "scores":["1:1","2:1","1:0","0:1","1:2","0:0","2:2"], "upset":"1:2", "confidence":"中高", "candidates":["2","1","3"]}
    raw["review"] = "竞彩全池刷新后：90分钟英格兰轻优、重点防平；2球主线，1-1主比分，最终晋级英格兰53%。"
    save(daily_path, daily)
    payload102 = {"date":"20260716","stage":"semifinal","matches":[m102],"generatedAt":"2026-07-14 14:40 +08:00","source":"Sporttery live full pools"}
    save(DATA / "semifinal_prediction_102_20260714.json", payload102)
    save(DATA / "semifinal_prediction_102_20260712.json", payload102)

    m101 = load(DATA / "semifinal_prediction_101_20260712.json")["matches"][0]
    html102 = page("世界杯半决赛 102", "竞彩全池赔率已刷新；90分钟方向、比分池和最终晋级已重新校准。", [m102])
    folder = ROOT / "20260716"
    (folder / "index.html").write_text(html102, encoding="utf-8")
    (folder / "predict_20260716.html").write_text(html102, encoding="utf-8")

    parlay = {
        "date":"20260714","stage":"semifinal_two_leg","title":"半决赛两场串（102赔率刷新）",
        "legs":[
            {"match_no":"101","match":"法国 vs 西班牙","win_draw_loss":"法国胜，防平","total_goals":"2/3球","scores":"2-1 / 1-1 / 1-0","upset":"西班牙1-2","confidence":"中"},
            {"match_no":"102","match":"英格兰 vs 阿根廷","win_draw_loss":"英格兰胜，重点防平","total_goals":"2球，防1/3球","scores":"1-1 / 2-1 / 1-0","upset":"阿根廷0-1 / 1-2","confidence":"中高；竞彩全池已校准"},
        ],
        "combination":{"main":"101法国胜或平 + 102英格兰胜或平","goals":"101 2/3球 + 102 2球（防1/3）","scores":"101 2-1/1-1 + 102 1-1/2-1","upset":"101西班牙1-2 + 102阿根廷0-1/1-2"},
        "risk":"两场均为强强半决赛；102平局赔率和1-1比分价很低，英格兰轻优不能解读为稳胜。", "disclaimer":DISCLAIMER,
    }
    save(DATA / "semifinal_parlay_20260714.json", parlay)
    save(DATA / "semifinal_parlay_20260712.json", parlay)
    extra = f"<section class='card'><h2>两场串关模型组合｜102全池已刷新</h2><div class='cols'><div class='panel'><h3>主线</h3><p>{parlay['combination']['main']}</p><p>总进球：{parlay['combination']['goals']}</p></div><div class='panel'><h3>比分 / 爆冷</h3><p>{parlay['combination']['scores']}</p><p class='red'>{parlay['combination']['upset']}</p></div></div><p class='gold'>{parlay['risk']}</p></section>"
    (ROOT / "parlay" / "index.html").write_text(page("世界杯半决赛两场串", "102竞彩胜平负、总进球、比分和半全场全池已录入。", [m101,m102], extra), encoding="utf-8")

    review = load(DATA / "model_review_lessons_20260712.json")
    review_html = "".join(f"<li><b>{x['match_no']}</b> {x['review']}</li>" for x in review["results"])
    archive_extra = f"<section class='card'><h2>四分之一决赛归档与模型复盘</h2><ul>{review_html}</ul><p><b>102赔率刷新：</b>英格兰轻优、平局重，1-1继续主推；晋级方向由阿根廷55%修正为英格兰53%。</p></section>"
    (ROOT / "knockout" / "index.html").write_text(page("2026 世界杯淘汰赛归档", "四强已确认；102竞彩全池赔率与半决赛预测已刷新。", [m101,m102], archive_extra), encoding="utf-8")

    outright = {"date":"20260714","source":"semifinal model calibrated by Sporttery 101/102 full pools and public market hierarchy","updatedAt":"2026-07-14 14:40 +08:00","odds":[{"team":"法国","decimal":2.50,"model_probability":0.40},{"team":"英格兰","decimal":4.35,"model_probability":0.23},{"team":"西班牙","decimal":4.55,"model_probability":0.22},{"team":"阿根廷","decimal":6.67,"model_probability":0.15}],"method":"101与102均使用竞彩全池校准；公平赔率为归一化模型展示，并非庄家实时报价。","note":DISCLAIMER}
    save(DATA / "outright_odds_20260714.json", outright)
    save(DATA / "outright_odds_20260712.json", outright)

    state = load(ROOT / "model_state.json")
    state["updatedAt"] = "2026-07-14T14:40:00+08:00"
    state["weights"]["odds"] = 0.24
    state["weights"]["external"] = 0.09
    state["calibration"]["todayAdjustment"] = "102竞彩2.35/2.75/2.94与2球/1-1低位：90分钟英格兰轻优、重点防平；主1-1，胜负分支2-1/1-0优先，晋级英格兰53%。"
    save(ROOT / "model_state.json", state)
    print("102 full odds refreshed; prediction, parlay, knockout archive and outright model updated")


if __name__ == "__main__":
    main()
