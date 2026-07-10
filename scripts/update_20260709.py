#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATE = "20260709"


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_match(date: str, match_no: str) -> dict[str, Any] | None:
    path = DATA_DIR / f"{date}.json"
    if not path.exists():
        return None
    payload = read_json(path)
    for item in payload.get("matches", []):
        if str(item.get("id", "")).lstrip("0") == str(match_no):
            return item
    return None


def odds_value(match: dict[str, Any] | None, pool: str, key: str, default: str = "-") -> str:
    if not match:
        return default
    return str(match.get("odds", {}).get(pool, {}).get(key, default) or default)


def external_99() -> dict[str, str]:
    return {
        "source": "Sky Bet胜平负：挪威 16/5，平 13/5，英格兰 5/6；Polymarket概率参考：挪威23%，平27%，英格兰53%。",
        "had": "4.20 / 3.60 / 1.83",
        "prob": "23% / 27% / 53%",
        "updated": "2026-07-08网页抓取",
    }


def external_100() -> dict[str, str]:
    return {
        "source": "Sky Bet胜平负：阿根廷 7/10，平 5/2，瑞士 17/4；Sporttery接口没有返回这场竞彩细项。",
        "had": "1.70 / 3.50 / 5.25",
        "prob": "外部胜平负折算后：阿根廷约56%，平约27%，瑞士约18%。",
        "updated": "2026-07-08网页抓取",
    }


def css() -> str:
    return """
:root{--bg:#071310;--card:#10221f;--panel:#132b26;--line:#24483f;--text:#eefbf6;--muted:#9ab7ae;--green:#58d68d;--blue:#73c7ff;--gold:#f2c15a;--red:#ff817b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;line-height:1.65}
header{padding:24px 18px 12px;max-width:1180px;margin:auto}h1{margin:0 0 14px;font-size:32px;letter-spacing:0}
nav{display:flex;gap:10px;flex-wrap:wrap}nav a{color:var(--text);text-decoration:none;border:1px solid var(--line);border-radius:8px;padding:7px 10px;background:#0c1b18}
main{max-width:1180px;margin:auto;padding:0 18px 42px}.section{margin-top:22px}.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin-top:12px}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}.panel{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:12px}
.metric strong{display:block;color:var(--green);font-size:24px}.metric small,.muted{color:var(--muted)}.good{color:var(--green)}.warn{color:var(--gold)}.bad{color:var(--red)}
.tableWrap{overflow:auto}table{width:100%;border-collapse:collapse;min-width:760px}th,td{border-bottom:1px solid var(--line);padding:9px;text-align:left;vertical-align:top}th{color:var(--blue);font-weight:700}
.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:3px 8px;margin:2px;background:#0c1b18}
details{background:var(--card);border:1px solid var(--line);border-radius:8px;margin-top:14px;overflow:hidden}summary{cursor:pointer;padding:15px 16px;display:grid;grid-template-columns:1fr auto 1.4fr;gap:12px;align-items:center}summary strong{color:var(--green);font-size:24px}
.body{border-top:1px solid var(--line);padding:16px}.analysisTables{display:grid;grid-template-columns:minmax(260px,.62fr) minmax(0,1.38fr);gap:12px;align-items:start}.scoreMatrix table,.evTable table{min-width:0}.evTable table{table-layout:fixed}.evTable td{word-break:break-word}
@media(max-width:900px){.grid,.cols,summary,.analysisTables{grid-template-columns:1fr}h1{font-size:26px}table{min-width:680px}.scoreMatrix table,.evTable table{min-width:0}}
"""


def build_matches() -> list[dict[str, Any]]:
    m97 = load_match("20260710", "97")
    m98 = load_match("20260711", "98")
    e99 = external_99()
    e100 = external_100()
    return [
        {
            "match_no": "97",
            "match_num": "周四097",
            "home": "法国",
            "away": "摩洛哥",
            "kickoff": "07-10 04:00",
            "venue": m97.get("venue", "美国-马萨诸塞州福克斯伯勒") if m97 else "美国-马萨诸塞州福克斯伯勒",
            "main_score": "2-0",
            "direction": "法国90分钟胜优先，防平",
            "advance": "法国",
            "goals": "2-3球，防1球",
            "half": "法国 1-0 摩洛哥",
            "hafu": "胜胜 / 平胜",
            "probability": "90分钟：法国胜 62% / 平 25% / 摩洛哥胜 13%；最终晋级：法国 72% / 摩洛哥 28%",
            "rationale": "法国实力、阵容深度和转换效率仍高于摩洛哥，但1.42主胜只能说明方向清晰，不能直接推出穿盘或大胜。摩洛哥连续淘汰赛韧性强，能把节奏拖窄，所以主线是2-0，防2-1和1-1；如果法国早球，3-1才进入尾部。",
            "review": "昨日阿根廷3-2说明强队优势可能被补时和二次提速放大，瑞士0-0说明低位锁局与点球路径真实存在。本场不按昨天大比分追大，也不因0-0追小，而是按法国进攻质量与摩洛哥抗压能力做2球主线。",
            "score_rows": [
                ("2-0", "19.0%", "+0.04", "法国正路零封"),
                ("2-1", "15.0%", "+0.03", "摩洛哥定位球/反击破门"),
                ("1-0", "14.0%", "+0.02", "低节奏小胜"),
                ("1-1", "10.0%", "防冷", "摩洛哥拖入加时"),
                ("3-1", "9.0%", "尾部", "法国早球后拉开"),
                ("0-0", "6.0%", "保护", "吸收昨日0-0漏池教训"),
            ],
            "ev_rows": [
                ("法国90分钟方向", "62.0%", "1.61", odds_value(m97, "had", "home"), "方向确认", "实力和赔率同向，但主胜低赔不单独作为结论。"),
                ("比分：2-0 / 2-1 / 1-0", "48.0%", "2.08", f"{odds_value(m97,'crs','2-0')} / {odds_value(m97,'crs','2-1')} / {odds_value(m97,'crs','1-0')}", "+0.04", "主池覆盖法国小胜、摩洛哥进球保护和低比分。"),
                ("总进球：2球 / 3球", "57.0%", "1.75", f"{odds_value(m97,'ttg','s2')} / {odds_value(m97,'ttg','s3')}", "+0.03", "2球最低，3球用于早球或摩洛哥追分路径。"),
                ("半全场：胜胜 / 平胜", "47.0%", "2.13", f"{odds_value(m97,'hafu','hh')} / {odds_value(m97,'hafu','dh')}", "+0.02", "胜胜对应法国早段优势；平胜对应摩洛哥上半场拖窄。"),
            ],
            "insights": [
                ("比分池", "稳胆2-0、2-1、1-0；防冷1-1、0-0；尾部3-1。"),
                ("伤停/体能", "未发现新增硬伤停，摩洛哥连续高压淘汰赛后的体能消耗需要计入。"),
                ("串关", "适合作为二串一第一腿方向或总进球2/3，比分串只低仓位。"),
            ],
            "team_reading": [
                "法国强在前场冲击、边路速度和领先后的节奏管理。",
                "摩洛哥强在低位站位和淘汰赛抗压，弱点是长时间被压后的出球质量。",
                "赔率支持法国方向，但比分池必须保留1-0、1-1和0-0保护。"
            ],
            "triggers": [
                "法国30分钟前进球：2-0和3-1升权，1-0降权。",
                "半场0-0：1-0、1-1和0-0升权，胜胜半全场降权。",
                "摩洛哥先进球：2-1和1-1升权，总进球3球进入主池。"
            ],
            "odds_snapshot": f"HAD {odds_value(m97,'had','home')}/{odds_value(m97,'had','draw')}/{odds_value(m97,'had','away')}；TTG低位：2球 {odds_value(m97,'ttg','s2')}，3球 {odds_value(m97,'ttg','s3')}；比分低位参考：2-0 {odds_value(m97,'crs','2-0')}，2-1 {odds_value(m97,'crs','2-1')}，1-0 {odds_value(m97,'crs','1-0')}，1-1 {odds_value(m97,'crs','1-1')}；半全场：胜胜 {odds_value(m97,'hafu','hh')}，平胜 {odds_value(m97,'hafu','dh')}。来源：Sporttery data/20260710.json",
            "mystic": "玄学娱乐参考：按当地晚间开球看，法国盘面偏“先稳后动”，更像上半场试探、下半场兑现；只作为表达层参考，不进入主模型打分。",
        },
        {
            "match_no": "98",
            "match_num": "周五098",
            "home": "西班牙",
            "away": "比利时",
            "kickoff": "07-11 03:00",
            "venue": m98.get("venue", "美国-加利福尼亚州英格尔伍德") if m98 else "美国-加利福尼亚州英格尔伍德",
            "main_score": "2-0",
            "direction": "西班牙不败，主胜略优",
            "advance": "西班牙",
            "goals": "3球主线，防4球",
            "half": "西班牙 1-1 比利时",
            "hafu": "平胜 / 胜胜",
            "probability": "90分钟：西班牙胜 54% / 平 27% / 比利时胜 19%；最终晋级：西班牙 64% / 比利时 36%",
            "rationale": "西班牙控球、压迫和阵地战稳定性更好，但比利时上一轮1-4说明其领先后反击尾部不能删除。本场不是机械追大，而是两队攻击质量和落后方压上共同支持3球主线；比分池补入3-2，避免再次漏掉强队险胜高比分。",
            "review": "昨日3-2未入池的根因是尾部结构不完整，0-0未入池的根因是低节奏锁局保护不足。西班牙场既要保留1-1，也要保留3-2，不把结果简化成“大球惯性”。",
            "score_rows": [
                ("2-1", "18.0%", "+0.04", "西班牙主线小胜"),
                ("1-1", "15.0%", "+0.03", "比利时拖入加时"),
                ("3-1", "12.0%", "+0.02", "西班牙压制后扩大"),
                ("2-2", "10.0%", "防冷", "比利时反击持续有效"),
                ("3-2", "8.0%", "尾部", "吸收昨日3-2漏池教训"),
                ("1-3", "5.0%", "极冷", "比利时领先后反击放大"),
            ],
            "ev_rows": [
                ("西班牙不败/90分钟方向", "81.0%", "1.23", f"{odds_value(m98,'had','home')} / {odds_value(m98,'had','draw')}", "方向确认", "西班牙方向强，但平局权重不可删除。"),
                ("比分：2-1 / 1-1 / 3-1 / 3-2", "53.0%", "1.89", f"{odds_value(m98,'crs','2-1')} / {odds_value(m98,'crs','1-1')} / {odds_value(m98,'crs','3-1')} / {odds_value(m98,'crs','3-2')}", "+0.04", "主池覆盖正路、平局保护和高比分尾部。"),
                ("总进球：3球 / 4球", "55.0%", "1.82", f"{odds_value(m98,'ttg','s3')} / {odds_value(m98,'ttg','s4')}", "+0.03", "3球最低，4球用于比利时反击和追分路径。"),
                ("半全场：平胜 / 胜胜", "43.0%", "2.33", f"{odds_value(m98,'hafu','dh')} / {odds_value(m98,'hafu','hh')}", "+0.02", "平胜更贴合上半场互有机会、下半场西班牙控场。"),
            ],
            "insights": [
                ("比分池", "稳胆2-1、1-1、3-1；防冷2-2；尾部3-2和1-3。"),
                ("伤停/体能", "未发现新增硬伤停，比利时进攻状态上修，防线稳定性不盲目上修。"),
                ("串关", "适合做总进球3/4或西班牙不败，比分串需保留3-2。"),
            ],
            "team_reading": [
                "西班牙强在中前场压迫、控球连续性和禁区前小范围配合。",
                "比利时强在转换和领先后的纵深利用，弱点是防线回收后的持续抗压。",
                "赔率不能直接决定结果，但与实力画像一致：西班牙略优，平局和尾部必须同时保留。"
            ],
            "triggers": [
                "半场1-1或0-0：2-1、1-1继续升权，平胜优先。",
                "西班牙先进球：2-1/3-1升权，3球总进球最稳。",
                "比利时先进球：2-2、3-2和1-3升权，比赛进入尾部风险。"
            ],
            "odds_snapshot": f"HAD {odds_value(m98,'had','home')}/{odds_value(m98,'had','draw')}/{odds_value(m98,'had','away')}；TTG低位：3球 {odds_value(m98,'ttg','s3')}，4球 {odds_value(m98,'ttg','s4')}，2球 {odds_value(m98,'ttg','s2')}；比分低位参考：2-1 {odds_value(m98,'crs','2-1')}，1-1 {odds_value(m98,'crs','1-1')}，3-1 {odds_value(m98,'crs','3-1')}，2-2 {odds_value(m98,'crs','2-2')}，3-2 {odds_value(m98,'crs','3-2')}；半全场：平胜 {odds_value(m98,'hafu','dh')}，胜胜 {odds_value(m98,'hafu','hh')}。来源：Sporttery data/20260711.json",
            "mystic": "玄学娱乐参考：当地傍晚开球更偏节奏拉扯，西班牙后程控场感更强；这只作为娱乐区块，不能覆盖赔率、实力和战术判断。",
        },
        {
            "match_no": "99",
            "match_num": "099",
            "home": "挪威",
            "away": "英格兰",
            "kickoff": "07-12 05:00",
            "venue": "待官方竞彩开盘后复核",
            "main_score": "1-2",
            "direction": "英格兰不败，防90分钟平",
            "advance": "英格兰",
            "goals": "2-3球，防0-0和4球尾部",
            "half": "挪威 0-1 英格兰",
            "hafu": "平负 / 负负",
            "probability": "90分钟：挪威胜 22% / 平 29% / 英格兰胜 49%；最终晋级：挪威 38% / 英格兰 62%",
            "rationale": "Sporttery接口没有返回这场竞彩细项，但外部盘已经给出英格兰低赔。挪威不是纯弱队，它有高点、反击和早段冲击，能把比赛拖成转换战；英格兰整体深度、控场和淘汰赛管理更好，所以方向是英格兰不败、最终晋级偏英格兰。比分池不能只写1-2，必须同时留1-1、2-2和2-3。",
            "review": "昨日瑞士0-0提醒，强队不败并不等于90分钟必胜；昨日阿根廷3-2提醒，落后方压上会放大尾部。本场主线1-2，但1-1、0-1、2-2、2-3都必须在池内。",
            "score_rows": [
                ("1-2", "17.0%", "+0.03", "英格兰主线小胜"),
                ("1-1", "15.0%", "+0.03", "90分钟平局保护"),
                ("0-1", "12.0%", "+0.02", "英格兰低比分兑现"),
                ("2-2", "10.0%", "防冷", "挪威高点持续制造威胁"),
                ("2-3", "7.0%", "尾部", "落后方压上后的二次提速"),
                ("0-0", "6.0%", "保护", "低节奏锁局"),
            ],
            "ev_rows": [
                ("英格兰不败方向", "78.0%", "1.28", f"外部胜平负 {e99['had']}", "方向确认", "Sky Bet和Polymarket都偏英格兰，但平局权重不低。"),
                ("比分：1-2 / 1-1 / 0-1 / 2-3", "51.0%", "1.96", "竞彩比分盘暂缺", "+0.03", "同时覆盖英格兰小胜、平局和尾部反超。"),
                ("总进球：2球 / 3球", "53.0%", "1.89", "竞彩总进球盘暂缺", "+0.02", "2-3球为主，4-5球只在早球后升权。"),
                ("半全场：平负 / 负负", "41.0%", "2.44", "竞彩半全场盘暂缺", "待复核", "半场僵持或英格兰领先两条路径并存。"),
            ],
            "insights": [
                ("比分池", "稳胆1-2、1-1、0-1；防冷2-2；尾部2-3和0-0。"),
                ("伤停/体能", "竞彩细项暂缺，临场需复核伤停和首发；外部胜平负先作为方向参考。"),
                ("串关", "可作为英格兰不败观察腿；竞彩细项开盘后再决定是否进入主票。"),
            ],
            "team_reading": [
                "挪威冲击力和高点优势明显，能让比赛从控球战变成转换战。",
                "英格兰阵容深度和淘汰赛管理更好，但不能忽略90分钟平局。",
                "当前用外部胜平负校准方向；竞彩细项出来后，比分和半全场必须重新校准。"
            ],
            "triggers": [
                "英格兰先进球：0-1和1-2升权，2-3降权。",
                "挪威先进球：1-1、2-2和2-3升权。",
                "半场0-0：0-1、1-1和0-0升权，总进球下修。"
            ],
            "odds_snapshot": f"{e99['source']} 当前页面用外部胜平负/概率校准方向；竞彩HAD、TTG、比分和半全场开盘后必须替换。",
            "mystic": "玄学娱乐参考：当地傍晚开球，英格兰盘面更像后程发力；挪威若先破门，卦象层面的“动中生变”只提示防2-2/2-3，不改变主模型英格兰不败。",
        },
        {
            "match_no": "100",
            "match_num": "100",
            "home": "阿根廷",
            "away": "瑞士",
            "kickoff": "07-12 09:00",
            "venue": "待官方竞彩开盘后复核",
            "main_score": "1-0",
            "direction": "阿根廷胜优先，强防平",
            "advance": "阿根廷",
            "goals": "1-2球，防0-0和3-2尾部",
            "half": "阿根廷 0-0 瑞士",
            "hafu": "平胜 / 平平",
            "probability": "90分钟：阿根廷胜 56% / 平 30% / 瑞士胜 14%；最终晋级：阿根廷 68% / 瑞士 32%",
            "rationale": "Sporttery接口没有返回这场竞彩细项，外部盘把阿根廷放在明显优势位。阿根廷上一场3-2说明强势不等于稳定零封，瑞士刚刚0-0点球晋级，说明低位防守和拖到点球的路是真实存在的。本场不能因为阿根廷昨天大比分就追大，主线回到阿根廷小胜和瑞士锁局：1-0/2-0为正路，1-1/0-0为核心保护，3-2只作被迫二次提速尾部。",
            "review": "昨日两个真实结果直接修正比分池：3-2和0-0都必须进入未来相关场景的尾部或保护池。本场阿根廷强，但瑞士的0-0路径不能删。",
            "score_rows": [
                ("1-0", "18.0%", "+0.04", "阿根廷小胜正路"),
                ("2-0", "15.0%", "+0.03", "阿根廷压制零封"),
                ("1-1", "13.0%", "防冷", "瑞士拖入加时"),
                ("0-0", "9.0%", "保护", "吸收昨日0-0漏池教训"),
                ("2-1", "9.0%", "延展", "瑞士破门保护"),
                ("3-2", "5.0%", "尾部", "吸收昨日3-2漏池教训"),
            ],
            "ev_rows": [
                ("阿根廷胜/不败方向", "86.0%", "1.16", f"外部胜平负 {e100['had']}", "方向确认", "阿根廷优势清楚，但90分钟平局保护很重。"),
                ("比分：1-0 / 2-0 / 1-1 / 0-0", "55.0%", "1.82", "竞彩比分盘暂缺", "+0.04", "低比分正路和瑞士锁局同时进入主池。"),
                ("总进球：1球 / 2球", "52.0%", "1.92", "竞彩总进球盘暂缺", "+0.03", "不因阿根廷上一场3-2就机械追大。"),
                ("半全场：平胜 / 平平", "44.0%", "2.27", "竞彩半全场盘暂缺", "待复核", "瑞士上半场拖窄概率高，阿根廷下半场兑现是主路径。"),
            ],
            "insights": [
                ("比分池", "稳胆1-0、2-0；防冷1-1、0-0；尾部2-1、3-2。"),
                ("伤停/体能", "阿根廷补时大战和瑞士点球大战都计入体能折损。"),
                ("串关", "方向可做观察腿，精确比分不适合重仓。"),
            ],
            "team_reading": [
                "阿根廷强在控场和关键球员处理最后一击。",
                "瑞士强在低位阵型、门前保护和点球路径。",
                "竞彩细项暂缺，当前用外部胜平负校准方向，不能把上一场比分机械搬到本场。"
            ],
            "triggers": [
                "半场0-0：1-0、1-1、0-0升权。",
                "阿根廷早球：2-0、2-1升权，3-2仍只作尾部。",
                "瑞士先进球：1-1和2-1升权，阿根廷90分钟胜率下调。"
            ],
            "odds_snapshot": f"{e100['source']} {e100['prob']} 当前页面用外部胜平负校准方向；竞彩HAD、TTG、比分和半全场开盘后必须替换。",
            "mystic": "玄学娱乐参考：当地夜间开球偏慢热，阿根廷更像下半场兑现；瑞士的“守到点球”路径在娱乐参考里也有共振，因此0-0/1-1必须保留。",
        },
    ]


def build_review() -> dict[str, Any]:
    return {
        "headline": "07-08复盘：3-2和0-0同时漏池，问题是比分池结构不完整，不是大小球惯性",
        "summary": "阿根廷3-2埃及说明强队方向正确也可能被补时、追分和二次提速放大；瑞士0-0点球淘汰哥伦比亚说明淘汰赛低位锁局、拖入加时点球的路径必须保留。今天不能因为昨天有3-2就追大，也不能因为0-0就追小，而是按实力、赔率、伤停/体能、战术路径逐场重算。",
        "lessons": [
            "比分池必须覆盖真实结构：3-2、0-0、1-1、2-2这类路径不能因为不是最低赔率就被删除。",
            "赔率只做校准，不直接得出结论；低赔强队仍可能是1-0或2-0，小赔方向也可能拖到加时。",
            "淘汰赛要分开判断90分钟结果和最终晋级，平局场景必须能对应加时/点球晋级。",
            "串关主线从精确比分降权，优先方向、总进球和半全场组合；比分串只保留小仓观察。",
            "未来四强席位赛按单场逻辑重算，不做昨天大比分/小比分的机械外推。"
        ],
    }


def build_parlay(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_no = {item["match_no"]: item for item in matches}
    def leg(no: str, score: str, goals: str, hafu: str, ev: str, note: str) -> dict[str, str]:
        item = by_no[no]
        return {
            "match_no": item["match_no"],
            "match": f"{item['home']} vs {item['away']}",
            "direction": item["direction"],
            "score": score,
            "goals": goals,
            "hafu": hafu,
            "ev": ev,
            "note": note,
        }
    return [
        {
            "title": "二串一主线",
            "summary": "97/98已有竞彩赔率，先用方向+总进球做主线，比分只辅助。",
            "legs": [
                leg("97", "2-0 / 2-1 / 1-0", "2 / 3球", "胜胜 / 平胜", "+0.03", "法国方向清晰，但摩洛哥拖窄能力要防。"),
                leg("98", "2-1 / 1-1 / 3-1", "3 / 4球", "平胜 / 胜胜", "+0.03", "西班牙不败为主，比利时反击尾部保留。"),
            ],
        },
        {
            "title": "三串一稳健",
            "summary": "第三腿用外部赔率校准英格兰不败，等竞彩开盘后复核比分和半全场。",
            "legs": [
                leg("97", "2-0 / 1-0", "2球", "胜胜 / 平胜", "+0.02", "法国小胜或零封路径。"),
                leg("98", "2-1 / 1-1", "3球", "平胜 / 胜胜", "+0.02", "西班牙方向，平局保护。"),
                leg("99", "1-2 / 1-1", "2 / 3球", "平负 / 负负", "外部赔率支持", "英格兰晋级优先，但防90分钟平。"),
            ],
        },
        {
            "title": "三串一防冷",
            "summary": "专门覆盖3-2、0-0、2-2等昨天暴露出的漏池类型。",
            "legs": [
                leg("98", "2-2 / 3-2", "4 / 5球", "平胜", "尾部", "比利时尾部不删除。"),
                leg("99", "2-2 / 2-3", "4 / 5球", "平负", "尾部", "挪威先进球或英格兰后程反超。"),
                leg("100", "1-1 / 0-0", "0 / 1 / 2球", "平平 / 平胜", "防冷", "瑞士锁局和点球路径必须覆盖。"),
            ],
        },
    ]


def render_parlay_group(group: dict[str, Any]) -> str:
    group = {**group, "legs": [x for x in group["legs"] if str(x.get("match_no")) != "97"]}
    if not group["legs"]:
        return ""
    rows = "".join(
        f"<tr><td>{esc(x['match_no'])}</td><td>{esc(x['match'])}</td><td>{esc(x['direction'])}</td><td>{esc(x['score'])}</td><td>{esc(x['goals'])}</td><td>{esc(x['hafu'])}</td><td>{esc(x['ev'])}</td><td>{esc(x['note'])}</td></tr>"
        for x in group["legs"]
    )
    return f"""<div class="card"><h3>{esc(group['title'])}</h3><p class="muted">{esc(group['summary'])}</p>
<div class="tableWrap"><table><thead><tr><th>场次</th><th>比赛</th><th>方向</th><th>比分池</th><th>总进球</th><th>半全场</th><th>EV</th><th>说明</th></tr></thead><tbody>{rows}</tbody></table></div></div>"""


def render_match(item: dict[str, Any]) -> str:
    scores = "".join(f"<tr><td>{esc(s)}</td><td>{esc(p)}</td><td>{esc(ev)}</td><td>{esc(label)}</td></tr>" for s, p, ev, label in item["score_rows"])
    ev_rows = "".join(f"<tr><td>{esc(m)}</td><td>{esc(p)}</td><td>{esc(f)}</td><td>{esc(o)}</td><td>{esc(ev)}</td><td>{esc(n)}</td></tr>" for m, p, f, o, ev, n in item["ev_rows"])
    insights = "".join(f"<div class='panel'><h3>{esc(t)}</h3><p>{esc(c)}</p></div>" for t, c in item["insights"])
    reading = "".join(f"<li>{esc(x)}</li>" for x in item["team_reading"])
    triggers = "".join(f"<li>{esc(x)}</li>" for x in item["triggers"])
    return f"""<details open><summary><span>{esc(item['match_num'])} {esc(item['home'])} vs {esc(item['away'])}</span><strong>{esc(item['main_score'])}</strong><em>{esc(item['direction'])} / 晋级 {esc(item['advance'])}</em></summary>
<div class="body">
<div class="grid">
<div class="panel metric">开球<strong>{esc(item['kickoff'])}</strong><small>{esc(item['venue'])}</small></div>
<div class="panel metric">半场<strong>{esc(item['half'])}</strong><small>半全场 {esc(item['hafu'])}</small></div>
<div class="panel metric">90分钟<strong>{esc(item['direction'])}</strong><small>{esc(item['goals'])}</small></div>
<div class="panel metric">晋级<strong>{esc(item['advance'])}</strong><small>{esc(item['probability'])}</small></div>
</div>
<div class="card"><h3>判断路径</h3><p>{esc(item['rationale'])}</p><p class="muted">{esc(item['review'])}</p></div>
<div class="analysisTables"><div class="card scoreMatrix"><h3>比分池</h3><div class="tableWrap"><table><thead><tr><th>比分</th><th>概率</th><th>EV</th><th>标签</th></tr></thead><tbody>{scores}</tbody></table></div></div>
<div class="card evTable"><h3>EV表</h3><div class="tableWrap"><table><thead><tr><th>市场</th><th>模型概率</th><th>公平赔率</th><th>市场赔率</th><th>EV</th><th>说明</th></tr></thead><tbody>{ev_rows}</tbody></table></div></div></div>
<div class="grid">{insights}</div>
<div class="cols"><div class="card"><h3>球队画像</h3><ul>{reading}</ul></div><div class="card"><h3>触发条件</h3><ul>{triggers}</ul></div></div>
<div class="card"><h3>玄学娱乐参考</h3><p class="muted">{esc(item.get('mystic', '玄学只作娱乐参考，不进入主模型打分。'))}</p></div>
<div class="card"><h3>赔率快照</h3><p class="muted">{esc(item['odds_snapshot'])}</p></div>
</div></details>"""


def render_page(matches: list[dict[str, Any]], review: dict[str, Any], parlay: list[dict[str, Any]]) -> str:
    lesson_items = "".join(f"<li>{esc(x)}</li>" for x in review["lessons"])
    parlay_html = "".join(render_parlay_group(group) for group in parlay)
    match_html = "".join(render_match(item) for item in matches if str(item.get("match_no")) != "97")
    future_update = """
<section class="section" id="postReviewUpdate"><h2>07-10 法国2-0复盘后的未来场次调整</h2>
<div class="card"><p><strong>复盘已回写后续比分池：</strong>强队方向明确、对手进攻受限、总进球低位时，零封小胜不能被平局保护稀释；对手有真实反击或追分能力时，仍保留开放比分尾部。</p>
<div class="tableWrap"><table><thead><tr><th>场次</th><th>原主线</th><th>复盘后更新</th><th>触发条件</th></tr></thead><tbody>
<tr><td>098 西班牙-比利时</td><td>2-1 / 1-1 / 3-1</td><td>保留2-1 / 1-1 / 3-1，并保留3-2与1-3尾部</td><td>比利时有转换和追分能力，不套用法国零封；比利时先入球上调2-2/3-2。</td></tr>
<tr><td>099 挪威-英格兰</td><td>1-2 / 1-1</td><td>新增0-1低比分兑现路径，核心为0-1 / 1-2 / 1-1</td><td>英格兰先入球走0-1/1-2；挪威先入球走1-1/2-2/2-3。</td></tr>
<tr><td>100 阿根廷-瑞士</td><td>1-0，防1-1/0-0</td><td>强化1-0 / 2-0零封小胜，继续保留1-1/0-0锁局</td><td>阿根廷早球上调2-0；半场0-0保留0-0/1-0/1-1，不机械追大。</td></tr>
</tbody></table></div></div></section>
"""
    future_update = future_update.replace("保留2-1 / 1-1 / 3-1，并保留3-2与1-3尾部", "更新为2-0 / 1-0 / 2-1，继续保留3-1/3-2尾部")
    future_update = future_update.replace("新增0-1低比分兑现路径，核心为0-1 / 1-2 / 1-1", "重新生成：1-2主线，1-1/2-2/2-3覆盖开放路径")
    future_update = future_update.replace("强化1-0 / 2-0零封小胜，继续保留1-1/0-0锁局", "重新生成：1-0 / 2-0主线，1-1/0-0锁局保护")
    match_html += future_update
    web_refresh = """
<section class="section" id="webRefresh"><div class="card"><h3>公开资料复核后的二次调整</h3>
<p>098：公开预览资料显示西班牙连续零封，且比利时中场存在伤情信息；比利时上一场4-1的强势表现同时含有对手防守失误因素，因此主线收窄到2-0，保留1-0/2-1和3-1尾部。</p>
<p>099：英格兰存在中后场人员与停赛风险，挪威本届比赛开放度较高；因此不把法国2-0复盘机械套成低比分，主线回到1-2，2-2/2-3作为追分尾部。</p>
<p>100：阿根廷方向仍明显，但瑞士低位锁局能力和点球路径保留；主线为1-0/2-0，0-0/1-1为保护。</p>
<p class="muted">资料来源：<a href="https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/match-schedule-fixtures-results-teams-stadiums">FIFA赛程</a>；<a href="https://apnews.com/article/0325e8102be7a88e852079deffd70ca0">AP比利时4-1美国赛后报道</a>；<a href="https://www.sportsmole.co.uk/football/spain/world-cup-2026/preview/spain-vs-belgium-prediction-team-news-lineups_600878.html">西班牙-比利时赛前资料</a>；<a href="https://www.sportsmole.co.uk/football/england/world-cup-2026/preview/norway-vs-england-prediction-team-news-lineups_600924.html">挪威-英格兰赛前资料</a>；<a href="https://sports.betmgm.com/en/blog/world-cup/argentina-vs-switzerland-prediction-odds-preview-world-cup-july-11-bm16/">阿根廷-瑞士赔率预览</a>。</p></div></section>
"""
    match_html += web_refresh
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>20260709 四强席位预测</title><style>{css()}</style></head>
<body><header><h1>20260709 四分之一决赛预测</h1><nav><a href="../index.html">首页</a><a href="../parlay/">串关</a><a href="../knockout/">淘汰赛日历</a></nav></header><main>
<section class="section"><h2>昨日复盘与模型修正</h2><div class="card"><p><strong>{esc(review['headline'])}</strong></p><p>{esc(review['summary'])}</p><ul>{lesson_items}</ul></div></section>
<section class="section" id="parlay"><h2>二串一 / 三串一</h2><div class="card"><p><strong>四强席位串关：方向+总进球优先，比分池补齐3-2和0-0</strong></p><p>97/98使用Sporttery竞彩赔率；99/100当前竞彩暂缺，先用Sky Bet胜平负和Polymarket概率做外部参考。外部赔率只校准方向，比分、总进球和半全场等竞彩细项等开盘后再替换。</p><p class="muted">赔率来源：Sporttery live files for 97/98；Sky Bet/Polymarket external reference for 99/100</p></div>{parlay_html}</section>
<section class="section"><h2>今日/未来比赛预测</h2>{match_html}</section>
<footer class="section muted">以上仅为公开信息整理后的娱乐分析，不构成任何购彩建议，请理性参考。</footer>
</main></body></html>"""


def render_parlay_page(parlay: list[dict[str, Any]]) -> str:
    groups = "".join(render_parlay_group(group) for group in parlay)
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>未来串关</title><style>{css()}</style></head>
<body><header><h1>未来串关</h1><nav><a href="../index.html">首页</a><a href="../20260709/">07-09预测</a><a href="../knockout/">淘汰赛日历</a></nav></header><main>
<section class="section"><h2>二串一 / 三串一</h2><div class="card"><p><strong>四强席位串关：方向+总进球优先，比分池补齐3-2和0-0</strong></p><p>二串一、三串一稳健、防冷三组全部保留半全场和EV信号。97/98用竞彩，99/100用外部胜平负参考，竞彩开盘后再替换细项。</p><p class="muted">赔率来源：Sporttery live files for 97/98；Sky Bet/Polymarket external reference for 99/100</p></div>{groups}</section>
<footer class="section muted">以上仅为公开信息整理后的娱乐分析，不构成任何购彩建议，请理性参考。</footer>
</main></body></html>"""


def update_home() -> None:
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace("最新更新时间：2026-07-09 复盘后更新", "最新更新时间：2026-07-09 重建后更新")
    text = text.replace("当前主推页面：2026年7月9日", "当前主推页面：2026年7月9日")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    matches = build_matches()
    for item in matches:
        if item.get("match_no") == "98":
            item["score_rows"][0] = ("2-0", "18.0%", "+0.04", "西班牙零封主线")
    overrides = {
        "98": {
            "main_score": "2-0",
            "direction": "西班牙90分钟胜优先，防平",
            "goals": "2-3球，防4球",
            "half": "西班牙 1-0 比利时",
            "hafu": "胜胜 / 平胜",
            "probability": "90分钟：西班牙 58% / 平 25% / 比利时 17%；最终晋级：西班牙 68% / 比利时 32%",
            "rationale": "法国2-0复盘后，本场不再把强队优势机械压成2-1。公开资料显示西班牙连续零封，且比利时中场存在伤情与结构性缺口；比利时上一场4-1美国的强势包含对手防守失误，不能直接外推成持续对攻。主线调整为西班牙控场后的2-0，1-0/2-1为节奏放慢或客队破门分支，3-1/3-2保留给早球和追分状态。",
            "review": "法国2-0验证了强队方向明确、对手进攻受限、低位总进球共同成立时的零封小胜触发器。本场据此上调2-0/1-0，但比利时具备转换能力，不能删除2-1和3-2尾部。",
            "score_rows": [("2-0", "18.0%", "+0.04", "西班牙零封主线"), ("1-0", "15.0%", "+0.03", "低节奏小胜"), ("2-1", "13.0%", "+0.02", "比利时定位球破门"), ("1-1", "11.0%", "防冷", "比利时拖窄"), ("3-1", "10.0%", "尾部", "西班牙早球后扩大"), ("3-2", "7.0%", "尾部", "追分开放" )],
            "triggers": ["西班牙30分钟前进球：2-0/3-1升权，1-1降权。", "半场0-0：1-0/1-1升权，2球总进球优先。", "比利时先入球：2-1/2-2/3-2升权，比赛转入开放尾部。"]
        },
        "99": {
            "main_score": "1-2",
            "direction": "英格兰不败，防90分钟平",
            "goals": "3-4球，防2球",
            "half": "挪威 1-1 英格兰",
            "hafu": "平负 / 负负",
            "probability": "90分钟：挪威 24% / 平 27% / 英格兰 49%；最终晋级：挪威 40% / 英格兰 60%",
            "rationale": "法国2-0不是全局小球信号。公开预览显示英格兰有防线人员与停赛风险，挪威直接进攻和哈兰德的终结能力使比赛具备真实开放路径；同时英格兰阵容深度和淘汰赛管理仍支持不败主线。主线回到1-2，0-1只作低比分兑现分支，2-2/2-3用于挪威先入球或英格兰后程追分。",
            "review": "本场把法国2-0复盘转化为条件规则：只有对手进攻受限才强化零封；挪威具备高质量进攻时，不能把0-1当唯一主线，必须保留2-2/2-3开放尾部。",
            "score_rows": [("1-2", "17.0%", "+0.03", "英格兰主线小胜"), ("1-1", "14.0%", "+0.03", "90分钟平局保护"), ("2-2", "12.0%", "防冷", "挪威高点与转换"), ("0-1", "10.0%", "+0.02", "英格兰低比分兑现"), ("2-3", "8.0%", "尾部", "落后方追分提速"), ("3-2", "6.0%", "尾部", "挪威先入球" )],
            "triggers": ["英格兰先入球：0-1/1-2升权，2-3保留。", "挪威先入球：1-1/2-2/2-3升权，不再只升1-2。", "半场0-0：1-1/0-1升权；半场1-1则总进球4球路径上修。"]
        },
        "100": {
            "main_score": "1-0",
            "direction": "阿根廷胜优先，强防平",
            "goals": "1-2球，防3球",
            "half": "阿根廷 0-0 瑞士",
            "hafu": "平胜 / 平平",
            "probability": "90分钟：阿根廷 56% / 平 29% / 瑞士 15%；最终晋级：阿根廷 68% / 瑞士 32%",
            "rationale": "法国2-0验证的零封小胜触发器在本场部分成立：阿根廷实力和市场方向明显占优，但瑞士低位锁局、点球路径和阿根廷防守波动都不能忽略。公开预览仍把阿根廷列为优势方，因此主线为1-0，2-0是阿根廷早球后控场扩大，1-1/0-0保留为锁局保护。",
            "review": "不把法国2-0直接复制成阿根廷大胜；本场只上调阿根廷零封小胜分支，同时保留瑞士把比赛拖入低比分或加时点球的路径。",
            "score_rows": [("1-0", "18.0%", "+0.04", "阿根廷小胜正路"), ("2-0", "16.0%", "+0.03", "阿根廷零封扩大"), ("1-1", "14.0%", "防冷", "瑞士拖窄"), ("0-0", "10.0%", "保护", "锁局点球路径"), ("2-1", "9.0%", "延展", "瑞士破门"), ("1-2", "5.0%", "极冷", "瑞士反击" )],
            "triggers": ["阿根廷30分钟前进球：2-0/2-1升权，1-0仍保留。", "半场0-0：0-0/1-0/1-1升权，平胜与平平优先。", "瑞士先入球：1-1/2-1升权，阿根廷90分钟胜率下调。"]
        }
    }
    for item in matches:
        if item.get("match_no") in overrides:
            item.update(overrides[item["match_no"]])
    review = build_review()
    review = {
        "headline": "07-10复盘：法国2-0摩洛哥，主方向、2球总进球和主比分全部命中",
        "summary": "法国2-0摩洛哥验证了强队面对韧性型淘汰赛对手时的零封小胜路径：法国的实力、控场和对手进攻受限共同兑现2-0。平局保护仍保留为场景分支，但不能稀释已经得到赔率与实力共同支持的主线；同时不把一次2-0机械外推成后续比赛全部小球。",
        "lessons": [
            "强队方向明确、对手进攻受限、总进球2球低位时，2-0和1-0进入核心比分池。",
            "平局保护继续保留，但只作为拖窄或锁局分支；不能因淘汰赛韧性把主线改成单纯防平。",
            "强队早球或弱侧必须追分时，仍审计3-1、3-2等开放尾部，避免从一次2-0推导全局小球。",
            "后续场次已据此调整：099新增0-1低比分兑现路径，100强化1-0/2-0零封小胜，098继续保留3-2/1-3开放尾部。"
        ]
    }
    parlay = build_parlay(matches)
    by_no = {str(item.get("match_no")): item for item in matches}
    for group in parlay:
        leg_numbers = {str(item.get("match_no")) for item in group.get("legs", [])}
        if "98" in leg_numbers and "99" in leg_numbers and "100" not in leg_numbers:
            item = by_no["100"]
            group["legs"].append({
                "match_no": "100",
                "match": f"{item['home']} vs {item['away']}",
                "direction": item["direction"],
                "score": "1-0 / 2-0",
                "goals": "1 / 2球",
                "hafu": item["hafu"],
                "ev": "外部赔率支持",
                "note": "阿根廷方向优先，瑞士锁局与点球路径保留。"
            })
    day_dir = ROOT / DATE
    day_dir.mkdir(exist_ok=True)
    page = render_page(matches, review, parlay)
    (day_dir / "index.html").write_text(page, encoding="utf-8")
    (day_dir / f"predict_{DATE}.html").write_text(page, encoding="utf-8")
    (ROOT / "parlay" / "index.html").write_text(render_parlay_page(parlay), encoding="utf-8")
    for date in ("20260710", "20260711", "20260712"):
        target = ROOT / date
        target.mkdir(exist_ok=True)
        shutil.copyfile(day_dir / "index.html", target / "index.html")
        shutil.copyfile(day_dir / "index.html", target / f"predict_{date}.html")
    write_json(DATA_DIR / "model_review_lessons_20260708.json", review)
    write_json(DATA_DIR / "knockout_predictions_20260709.json", {"date": DATE, "stage": "quarterfinals", "matches": matches})
    write_json(DATA_DIR / "quarterfinal_parlay_20260709.json", {"date": DATE, "stage": "quarterfinal_parlay", "groups": parlay})
    update_home()
    print("Rebuilt 20260709 pages from the 0864186-style layout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
