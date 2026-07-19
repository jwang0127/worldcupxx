from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
UPDATED_AT = "2026-07-19 11:20 +08:00"
DISCLAIMER = "以上仅为公开信息整理后的娱乐分析，不构成任何购彩建议，请理性参考。"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def load_base():
    path = ROOT / "scripts" / "update_finals_20260716.py"
    spec = importlib.util.spec_from_file_location("finals_base", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    module.UPDATED_AT = UPDATED_AT
    return module


def settle_third_place() -> None:
    path = DATA / "20260719.json"
    payload = load(path)
    match = payload["matches"][0]
    match["matchStatus"] = "Finished"
    match["result"] = {
        "homeGoals": 4,
        "awayGoals": 6,
        "status": "Finished",
        "source": "user-confirmed; public match reports",
        "excludeFromModel": True,
        "exclusionReason": "季军赛双方大幅轮换并开放进攻，比赛目标和战术约束与常规模型样本不同。",
    }
    match["excludeFromModel"] = True
    match["postReview"] = (
        "法国4-6英格兰（90分钟）。赛果写入赛程、赛果页与归档，但不进入模型准确率、权重校准或训练样本。"
        "原因是季军赛两队大幅轮换、主动放开进攻，10球脚本属于特殊赛制与动机环境；只保留一条展示层经验："
        "季军赛要单独标注高轮换与高开放度，不把极端大比分外推到决赛或普通淘汰赛。"
    )
    payload["lastUpdateTime"] = UPDATED_AT
    payload["updateNote"] = "103赛果已回填；明确excludeFromModel，不参与准确率、校准或训练。"
    save(path, payload)

    lesson = {
        "date": "20260719",
        "headline": "法国4-6英格兰：只记录赛果，不纳入预测模型",
        "summary": match["postReview"],
        "modelAction": "excluded",
        "excludeFromModel": True,
        "reason": match["result"]["exclusionReason"],
        "displayLesson": "季军赛需单列高轮换、高动机波动和高开放度标签，但不得用该场10球结果抬高决赛或常规淘汰赛的大球权重。",
    }
    save(DATA / "model_review_lessons_20260719.json", lesson)


def update_schedule() -> None:
    path = DATA / "knockout_schedule.json"
    payload = load(path)
    for match in payload["matches"]:
        if str(match.get("match_no")) == "103":
            match["status"] = "已完赛：英格兰6-4获季军（90分钟）"
            match["exclude_from_model"] = True
            match["note"] = str(match.get("note", "")) + " 该场为高轮换、开放式季军赛，赛果仅展示，不进入预测模型。"
    payload["last_updated"] = "2026-07-19"
    payload["update_note"] = "103回填法国4-6英格兰并隔离出模型；104维持西班牙vs阿根廷决赛。"
    save(path, payload)


def final_match_from_live() -> tuple[dict, dict]:
    live = load(DATA / "20260720_sporttery_live.json")
    live_match = next(x for x in live["matches"] if str(x.get("id")) == "104")
    analysis = (
        "官方体彩周日104现盘为西班牙2.02、平2.87、阿根廷3.50；较7月16日旧盘2.25/3.05/3.70，"
        "西班牙胜与平局同时被压低，阿根廷也较开盘缩短，市场更像西班牙不败下的一球内决赛，而非单边大胜。"
        "总进球2球赔率3.00最低，比分1-1为5.20最低，2-1为6.80、1-0为7.00。"
        "阵容面上，亚马尔与波罗此前缺训/有紧张感但预计首发，西班牙其余主力健康且大概率沿用半决赛框架；"
        "阿根廷无新增伤情，但蒙铁尔/莫利纳、德保罗/朱利亚诺、阿尔瓦雷斯/劳塔罗存在首发抉择，替补冲击力经过半决赛验证。"
        "经验面阿根廷的卫冕、决赛和点球经验占优，西班牙则有2024欧洲杯决赛与更稳定的控球脱压模板。"
        "综合后把1-1升为单一主比分，保留西班牙90分钟小胜为方向优势，最终捧杯仍略倾向西班牙。"
    )
    prediction = {
        "totalGoals": "2",
        "scores": ["1:1", "2:1", "1:0", "0:0", "1:2", "2:0", "0:1", "2:2", "1:3", "0:3", "1:4"],
        "upset": "0:1",
        "confidence": "中等",
        "candidates": ["2", "3", "1"],
    }
    live_match["groupName"] = "决赛"
    live_match["prediction"] = prediction
    live_match["review"] = analysis
    live_match["postReview"] = None
    live_match["newsContext"] = {
        "spain": [
            "亚马尔左大腿有包扎并接受赛前体能评估，但主帅确认预期可首发。",
            "波罗肌肉紧张但预计可用；其余主力没有新增伤停。",
            "罗德里+法比安继续优先，佩德里可能替补；巴埃纳与尼科-威廉姆斯仍有左路选择。",
        ],
        "argentina": [
            "半决赛后无新增伤停；蒙铁尔、德保罗、尼古拉斯-冈萨雷斯和劳塔罗均因替补表现竞争首发。",
            "埃米利亚诺-马丁内斯带伤参赛但已恢复完整合练，点球战经验仍是阿根廷的重要后手。",
            "斯卡洛尼可在控场型与更直接的双前锋/边路冲击之间切换。",
        ],
        "environment": "雷暴打乱两队最后一练；只小幅增加执行波动，不改变低比分主结构。",
    }
    live_match["modelDecision"] = {
        "direction90": "西班牙不败，胜优先、平局重点防范",
        "mainScore": "1-1",
        "top3Scores": ["1-1", "2-1", "1-0"],
        "totalGoals": "2球主线，防1/3球",
        "champion": "西班牙夺冠57% / 阿根廷夺冠43%",
    }
    return live, live_match


def update_final_data() -> dict:
    live, match = final_match_from_live()
    payload = {
        "date": "20260720",
        "dateText": "2026-07-20",
        "source": "sporttery-live-api + pre-match news review",
        "fetchedAt": live["fetchedAt"],
        "lastUpdateTime": live["lastUpdateTime"],
        "apiPoolCode": live["apiPoolCode"],
        "matches": [match],
    }
    save(DATA / "20260720.json", payload)
    return match


def final_prediction_record(match: dict) -> dict:
    return {
        "no": "104", "date": "20260720", "round": "决赛", "home": "西班牙", "away": "阿根廷",
        "kickoff": "07-20 03:00", "local": "07-19 15:00（纽约/新泽西，EDT）",
        "direction": "西班牙不败，胜优先、重点防平",
        "probability": "西班牙胜44% / 平31% / 阿根廷胜25%",
        "main_score": "1-1", "goals": "2球主线，防1/3球", "final_pick": "西班牙夺冠（57%）",
        "analysis": match["review"],
        "script": "半场0-0时1-1/1-0/0-0升权；西班牙先球时1-0/2-0/2-1升权；阿根廷先球时1-1/1-2/0-1升权。若阿根廷启用劳塔罗并加强前场压迫，2-1与1-2同时上调；若亚马尔临场无法首发，西班牙胜率下调约3个百分点，1-1继续居首。",
        "odds": "体彩周日104（截至7月19日11:08）：HAD 2.02 / 2.87 / 3.50；西班牙-1为4.35 / 3.55 / 1.62；总进球2球3.00最低，3球3.85、1球4.25；比分1-1为5.20最低，2-1为6.80、1-0为7.00。",
        "score_pool": [
            {"score": "1-1", "prob": 19, "role": "主比分", "reason": "体彩最低比分与决赛谨慎结构"},
            {"score": "2-1", "prob": 15, "role": "前三保护", "reason": "西班牙控球优势与阿根廷反击得分并存"},
            {"score": "1-0", "prob": 14, "role": "前三保护", "reason": "西班牙先手后的控场零封"},
            {"score": "0-0", "prob": 12, "role": "锁局保护", "reason": "双方前60分钟优先压缩风险"},
            {"score": "1-2", "prob": 10, "role": "反向核心", "reason": "阿根廷决赛经验与后程替补冲击"},
            {"score": "2-0", "prob": 10, "role": "控制扩展", "reason": "西班牙领先后继续压迫"},
            {"score": "0-1", "prob": 9, "role": "反向零封", "reason": "梅西定位球或转换先手"},
            {"score": "2-2", "prob": 5, "role": "平局尾部", "reason": "早球后双方转换空间扩大"},
            {"score": "1-3", "prob": 2, "role": "反向尾部", "reason": "西班牙追分导致阿根廷连续转换"},
            {"score": "0-3", "prob": 1, "role": "极端尾部", "reason": "阿根廷先手且西班牙压上失衡"},
            {"score": "1-4", "prob": 1, "role": "极端尾部", "reason": "仅保留体彩有报价的崩盘情景"},
        ],
        "sources": [
            {"label": "中国体育彩票周日104官方赔率", "url": "https://www.sporttery.cn/"},
            {"label": "西班牙阵容与亚马尔、波罗伤情", "url": "https://www.standard.co.uk/sport/football/spain-xi-vs-argentina-confirmed-team-news-predicted-lineup-injury-latest-world-cup-final-2026-b1290417.html"},
            {"label": "阿根廷阵容与轮换选择", "url": "https://www.standard.co.uk/sport/football/argentina-xi-vs-spain-confirmed-team-news-predicted-lineup-injury-latest-world-cup-final-2026-b1290419.html"},
            {"label": "德拉富恩特：不会专人盯防梅西", "url": "https://www.theguardian.com/football/2026/jul/18/luis-de-la-fuente-reveals-spain-will-not-man-mark-messi-in-world-cup-final"},
            {"label": "雷暴影响两队最后训练", "url": "https://www.reuters.com/sports/soccer/spains-final-world-cup-training-session-cancelled-due-thunderstorms-2026-07-18/"},
            {"label": "7月18日多公司盘与战术预览", "url": "https://www.rotowire.com/soccer/article/spain-vs-argentina-preview-predicted-lineups-team-news-tactical-analysis-2026-world-cup-final-123191"},
        ],
    }


def third_place_page(base) -> str:
    return f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>季军赛 法国4-6英格兰赛果</title><style>{base.CSS}</style></head><body><main>
<span class='matchNo'>季军赛 103｜已结束｜90分钟</span><h1>法国 4-6 英格兰</h1><div class='chips'><a class='chip' href='../index.html'>首页</a><a class='chip' href='../20260720/'>决赛新预测</a><a class='chip' href='../accuracy/'>模型准确率</a></div>
<section class='card'><div class='core'><div class='metric'>90分钟赛果<strong>4-6</strong></div><div class='metric'>季军<strong>英格兰</strong></div><div class='metric'>模型处理<strong>明确排除</strong></div></div><p>赛果已写入赛程与网页归档。该场双方在季军赛环境下大幅轮换并开放进攻，比赛目标、风险偏好和战术约束与常规淘汰赛不同，因此不进入模型准确率、权重校准或训练样本。</p><p><strong>只保留展示层经验：</strong>季军赛要单列高轮换、高动机波动与高开放度标签，但不能把这场10球外推到西班牙—阿根廷决赛。</p></section>
<footer>{DISCLAIMER}</footer></main></body></html>"""


def update_hubs(base, accuracy: dict) -> None:
    final_card = final_prediction_record(final_match_from_live()[1])
    root = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>2026 世界杯决赛预测</title><style>{base.CSS}</style></head><body><main><header class='hero'><div><h1>西班牙 vs 阿根廷｜决赛新预测</h1><p>季军赛已结束：法国4-6英格兰。该赛果只展示，不进入模型；决赛已按官方体彩周日104现盘、最新阵容消息、轮换选择与大赛经验重新评估。</p><div class='chips'><span class='chip'>更新 {UPDATED_AT}</span><span class='chip'>体彩周日104</span><span class='chip'>季军赛样本已隔离</span></div></div></header>
<h2>决赛核心结论</h2><section class='card'><span class='matchNo'>决赛104｜07-20 03:00</span><div class='teams'>西班牙 vs 阿根廷</div><div class='core'><div class='metric'>90分钟<strong>西班牙不败，胜优先</strong></div><div class='metric'>主比分<strong>1-1</strong></div><div class='metric'>捧杯<strong>西班牙57%</strong></div></div><p>前三比分：1-1 / 2-1 / 1-0。体彩HAD 2.02 / 2.87 / 3.50，总进球2球最低，比分1-1最低；阿根廷的卫冕与后程经验使平局和反向小胜不能再留在尾池。</p><a class='chip' href='./20260720/'>查看完整预测 →</a></section>
<h2>已结束比赛</h2><section class='card'><span class='matchNo'>季军赛103</span><h3>法国 4-6 英格兰</h3><p>赛果已回填；高轮换、开放式季军赛，明确排除出模型准确率与校准。</p><a href='./20260719/'>查看赛果与排除说明</a></section>
<h2>功能入口</h2><section class='archive'><a class='card' href='./accuracy/'><strong>历史准确率</strong><p>{accuracy['metrics']['settled']}场模型样本；不含103季军赛。</p></a><a class='card' href='./knockout/'><strong>淘汰赛归档</strong><p>查看半决赛、季军赛与决赛。</p></a><a class='card' href='./group/'><strong>小组赛归档</strong><p>历史每日预测页面。</p></a><a class='card' href='./20260720/'><strong>决赛预测</strong><p>新闻、轮换、盘口与比分池。</p></a></section><footer>{DISCLAIMER}</footer></main></body></html>"""
    write(ROOT / "index.html", root)

    knockout = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>2026 世界杯淘汰赛归档</title><style>{base.CSS}</style></head><body><main><h1>淘汰赛决赛阶段</h1><div class='chips'><a class='chip' href='../index.html'>首页</a><a class='chip' href='../accuracy/'>历史准确率</a></div><section class='card tableWrap'><table><thead><tr><th>轮次</th><th>北京时间</th><th>对阵</th><th>状态 / 预测</th><th>入口</th></tr></thead><tbody><tr><td>半决赛101</td><td>已结束</td><td>法国0-2西班牙</td><td>西班牙晋级</td><td><a href='../20260715/'>复盘</a></td></tr><tr><td>半决赛102</td><td>已结束</td><td>英格兰1-2阿根廷</td><td>阿根廷晋级</td><td><a href='../20260716/'>复盘</a></td></tr><tr><td>季军赛103</td><td>已结束</td><td>法国4-6英格兰</td><td>赛果展示；不入模型</td><td><a href='../20260719/'>赛果</a></td></tr><tr><td>决赛104</td><td>07-20 03:00</td><td>西班牙 vs 阿根廷</td><td>西班牙不败；主比分1-1</td><td><a href='../20260720/'>新预测</a></td></tr></tbody></table></section><footer>{DISCLAIMER}</footer></main></body></html>"""
    write(ROOT / "knockout" / "index.html", knockout)

    parlay_data = {
        "date": "20260719",
        "stage": "final_stage_archive",
        "status": "closed",
        "reason": "103季军赛已经结束，旧的103+104二串一不再有效；104为单场决赛，不生成伪二串一。",
        "settledMatch": "103 法国4-6英格兰",
        "finalMatch": "104 西班牙vs阿根廷",
        "disclaimer": DISCLAIMER,
    }
    save(DATA / "final_stage_parlay_20260716.json", parlay_data)
    parlay_page = f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>决赛阶段二串一归档</title><style>{base.CSS}</style></head><body><main><h1>决赛阶段二串一已封存</h1><div class='chips'><a class='chip' href='../index.html'>首页</a><a class='chip' href='../20260720/'>决赛新预测</a></div><section class='card'><div class='core'><div class='metric'>季军赛103<strong>已结束 4-6</strong></div><div class='metric'>决赛104<strong>单场待赛</strong></div><div class='metric'>旧组合<strong>停止展示</strong></div></div><p>原103+104组合因季军赛已经结束而失效。当前只剩西班牙—阿根廷单场决赛，不用已经结算的103拼接伪二串一，也不把季军赛极端大比分外推到决赛。</p></section><footer>{DISCLAIMER}</footer></main></body></html>"""
    write(ROOT / "parlay" / "index.html", parlay_page)


def update_model_state() -> None:
    path = ROOT / "model_state.json"
    state = load(path)
    state["updatedAt"] = "2026-07-19T11:20:00+08:00"
    state["calibration"]["todayAdjustment"] = "103法国4-6英格兰仅展示并排除出模型；104按体彩2.02/2.87/3.50与赛前阵容重排为1-1主比分，2-1/1-0前三保护，最终仍略倾向西班牙。"
    state["excludedResults"] = [x for x in state.get("excludedResults", []) if x.get("matchNo") != "103"]
    state["excludedResults"].append({"date": "20260719", "matchNo": "103", "score": "法国4-6英格兰", "reason": "季军赛高轮换与开放式比赛，不进入准确率、权重校准或训练。"})
    save(path, state)


def main() -> None:
    base = load_base()
    settle_third_place()
    update_schedule()
    match = update_final_data()
    record = final_prediction_record(match)
    save(DATA / "final_stage_prediction_104_20260719.json", {"date": "20260720", "stage": "决赛", "matches": [record], "generatedAt": UPDATED_AT, "source": "Sporttery live odds + pre-match news review"})
    # Keep the canonical 104 record current for any older consumers that use the original filename.
    save(DATA / "final_stage_prediction_104_20260716.json", {"date": "20260720", "stage": "决赛", "matches": [record], "generatedAt": UPDATED_AT, "source": "Sporttery live odds + pre-match news review"})
    page = base.prediction_page(record).replace("体彩赔率未出，本页使用公开赔率综合快照。", "体彩周日104已开售；本页使用官方现盘并结合最新赛前信息。")
    write(ROOT / "20260720" / "index.html", page)
    write(ROOT / "20260720" / "predict_20260720.html", page)
    third = third_place_page(base)
    write(ROOT / "20260719" / "index.html", third)
    write(ROOT / "20260719" / "predict_20260719.html", third)
    write(ROOT / "20260719" / "review.html", third)
    update_model_state()
    accuracy, accuracy_page = base.build_accuracy()
    write(ROOT / "accuracy" / "index.html", accuracy_page)
    update_hubs(base, accuracy)
    print(json.dumps({"updated": ["103 result/exclusion", "104 live odds/news prediction", "homepage", "knockout", "accuracy"], "accuracy": accuracy["metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
