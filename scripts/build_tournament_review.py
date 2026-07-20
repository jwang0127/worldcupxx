#!/usr/bin/env python3
"""Build the final, reproducible World Cup prediction review.

The project stores group-stage predictions in daily JSON files and knockout
predictions/results in separate archives.  This script joins both formats,
deduplicates by pre-match record, and settles every metric on 90-minute scores.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path


DISCLAIMER = "以上仅为公开信息整理后的娱乐分析，不构成任何购彩建议，请理性参考。"
FINAL_RESULT_SOURCE = "https://apnews.com/article/fccc26aa12d9226e63d06b601b770617"
GROUP_RESULT_SOURCE = "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def repair_text(value):
    if not isinstance(value, str):
        return value
    for source_encoding in ("latin1", "cp1252"):
        try:
            fixed = value.encode(source_encoding).decode("utf-8")
            if fixed != value and any("\u4e00" <= c <= "\u9fff" for c in fixed):
                return fixed
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return value


def score_norm(value) -> str:
    match = re.search(r"(\d+)\s*[:\-]\s*(\d+)", str(value or ""))
    return f"{int(match.group(1))}-{int(match.group(2))}" if match else "—"


def score_direction(score: str) -> str:
    try:
        home, away = (int(x) for x in score_norm(score).split("-"))
    except ValueError:
        return "—"
    return "主胜" if home > away else "平" if home == away else "客胜"


def unique_scores(values) -> list[str]:
    output = []
    for value in values:
        score = score_norm(value.get("score") if isinstance(value, dict) else value)
        if score != "—" and score not in output:
            output.append(score)
    return output


def goal_prediction_hit(label: str, actual: int) -> bool:
    text = str(label or "")
    core = re.search(r"核心\s*(\d+)(?:\s*/\s*(\d+))?\s*球", text)
    if core:
        return actual in {int(x) for x in core.groups() if x is not None}
    range_match = re.search(r"(\d+)\s*[-–至]\s*(\d+)\s*球", text)
    if range_match:
        low, high = map(int, range_match.groups())
        return low <= actual <= high
    values = [int(x) for x in re.findall(r"\d+", text)]
    return actual in values or (7 in values and actual >= 7)


def rate(hits: int, total: int) -> str:
    return f"{hits / total * 100:.1f}%" if total else "—"


def make_row(*, date: str, no: str, match: str, stage: str, main: str,
             pool: list[str], actual: str, total_goal_prediction: str,
             excluded: bool = False, exclusion_reason: str = "", source: str = "") -> dict:
    main = score_norm(main)
    pool = unique_scores(pool)[:3]
    actual = score_norm(actual)
    actual_goals = sum(int(x) for x in actual.split("-"))
    return {
        "date": date,
        "no": str(no),
        "match": repair_text(match),
        "stage": stage,
        "main_score": main,
        "top3_pool": pool,
        "actual_90": actual,
        "main_hit": main == actual,
        "score_pool_hit": actual in pool,
        "wdl_prediction": score_direction(main),
        "wdl_actual": score_direction(actual),
        "wdl_hit": score_direction(main) == score_direction(actual),
        "total_goal_prediction": str(total_goal_prediction or "—"),
        "actual_total_goals": actual_goals,
        "total_goal_hit": goal_prediction_hit(total_goal_prediction, actual_goals),
        "excluded_from_calibration": excluded,
        "exclusion_reason": exclusion_reason,
        "result_source": source,
    }


def daily_goal_index(data_dir: Path) -> dict[tuple[str, str], str]:
    output = {}
    for path in sorted(data_dir.glob("2026????.json")):
        try:
            payload = load(path)
        except (OSError, json.JSONDecodeError):
            continue
        for match in payload.get("matches", []):
            output[(path.stem, str(match.get("id", "")))] = str((match.get("prediction") or {}).get("totalGoals", "—"))
    return output


def collect_rows(root: Path) -> list[dict]:
    data = root / "data"
    old = load(data / "accuracy_summary_20260716.json")
    goal_index = daily_goal_index(data)
    rows = []

    # Preserve the already-audited 56 historical rows, then fill the archive gaps.
    for item in old["matches"]:
        stage = "小组赛" if item["date"] <= "20260628" else "淘汰赛"
        rows.append(make_row(
            date=item["date"], no=item["no"], match=item["match"], stage=stage,
            main=item["main_score"], pool=item["top3_pool"], actual=item["actual"],
            total_goal_prediction=goal_index.get((item["date"], item["no"]), "—"),
            source="项目原始赛果归档",
        ))

    # Six group-stage predictions existed on 28 June but were absent from the old accuracy page.
    june28 = load(data / "20260628.json")
    for match in june28["matches"]:
        result = match.get("result") or {}
        if result.get("homeGoals") is None:
            continue
        pred = match.get("prediction") or {}
        scores = list(pred.get("scores", [])) + [pred.get("upset")]
        rows.append(make_row(
            date="20260628", no=match["id"], match=f"{match['home']} vs {match['away']}", stage="小组赛",
            main=pred.get("scores", ["—"])[0], pool=scores,
            actual=f"{result['homeGoals']}-{result['awayGoals']}", total_goal_prediction=pred.get("totalGoals", "—"),
            source=GROUP_RESULT_SOURCE,
        ))

    # Join knockout pre-match snapshots 73-96 with their separate result files.
    predictions = {}
    results = {}
    for path in sorted(data.glob("knockout_predictions_2026????.json")):
        for match in load(path).get("matches", []):
            no = str(match.get("match_no", ""))
            if no.isdigit() and 73 <= int(no) <= 96:
                predictions[no] = (path.stem.rsplit("_", 1)[-1], match)
    for path in sorted(data.glob("knockout_results_2026????.json")):
        for match in load(path).get("matches", []):
            no = str(match.get("match_no", ""))
            if no.isdigit() and 73 <= int(no) <= 96:
                results[no] = match
    for no in sorted(predictions, key=int):
        date, pred = predictions[no]
        result = results.get(no)
        if not result:
            continue
        matrix = pred.get("score_matrix_top") or []
        pool = matrix if matrix else [pred.get("main_score")] + pred.get("safe_scores", []) + pred.get("backup_scores", [])
        home = repair_text(pred.get("home_team") or result.get("home_team") or "主队")
        away = repair_text(pred.get("away_team") or result.get("away_team") or "客队")
        rows.append(make_row(
            date=date, no=no, match=f"{home} vs {away}", stage="淘汰赛",
            main=pred.get("main_score"), pool=pool, actual=result.get("score"),
            total_goal_prediction=repair_text(pred.get("goals_range", "—")), source="项目淘汰赛赛果归档",
        ))

    # Special third-place match remains visible but is excluded only from calibration metrics.
    third = load(data / "20260719.json")["matches"][0]
    third_pred, third_result = third["prediction"], third["result"]
    rows.append(make_row(
        date="20260719", no=third["id"], match=f"{third['home']} vs {third['away']}", stage="季军赛",
        main=third_pred["scores"][0], pool=third_pred["scores"],
        actual=f"{third_result['homeGoals']}-{third_result['awayGoals']}",
        total_goal_prediction=third_pred["totalGoals"], excluded=True,
        exclusion_reason=third_result.get("exclusionReason", "特殊比赛样本"), source="公开赛果与项目归档",
    ))

    final = load(data / "20260720.json")["matches"][0]
    final_pred, final_result = final["prediction"], final["result"]
    rows.append(make_row(
        date="20260720", no=final["id"], match=f"{final['home']} vs {final['away']}", stage="决赛",
        main=final_pred["scores"][0], pool=final_pred["scores"],
        actual=f"{final_result['homeGoals']}-{final_result['awayGoals']}",
        total_goal_prediction=final_pred["totalGoals"], source=FINAL_RESULT_SOURCE,
    ))

    rows.sort(key=lambda x: (x["date"], int(re.sub(r"\D", "", x["no"]) or 0), x["match"]))
    return rows


def metrics(rows: list[dict]) -> dict:
    return {
        "settled": len(rows),
        "main_score_hits": sum(x["main_hit"] for x in rows),
        "score_pool_hits": sum(x["score_pool_hit"] for x in rows),
        "wdl_hits": sum(x["wdl_hit"] for x in rows),
        "total_goal_hits": sum(x["total_goal_hit"] for x in rows),
        "main_score_rate": rate(sum(x["main_hit"] for x in rows), len(rows)),
        "score_pool_rate": rate(sum(x["score_pool_hit"] for x in rows), len(rows)),
        "wdl_rate": rate(sum(x["wdl_hit"] for x in rows), len(rows)),
        "total_goal_rate": rate(sum(x["total_goal_hit"] for x in rows), len(rows)),
    }


def build_summary(rows: list[dict]) -> dict:
    comparable = [x for x in rows if not x["excluded_from_calibration"]]
    stages = {}
    for stage in ("小组赛", "淘汰赛", "季军赛", "决赛"):
        subset = [x for x in rows if x["stage"] == stage]
        if subset:
            stages[stage] = metrics(subset)
    actual_draws = sum(x["wdl_actual"] == "平" for x in comparable)
    predicted_draws = sum(x["wdl_prediction"] == "平" for x in comparable)
    high_tail_misses = sum(
        not x["main_hit"] and x["actual_total_goals"] >= 4 and
        sum(int(v) for v in x["main_score"].split("-")) + 2 <= x["actual_total_goals"]
        for x in comparable
    )
    return {
        "updatedAt": "2026-07-20 赛后终版",
        "coverage": {
            "tournament_matches": 104,
            "settled_predictions": len(rows),
            "not_predicted_or_not_archived": 104 - len(rows),
            "calibration_samples": len(comparable),
            "excluded_special_samples": len(rows) - len(comparable),
        },
        "settlement": {
            "score_basis": "所有指标按90分钟比分结算；加时、点球和晋级结果单列。",
            "main_score": "只取赛前排序第一的比分。",
            "score_pool": "只取赛前排序前三；完整尾池不用于主准确率。",
            "wdl": "由单一主比分映射为主胜、平、客胜，不允许用胜/防平复式双算。",
            "total_goals": "按当时公开的单值或明确区间结算；区间命中不等于精确球数命中。",
            "exclusions": "季军赛103在全量原始表现中展示，但因预先标记为特殊样本，不进入模型校准口径。",
        },
        "all_settled_metrics": metrics(rows),
        "calibration_metrics": metrics(comparable),
        "stage_metrics": stages,
        "diagnostics": {
            "actual_draws": actual_draws,
            "predicted_draws": predicted_draws,
            "high_score_undercoverage_misses": high_tail_misses,
        },
        "methodology": [
            "先锁定赛程和90分钟赛果，再连接赔率、赛前预测与赛后复盘；场次映射错则整场不计。",
            "分层输出：单一胜平负、总进球主线、主比分、前三比分池；完整池只解释尾部风险。",
            "比分池必须排序，不能赛后用大池覆盖替代前三命中；胜平负必须单选，不能把防守项一起算中。",
            "淘汰赛把90分钟与晋级拆开；季军赛、高轮换等分布漂移样本先标记、后分析，排除规则不得赛后临时发明。",
            "复盘先找结构性触发器：弱队先球、强队零封、追分扩大、韧性平局、低价客胜尾部；不追逐上一天的大小球。",
            "模型优化目标按稳定性排序：先提高胜平负校准，再提高总进球主线，最后优化主比分和前三池排序。",
        ],
        "sources": [
            {"label": "FIFA 全赛程与赛果", "url": GROUP_RESULT_SOURCE},
            {"label": "决赛赛果与90分钟/加时说明（AP）", "url": FINAL_RESULT_SOURCE},
        ],
        "matches": rows,
    }


CSS = """
:root{--bg:#071411;--card:#10251f;--panel:#17342c;--line:#2b5b4d;--text:#effcf7;--muted:#a7c1b8;--green:#62e49e;--blue:#7bd2ff;--gold:#f3c65c;--red:#ff8c85}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 12% 0,rgba(98,228,158,.15),transparent 28%),var(--bg);color:var(--text);font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.65}main{max-width:1260px;margin:auto;padding:34px 18px 54px}h1{font-size:clamp(30px,5vw,50px);margin:0}h2{color:var(--blue);margin:30px 0 12px}h3{color:var(--gold)}p{color:var(--muted)}a{color:var(--green)}.chips,.metrics{display:flex;gap:9px;flex-wrap:wrap}.chip{border:1px solid var(--line);border-radius:999px;padding:6px 11px;color:#b8ffe0;text-decoration:none;background:#0c211b}.card{background:linear-gradient(180deg,var(--card),#0a1d18);border:1px solid var(--line);border-radius:12px;padding:18px}.metrics{display:grid;grid-template-columns:repeat(4,1fr)}.metric{background:var(--panel);padding:13px;border-radius:9px}.metric strong{display:block;color:var(--green);font-size:clamp(20px,3vw,30px)}.note{border-left:4px solid var(--gold)}.tableWrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:1050px}th,td{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{position:sticky;top:0;background:#0b211b;color:var(--blue)}.hit{color:var(--green);font-weight:800}.miss{color:var(--red);font-weight:800}.excluded{color:var(--gold)}details{margin:10px 0}summary{cursor:pointer;color:var(--gold);font-weight:700}ol,ul{color:var(--muted)}footer{margin-top:32px;color:var(--muted);font-size:13px}@media(max-width:820px){.metrics{grid-template-columns:1fr 1fr}table{min-width:940px}}@media(max-width:520px){.metrics{grid-template-columns:1fr}}
"""


def badge(hit: bool) -> str:
    return f"<span class='{'hit' if hit else 'miss'}'>{'命中' if hit else '未中'}</span>"


def render(summary: dict) -> str:
    e = html.escape
    m = summary["calibration_metrics"]
    raw = summary["all_settled_metrics"]
    rows = "".join(
        "<tr>"
        f"<td>{e(x['date'])}</td><td>{e(x['no'])}</td><td>{e(x['stage'])}</td><td>{e(x['match'])}</td>"
        f"<td><strong>{e(x['actual_90'])}</strong></td>"
        f"<td>{e(x['total_goal_prediction'])}<br>{badge(x['total_goal_hit'])}</td>"
        f"<td>{e(x['main_score'])}<br>{badge(x['main_hit'])}</td>"
        f"<td>{e(' / '.join(x['top3_pool']))}<br>{badge(x['score_pool_hit'])}</td>"
        f"<td>{e(x['wdl_prediction'])} → {e(x['wdl_actual'])}<br>{badge(x['wdl_hit'])}</td>"
        f"<td>{'<span class=\"excluded\">仅展示，不校准</span>' if x['excluded_from_calibration'] else '纳入'}</td>"
        "</tr>" for x in reversed(summary["matches"])
    )
    stage_rows = "".join(
        f"<tr><td>{e(stage)}</td><td>{v['settled']}</td><td>{v['total_goal_hits']}/{v['settled']} · {v['total_goal_rate']}</td>"
        f"<td>{v['main_score_hits']}/{v['settled']} · {v['main_score_rate']}</td><td>{v['score_pool_hits']}/{v['settled']} · {v['score_pool_rate']}</td>"
        f"<td>{v['wdl_hits']}/{v['settled']} · {v['wdl_rate']}</td></tr>"
        for stage, v in summary["stage_metrics"].items()
    )
    methods = "".join(f"<li>{e(x)}</li>" for x in summary["methodology"])
    settlement = "".join(f"<li><strong>{e(k)}：</strong>{e(v)}</li>" for k, v in summary["settlement"].items())
    return f"""<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>2026 世界杯全部预测复盘</title><style>{CSS}</style></head><body><main>
<header><h1>2026 世界杯全部预测复盘</h1><p>赛事终版：项目共留存并结算 {summary['coverage']['settled_predictions']} 场赛前预测，覆盖整届 104 场中的 {summary['coverage']['settled_predictions']} 场；缺少赛前存档的 {summary['coverage']['not_predicted_or_not_archived']} 场不补猜、不计准确率。</p><div class='chips'><span class='chip'>西班牙夺冠</span><span class='chip'>决赛90分钟 0-0</span><span class='chip'>加时 1-0</span><a class='chip' href='./accuracy/'>准确率副页</a></div></header>
<h2>总成绩｜校准口径 {m['settled']} 场</h2><section class='metrics'><div class='metric'>总进球<strong>{m['total_goal_hits']}/{m['settled']} · {m['total_goal_rate']}</strong></div><div class='metric'>主比分<strong>{m['main_score_hits']}/{m['settled']} · {m['main_score_rate']}</strong></div><div class='metric'>比分池前三<strong>{m['score_pool_hits']}/{m['settled']} · {m['score_pool_rate']}</strong></div><div class='metric'>胜平负<strong>{m['wdl_hits']}/{m['settled']} · {m['wdl_rate']}</strong></div></section>
<section class='card note'><p><strong>全量原始表现：</strong>{raw['settled']} 场（含季军赛特殊样本103）：总进球 {raw['total_goal_rate']}、主比分 {raw['main_score_rate']}、比分池前三 {raw['score_pool_rate']}、胜平负 {raw['wdl_rate']}。排除样本仍在逐场表中展示，不能从复盘中消失。</p><p><strong>决赛104：</strong>主比分1-1未中；前三池未中；完整池的0-0覆盖但不抬高前三池准确率；胜平负按主比分映射为“平”并命中；2球主线未中。西班牙加时1-0夺冠与竞彩90分钟结算分开记录。</p></section>
<h2>分阶段表现</h2><section class='card tableWrap'><table><thead><tr><th>阶段</th><th>场数</th><th>总进球</th><th>主比分</th><th>比分池前三</th><th>胜平负</th></tr></thead><tbody>{stage_rows}</tbody></table></section>
<h2>这次复盘沉淀出的判断</h2><section class='card'><ul><li>最稳定的是胜平负（{m['wdl_rate']}），适合作为第一层输出；精确比分最低（{m['main_score_rate']}），不能承担“稳胆”叙事。</li><li>前三比分池把主比分覆盖率从 {m['main_score_rate']} 提升到 {m['score_pool_rate']}，说明场景分层有效，但必须保留排序纪律。</li><li>实际平局 {summary['diagnostics']['actual_draws']} 场，主比分预测平局 {summary['diagnostics']['predicted_draws']} 场；以后应做平局概率校准，不能靠“防平”模糊结算。</li><li>共有 {summary['diagnostics']['high_score_undercoverage_misses']} 场高比分失误属于主比分至少少估2球，尾部扩展仍是主要结构性短板。</li><li>总进球含单值与明确区间两种历史表达，后续统一输出“核心单值 + 保护区间”，分别统计，避免口径漂移。</li></ul></section>
<h2>可复用方法论</h2><section class='card'><ol>{methods}</ol><details><summary>查看精确结算口径</summary><ul>{settlement}</ul></details></section>
<h2>全部逐场复盘</h2><section class='card tableWrap'><table><thead><tr><th>日期</th><th>场次</th><th>阶段</th><th>对阵</th><th>90分钟赛果</th><th>总进球</th><th>主比分</th><th>比分池前三</th><th>胜平负</th><th>校准</th></tr></thead><tbody>{rows}</tbody></table></section>
<h2>数据来源</h2><section class='card'><ul><li><a href='{GROUP_RESULT_SOURCE}'>FIFA 官方全赛程与赛果</a></li><li><a href='{FINAL_RESULT_SOURCE}'>AP 决赛报道：90分钟0-0，西班牙加时1-0</a></li><li>项目内赛前 JSON、淘汰赛预测归档和赛果归档；脚本只连接赛前记录，不用赛后文本反推。</li></ul></section><footer>{DISCLAIMER}</footer></main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    rows = collect_rows(args.root)
    summary = build_summary(rows)
    save(args.root / "data" / "tournament_review_20260720.json", summary)
    page = render(summary)
    write(args.root / "index.html", page)
    write(args.root / "accuracy" / "index.html", page.replace("href='./accuracy/'", "href='../index.html'").replace("准确率副页", "返回主页面"))
    print(json.dumps({"coverage": summary["coverage"], "metrics": summary["calibration_metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
