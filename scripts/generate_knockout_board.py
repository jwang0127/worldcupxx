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
DATA_DIR = ROOT / "data"


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


def parse_markdown_table(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
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
    mismatches: list[dict[str, str]] = []
    fields = ["场次编号", "轮次", "名义主队中文", "名义客队中文", "北京时间", "胜者晋级比赛ID"]
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
                "beijing_date": row["北京日期"],
                "beijing_time": row["北京开球时间"],
                "beijing_timezone": row["北京时区"],
                "status": row["比赛状态"],
                "winner_advances_to": row["胜者晋级比赛ID"],
                "note": row["备注"],
            }
        )
    return out


def latest_standings() -> list[dict[str, Any]]:
    candidates = sorted(ROOT.glob("20*/standings_*.json"), reverse=True)
    for path in candidates:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return []


def team_key(name: str) -> str:
    name = TEAM_ALIAS.get(name, name)
    return re.sub(r"\s+", "", name).lower()


def qualified_team_stats(schedule: list[dict[str, Any]]) -> list[dict[str, Any]]:
    first_round = [item for item in schedule if item["stage_order"] == 1 and not item["home_team"].startswith("待定")]
    team_order: list[tuple[str, str, str]] = []
    for item in first_round:
        team_order.append((item["home_team"], item["home_code"], item["game_id"]))
        team_order.append((item["away_team"], item["away_code"], item["game_id"]))

    standings_lookup: dict[str, dict[str, Any]] = {}
    for group in latest_standings():
        for row in group.get("rows", []):
            copied = dict(row)
            copied["group"] = group.get("group", copied.get("group", ""))
            standings_lookup[team_key(str(row.get("team", "")))] = copied

    stats = []
    seen = set()
    for name, code, game_id in team_order:
        if name in seen:
            continue
        seen.add(name)
        row = standings_lookup.get(team_key(name), {})
        rank = int(float(row.get("rank", 0) or 0))
        if rank == 1:
            path = "小组第1"
        elif rank == 2:
            path = "小组第2"
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


def first_prediction(schedule: list[dict[str, Any]]) -> dict[str, Any]:
    match = next(item for item in schedule if item["game_id"] == "53452545")
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
        "model_version": "v2-knockout-score-first",
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
        "extra_time_penalty_script": "90分钟1-1，加拿大加时/点球小优。",
        "score_confidence": 0.61,
        "direction_confidence": 0.56,
        "data_completeness": 0.82,
        "score_matrix_top": [
            {"score": "1-1", "probability": 0.176, "label": "主比分"},
            {"score": "0-1", "probability": 0.142, "label": "加拿大小胜"},
            {"score": "1-2", "probability": 0.116, "label": "尾部上修"},
            {"score": "0-0", "probability": 0.104, "label": "平局保护"},
            {"score": "1-0", "probability": 0.092, "label": "南非冷门"},
            {"score": "2-1", "probability": 0.074, "label": "南非开放冷门"},
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
            "加拿大小组赛进攻效率和净胜球更好，但南非淘汰赛首场具备压低节奏能力，1-1 是主脚本。",
            "若南非先丢球，比赛会进入 1-2 的开放路径；若加拿大久攻不下，0-0/1-1 会把比赛拖向加时。",
        ],
        "risks": [
            "淘汰赛首战保守程度可能高于小组赛，比分仓位不宜重。",
            "若加拿大边路早早打穿，0-1 会升级为 1-2。",
            "若南非定位球先手，1-0 冷门路径成立。",
        ],
    }


def dt_bjt(value: str) -> datetime:
    cleaned = value.replace(" +08:00", "")
    return datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def render_score_matrix(rows: list[dict[str, Any]]) -> str:
    return "".join(
        f"<tr><td>{esc(item['score'])}</td><td>{float(item['probability']) * 100:.1f}%</td><td>{esc(item['label'])}</td></tr>"
        for item in rows
    )


def render_qualified_stats(stats: list[dict[str, Any]]) -> str:
    rows = []
    for item in stats:
        rows.append(
            "<tr>"
            f"<td>{esc(item['team_name'])}</td><td>{esc(item['team_code'])}</td><td>{esc(item['group'])}</td>"
            f"<td>{esc(item['qualifying_path'])}</td><td>{item['wins']}</td><td>{item['draws']}</td><td>{item['losses']}</td>"
            f"<td>{item['goals_for']}</td><td>{item['goals_against']}</td><td>{item['goal_difference']}</td>"
            f"<td>{esc(item['first_knockout_match_id'])}</td></tr>"
        )
    return "".join(rows)


def render_upcoming(schedule: list[dict[str, Any]], start: datetime) -> str:
    end = start + timedelta(days=3)
    matches = [item for item in schedule if start <= dt_bjt(item["kickoff_bjt"]) < end and not item["home_team"].startswith("待定")]
    matches.sort(key=lambda item: (item["beijing_date"], item["beijing_time"], int(item["match_no"])))
    rows = []
    for item in matches:
        rows.append(
            "<tr>"
            f"<td>{esc(item['beijing_date'][5:])} {esc(item['beijing_time'])}</td>"
            f"<td>{esc(item['match_no'])}</td><td>{esc(item['round'])}</td>"
            f"<td>{esc(item['home_team'])} vs {esc(item['away_team'])}</td>"
            f"<td>{esc(item['winner_advances_to'])}</td></tr>"
        )
    return "".join(rows)


def render_group_archive() -> str:
    dirs = sorted([p for p in ROOT.glob("2026*") if p.is_dir() and re.match(r"^202606\d{2}$", p.name)], reverse=True)
    links = "".join(f'<a href="../{p.name}/">{p.name}</a>' for p in dirs)
    return f'<details class="archive"><summary>小组赛预测</summary><div class="archiveLinks">{links}</div></details>'


def render_knockout_page(schedule: list[dict[str, Any]], stats: list[dict[str, Any]], prediction: dict[str, Any]) -> str:
    today = datetime(2026, 6, 28)
    upcoming_rows = render_upcoming(schedule, today)
    qualified_rows = render_qualified_stats(stats)
    matrix_rows = render_score_matrix(prediction["score_matrix_top"])
    analysis = "".join(f"<li>{esc(item)}</li>" for item in prediction["analysis"])
    risks = "".join(f"<li>{esc(item)}</li>" for item in prediction["risks"])
    archive = render_group_archive()
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026世界杯淘汰赛预测看板</title>
<style>
:root{{--bg:#06120f;--panel:#102528;--line:#1f4a43;--text:#e9fff8;--muted:#9bb8b0;--green:#33e28a;--blue:#7dd3fc;--orange:#ffad4d;--red:#ff5a63}}
*{{box-sizing:border-box}}body{{margin:0;font-family:"Microsoft YaHei",Arial,sans-serif;background:linear-gradient(135deg,#020807,#071b2a);color:var(--text)}}a{{color:var(--blue);text-decoration:none}}
header,main{{max-width:1240px;margin:auto;padding:24px 18px}}header{{position:sticky;top:0;background:rgba(3,12,11,.9);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);z-index:5}}
h1{{margin:0 0 12px;font-size:clamp(28px,5vw,44px)}}nav{{display:flex;gap:10px;flex-wrap:wrap}}nav a,.archive summary{{padding:9px 12px;border:1px solid var(--line);border-radius:8px;background:#0b201d;color:#8fffd0;cursor:pointer}}
.section{{margin:22px 0 34px}}.section h2{{color:var(--blue);font-size:26px}}.card,.panel,.archive{{border:1px solid var(--line);border-radius:8px;background:linear-gradient(180deg,rgba(16,37,40,.96),rgba(9,26,29,.96));box-shadow:0 16px 36px rgba(0,0,0,.24);padding:18px;margin:16px 0}}
.heroGrid,.coreGrid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}}.coreGrid{{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:850px){{.heroGrid,.coreGrid{{grid-template-columns:1fr}}}}
.metric{{background:#071817;border:1px solid #1f4a43;border-radius:8px;padding:14px}}.metric strong{{display:block;color:var(--green);font-size:24px;margin-top:4px}}
.bigScore{{font-size:48px;color:var(--green);font-weight:900}}.adv{{color:var(--orange);font-weight:900}}.muted{{color:var(--muted)}}.tableWrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;min-width:860px}}th,td{{padding:11px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{color:#8fffd0;background:#09211e}}
ul{{line-height:1.8}}.scoreTag{{display:inline-block;margin:4px 8px 4px 0;padding:8px 12px;border-radius:8px;border:1px solid #2ecf7a;background:#0d3028;color:#a8ffd6;font-weight:800}}.danger{{border-color:var(--red);color:#ffd2b0;background:#331415}}
.archiveLinks{{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}}.archiveLinks a{{padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:#071817}}
footer{{color:#8ea8a1;font-size:13px;margin-top:36px}}
</style>
</head>
<body>
<header>
  <h1>2026世界杯淘汰赛预测看板</h1>
  <nav><a href="#today">首场预测</a><a href="#upcoming">未来三天比赛</a><a href="#qualified">32强球队当前战绩</a><a href="#archive">小组赛预测</a></nav>
</header>
<main>
  <section class="section" id="today">
    <h2>首场淘汰赛预测：{esc(prediction['home_team'])} vs {esc(prediction['away_team'])}</h2>
    <div class="card">
      <div class="heroGrid">
        <div class="metric">轮次<strong>{esc(prediction['round'])}</strong></div>
        <div class="metric">北京时间<strong>{esc(prediction['kickoff_bjt'].replace(' +08:00',''))}</strong></div>
        <div class="metric">90分钟方向<strong>{esc(prediction['direction_text'])}</strong></div>
        <div class="metric">晋级倾向<strong class="adv">{esc(prediction['advance_pick'])}</strong></div>
      </div>
      <div class="coreGrid">
        <div class="panel"><h3>主比分</h3><div class="bigScore">{esc(prediction['main_score'])}</div><p class="muted">比分置信：{float(prediction['score_confidence']) * 100:.0f}%</p></div>
        <div class="panel"><h3>比分池</h3><span class="scoreTag">{esc(prediction['safe_scores'][0])}</span><span class="scoreTag">{esc(prediction['safe_scores'][1])}</span><span class="scoreTag">{esc(prediction['draw_protection_scores'][0])}</span><span class="scoreTag danger">{esc(prediction['upset_score'])}</span></div>
        <div class="panel"><h3>晋级概率</h3><p>{esc(prediction['home_team'])}: {prediction['home_advance_probability'] * 100:.0f}%</p><p>{esc(prediction['away_team'])}: {prediction['away_advance_probability'] * 100:.0f}%</p><p>{esc(prediction['extra_time_penalty_script'])}</p></div>
      </div>
      <div class="coreGrid">
        <div class="panel"><h3>剧本分析</h3><p>{esc(prediction['scenario']['home_win_script'])}</p><p>{esc(prediction['scenario']['away_win_script'])}</p><p>{esc(prediction['scenario']['home_loss_script'])}</p><p>{esc(prediction['scenario']['away_loss_script'])}</p></div>
        <div class="panel"><h3>分析依据</h3><ul>{analysis}</ul></div>
        <div class="panel"><h3>风险提示</h3><ul>{risks}</ul></div>
      </div>
      <div class="tableWrap"><table><thead><tr><th>比分</th><th>概率</th><th>标签</th></tr></thead><tbody>{matrix_rows}</tbody></table></div>
    </div>
  </section>
  <section class="section" id="upcoming"><h2>未来三天比赛（北京时间）</h2><div class="card tableWrap"><table><thead><tr><th>北京时间</th><th>场次</th><th>轮次</th><th>对阵</th><th>胜者进入</th></tr></thead><tbody>{upcoming_rows}</tbody></table></div></section>
  <section class="section" id="qualified"><h2>32强球队当前战绩</h2><div class="card tableWrap"><table><thead><tr><th>球队</th><th>代码</th><th>小组</th><th>出线路径</th><th>胜</th><th>平</th><th>负</th><th>进</th><th>失</th><th>净胜</th><th>首场淘汰赛</th></tr></thead><tbody>{qualified_rows}</tbody></table></div></section>
  <section class="section" id="archive"><h2>小组赛历史预测</h2>{archive}</section>
  <footer>赛程主源：2026世界杯淘汰赛赛程表_中文版_Codex.md；Excel 用于一致性校验。模型：v2-knockout-score-first。仅供娱乐分析参考。</footer>
</main>
</body>
</html>"""


def main() -> int:
    md_rows = parse_markdown_table(SCHEDULE_MD)
    xlsx_rows = read_excel_rows(SCHEDULE_XLSX)
    verification = verify_schedule(md_rows, xlsx_rows)
    if verification["mismatches"]:
        raise RuntimeError("Knockout schedule markdown/xlsx mismatch: " + json.dumps(verification, ensure_ascii=False))

    schedule = normalize_schedule(md_rows)
    stats = qualified_team_stats(schedule)
    prediction = first_prediction(schedule)

    write_json(DATA_DIR / "knockout_schedule.json", {"source": str(SCHEDULE_MD.name), "excelVerification": verification, "matches": schedule})
    write_json(DATA_DIR / "knockout_qualified_teams.json", stats)
    write_json(DATA_DIR / "knockout_predictions_20260629.json", {"date": "20260629", "stage": "knockout", "matches": [prediction]})

    html_text = render_knockout_page(schedule, stats, prediction)
    knockout_dir = ROOT / "knockout"
    day_dir = ROOT / "20260629"
    knockout_dir.mkdir(exist_ok=True)
    day_dir.mkdir(exist_ok=True)
    (knockout_dir / "index.html").write_text(html_text, encoding="utf-8")
    (day_dir / "index.html").write_text(html_text, encoding="utf-8")
    (day_dir / "predict_20260629.html").write_text(html_text, encoding="utf-8")
    (ROOT / "index.html").write_text(html_text, encoding="utf-8")

    model_copy = knockout_dir / "world_cup_knockout_model_optimization_codex.md"
    if MODEL_MD.exists():
        shutil.copyfile(MODEL_MD, model_copy)

    print("Generated knockout dashboard:")
    print(ROOT / "index.html")
    print(day_dir / "predict_20260629.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
