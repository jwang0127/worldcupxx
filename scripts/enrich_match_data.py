#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import re
import ssl
import sys
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


ROOT = Path(__file__).resolve().parent.parent
ALIASES_FILE = ROOT / "team_aliases.json"
DEFAULT_TIMEOUT = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrich daily match data with external sources.")
    parser.add_argument("--date", required=True, help="Date in yyyyMMdd format")
    parser.add_argument("--data-file", required=True, help="Path to data json file")
    return parser.parse_args()


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def http_json(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = DEFAULT_TIMEOUT) -> Any:
    req = urllib.request.Request(url, headers=headers or {})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        text = resp.read().decode(charset, errors="replace")
        return json.loads(text)


def to_int(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).strip()))
    except Exception:
        return None


def normalize_group_name(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""
    upper = raw.upper()
    if upper.startswith("GROUP "):
        upper = upper.replace("GROUP ", "", 1).strip()
    if len(upper) == 1 and upper.isalpha():
        return upper + "\u7ec4"
    if raw.endswith("\u7ec4"):
        return raw
    return raw


def load_alias_maps() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    rows = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
    by_name: dict[str, dict[str, Any]] = {}
    by_code: dict[str, dict[str, Any]] = {}
    for row in rows:
        code = str(row.get("code", "")).upper()
        if code:
            by_code[code] = row
        names = [row.get("zh", ""), row.get("en", "")]
        names.extend(row.get("aliases", []) or [])
        for name in names:
            key = str(name or "").strip().lower()
            if key:
                by_name[key] = row
    return by_name, by_code


ALIAS_BY_NAME, ALIAS_BY_CODE = load_alias_maps()


def lookup_team(team_name: str = "", team_code: str = "") -> Optional[dict[str, Any]]:
    code = (team_code or "").strip().upper()
    if code and code in ALIAS_BY_CODE:
        return ALIAS_BY_CODE[code]
    key = (team_name or "").strip().lower()
    if key and key in ALIAS_BY_NAME:
        return ALIAS_BY_NAME[key]
    return None


def source_status() -> List[Dict[str, Any]]:
    return [
        {
            "name": "worldcup26-ir",
            "enabled": True,
            "baseUrl": "https://worldcup26.ir/get/games",
            "role": "world-cup-schedule-score-mirror",
        },
        {
            "name": "football-data",
            "enabled": bool(os.environ.get("FOOTBALL_DATA_TOKEN")),
            "baseUrl": "https://api.football-data.org/v4/matches",
            "role": "official-match-and-standings-backup",
        },
        {
            "name": "api-sports-football",
            "enabled": bool(os.environ.get("API_FOOTBALL_KEY")),
            "baseUrl": "https://v3.football.api-sports.io/",
            "role": "injuries-h2h-odds-trend-primary",
        },
        {
            "name": "thesportsdb",
            "enabled": True,
            "baseUrl": "https://www.thesportsdb.com/api/v1/json/123/",
            "role": "team-metadata-fallback",
        },
        {
            "name": "serpapi-google",
            "enabled": bool(os.environ.get("SERPAPI_KEY")),
            "baseUrl": "https://serpapi.com/search?engine=google",
            "role": "fifa-ranking-news-fallback",
        },
    ]


def ensure_external_shell(match: dict[str, Any]) -> dict[str, Any]:
    external = match.get("external")
    if not isinstance(external, dict):
        external = {}
        match["external"] = external
    external.setdefault("updatedAt", now_text())
    external.setdefault("sources", [])
    return external


def attach_aliases(match: dict[str, Any]) -> None:
    home_alias = lookup_team(match.get("home", ""), match.get("homeCode", ""))
    away_alias = lookup_team(match.get("away", ""), match.get("awayCode", ""))
    if home_alias:
        match["homeEn"] = home_alias["en"]
        match["homeAlias"] = home_alias
    if away_alias:
        match["awayEn"] = away_alias["en"]
        match["awayAlias"] = away_alias


def thesportsdb_team(english_name: str, cache: dict[str, Any]) -> dict[str, Any]:
    if not english_name:
        return {"status": "missing-team-name", "source": "thesportsdb"}
    if english_name in cache:
        return cache[english_name]

    query = urllib.parse.quote(english_name)
    url = f"https://www.thesportsdb.com/api/v1/json/123/searchteams.php?t={query}"
    try:
        data = http_json(url)
        teams = data.get("teams") or []
        if not teams:
            result = {"status": "not-found", "source": "thesportsdb", "query": english_name}
        else:
            team = teams[0]
            result = {
                "status": "ok",
                "source": "thesportsdb",
                "name": team.get("strTeam"),
                "country": team.get("strCountry"),
                "formedYear": team.get("intFormedYear"),
                "league": team.get("strLeague"),
                "stadium": team.get("strStadium"),
                "description": (team.get("strDescriptionCN") or team.get("strDescriptionEN") or "")[:240],
            }
    except Exception as exc:
        result = {"status": "unavailable", "source": "thesportsdb", "error": str(exc)}

    cache[english_name] = result
    return result


def api_sports_get(path: str, params: Dict[str, Any], api_key: str) -> Any:
    query = urllib.parse.urlencode({k: v for k, v in params.items() if v not in (None, "")})
    url = f"https://v3.football.api-sports.io/{path}"
    if query:
        url += f"?{query}"
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "v3.football.api-sports.io",
    }
    return http_json(url, headers=headers)


def api_sports_team_id(english_name: str, api_key: str, cache: dict[str, Any]) -> Optional[int]:
    if english_name in cache:
        return cache[english_name]
    try:
        data = api_sports_get("teams", {"search": english_name}, api_key)
        rows = data.get("response") or []
        team_id = None
        if rows:
            national_rows = [r for r in rows if (r.get("team") or {}).get("national") is True]
            preferred = national_rows[0] if national_rows else rows[0]
            team_id = (preferred.get("team") or {}).get("id")
        cache[english_name] = team_id
        return team_id
    except Exception:
        cache[english_name] = None
        return None


def api_sports_h2h(home_name: str, away_name: str, api_key: str, cache: dict[str, Any]) -> dict[str, Any]:
    home_id = api_sports_team_id(home_name, api_key, cache)
    away_id = api_sports_team_id(away_name, api_key, cache)
    if not home_id or not away_id:
        return {"status": "pending-team-id", "source": "api-sports", "matches": []}
    try:
        data = api_sports_get("fixtures/headtohead", {"h2h": f"{home_id}-{away_id}", "last": 5}, api_key)
        items = []
        for row in data.get("response") or []:
            fixture = row.get("fixture") or {}
            teams = row.get("teams") or {}
            goals = row.get("goals") or {}
            items.append({
                "date": fixture.get("date"),
                "home": ((teams.get("home") or {}).get("name")),
                "away": ((teams.get("away") or {}).get("name")),
                "score": f"{goals.get('home', '-')}" + ":" + f"{goals.get('away', '-')}",
            })
        return {"status": "ok", "source": "api-sports", "matches": items}
    except Exception as exc:
        return {"status": "unavailable", "source": "api-sports", "error": str(exc), "matches": []}


def api_sports_injuries(english_name: str, api_key: str, season: int, cache: dict[str, Any]) -> dict[str, Any]:
    team_id = api_sports_team_id(english_name, api_key, cache)
    if not team_id:
        return {"status": "pending-team-id", "source": "api-sports", "items": []}
    try:
        data = api_sports_get("injuries", {"team": team_id, "season": season}, api_key)
        items = []
        for row in (data.get("response") or [])[:5]:
            player = row.get("player") or {}
            fixture = row.get("fixture") or {}
            items.append({
                "player": player.get("name"),
                "type": row.get("type"),
                "reason": row.get("reason"),
                "fixture": fixture.get("date"),
            })
        return {"status": "ok", "source": "api-sports", "items": items}
    except Exception as exc:
        return {"status": "unavailable", "source": "api-sports", "error": str(exc), "items": []}


def football_data_matches(token: str) -> list[dict[str, Any]]:
    data = http_json("https://api.football-data.org/v4/matches", headers={"X-Auth-Token": token})
    return data.get("matches") or []


def serpapi_fifa_rank(english_name: str, api_key: str, cache: dict[str, Any]) -> dict[str, Any]:
    if not english_name:
        return {"status": "missing-team-name"}
    if english_name in cache:
        return cache[english_name]
    try:
        q = urllib.parse.quote(f"FIFA men ranking {english_name}")
        url = f"https://serpapi.com/search.json?engine=google&q={q}&api_key={api_key}"
        data = http_json(url)
        text_pool: list[str] = []
        ai_overview = data.get("ai_overview") or {}
        for block in ai_overview.get("text_blocks") or []:
            snippet = block.get("snippet")
            if snippet:
                text_pool.append(str(snippet))
        for item in data.get("organic_results") or []:
            for key in ("snippet", "title"):
                value = item.get(key)
                if value:
                    text_pool.append(str(value))
        for item in data.get("related_questions") or []:
            snippet = item.get("snippet")
            if snippet:
                text_pool.append(str(snippet))
        combined = " | ".join(text_pool)
        rank = None
        points = None
        match = re.search(r"\b(\d{1,3})(?:st|nd|rd|th)\b", combined, flags=re.I)
        if match:
            rank = int(match.group(1))
        points_match = re.search(r"(\d{4}\.\d{1,2})", combined)
        if points_match:
            points = float(points_match.group(1))
        result = {
            "status": "ok" if rank else "unparsed",
            "source": "serpapi",
            "rank": rank,
            "points": points,
            "query": english_name,
        }
    except Exception as exc:
        result = {"status": "unavailable", "source": "serpapi", "error": str(exc)}
    cache[english_name] = result
    return result


def walk_dicts(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from walk_dicts(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from walk_dicts(item)


def first_value(row: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in row and row[key] not in (None, ""):
            return row[key]
    return None


def worldcup26_matches() -> list[dict[str, Any]]:
    data = http_json("https://worldcup26.ir/get/games")
    rows = []
    for row in walk_dicts(data):
        home = first_value(row, ["home_team_name_en", "home_team_en", "homeTeamEn", "home_team", "homeTeam", "home", "team1"])
        away = first_value(row, ["away_team_name_en", "away_team_en", "awayTeamEn", "away_team", "awayTeam", "away", "team2"])
        if not home or not away:
            continue
        group = first_value(row, ["group", "group_name", "groupName", "stage_group"])
        stage = first_value(row, ["stage", "stage_name", "stageName"])
        hg = first_value(row, ["home_score", "homeScore", "score1", "home_goals"])
        ag = first_value(row, ["away_score", "awayScore", "score2", "away_goals"])
        rows.append({
            "home_en": str(home).strip(),
            "away_en": str(away).strip(),
            "group": normalize_group_name(str(group or "")),
            "stage": str(stage or ""),
            "home_goals": to_int(hg),
            "away_goals": to_int(ag),
            "status": str(first_value(row, ["status", "state", "match_status"]) or ""),
            "date": str(first_value(row, ["date", "match_date", "kickoff"]) or ""),
        })
    return rows


def build_snapshot(payload: dict[str, Any], external_matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups_of_interest = {
        normalize_group_name(str(m.get("group", "")))
        for m in payload.get("matches", [])
        if m.get("group")
    }
    tables: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)

    for match in payload.get("matches", []):
        group = normalize_group_name(str(match.get("group", "")))
        if not group:
            continue
        for side in ("home", "away"):
            team_name = str(match.get(side, "")).strip()
            if team_name and team_name not in tables[group]:
                tables[group][team_name] = {
                    "team": team_name,
                    "played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "gf": 0,
                    "ga": 0,
                    "gd": 0,
                    "points": 0,
                }

    for row in external_matches:
        group = normalize_group_name(row.get("group", ""))
        if not group or group not in groups_of_interest:
            continue
        hg = row.get("home_goals")
        ag = row.get("away_goals")
        if hg is None or ag is None:
            continue
        home_alias = lookup_team(row.get("home_en", ""))
        away_alias = lookup_team(row.get("away_en", ""))
        home = (home_alias or {}).get("zh") or row.get("home_en")
        away = (away_alias or {}).get("zh") or row.get("away_en")
        for team in (home, away):
            if team not in tables[group]:
                tables[group][team] = {
                    "team": team,
                    "played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "gf": 0,
                    "ga": 0,
                    "gd": 0,
                    "points": 0,
                }
        hrow = tables[group][home]
        arow = tables[group][away]
        hrow["played"] += 1
        arow["played"] += 1
        hrow["gf"] += hg
        hrow["ga"] += ag
        arow["gf"] += ag
        arow["ga"] += hg
        if hg > ag:
            hrow["wins"] += 1
            arow["losses"] += 1
            hrow["points"] += 3
        elif ag > hg:
            arow["wins"] += 1
            hrow["losses"] += 1
            arow["points"] += 3
        else:
            hrow["draws"] += 1
            arow["draws"] += 1
            hrow["points"] += 1
            arow["points"] += 1

    snapshot = []
    for group in sorted(tables.keys()):
        rows = list(tables[group].values())
        for row in rows:
            row["gd"] = row["gf"] - row["ga"]
        rows.sort(key=lambda x: (-x["points"], -x["gd"], -x["gf"], x["team"]))
        snapshot.append({"group": group, "rows": rows})
    return snapshot


def attach_model_inputs(match: dict[str, Any]) -> None:
    external = ensure_external_shell(match)
    external.setdefault("teamMeta", {})
    external.setdefault("fifaRanking", {"status": "pending-serpapi-or-manual", "home": None, "away": None})
    external.setdefault("oddsMovement", {"status": "pending-live-odds-source"})
    external.setdefault("injuries", {"status": "pending-api-sports", "home": [], "away": []})
    external.setdefault("h2h", {"status": "pending-api-sports", "matches": []})


def main() -> int:
    args = parse_args()
    data_file = Path(args.data_file)
    payload = json.loads(data_file.read_text(encoding="utf-8-sig"))
    payload["externalEnrichment"] = {
        "updatedAt": now_text(),
        "date": args.date,
        "sources": source_status(),
    }

    for match in payload.get("matches", []):
        attach_aliases(match)
        attach_model_inputs(match)

    team_meta_cache: dict[str, Any] = {}
    api_team_cache: dict[str, Any] = {}
    serpapi_cache: dict[str, Any] = {}
    api_key = os.environ.get("API_FOOTBALL_KEY", "").strip()
    serpapi_key = os.environ.get("SERPAPI_KEY", "").strip()
    season = int(args.date[:4]) if args.date[:4].isdigit() else datetime.now().year

    for match in payload.get("matches", []):
        external = ensure_external_shell(match)
        home_en = match.get("homeEn", "")
        away_en = match.get("awayEn", "")
        external["teamMeta"] = {
            "home": thesportsdb_team(home_en, team_meta_cache),
            "away": thesportsdb_team(away_en, team_meta_cache),
        }
        if serpapi_key:
            external["fifaRanking"] = {
                "status": "ok",
                "source": "serpapi",
                "home": serpapi_fifa_rank(home_en, serpapi_key, serpapi_cache),
                "away": serpapi_fifa_rank(away_en, serpapi_key, serpapi_cache),
            }
        if api_key:
            external["h2h"] = api_sports_h2h(home_en, away_en, api_key, api_team_cache)
            home_inj = api_sports_injuries(home_en, api_key, season, api_team_cache)
            away_inj = api_sports_injuries(away_en, api_key, season, api_team_cache)
            external["injuries"] = {
                "status": "ok",
                "source": "api-sports",
                "home": home_inj.get("items", []),
                "away": away_inj.get("items", []),
            }

    external_matches: list[dict[str, Any]] = []
    snapshot_source = ""
    try:
        external_matches = worldcup26_matches()
        snapshot_source = "worldcup26-ir"
    except Exception:
        token = os.environ.get("FOOTBALL_DATA_TOKEN", "").strip()
        if token:
            try:
                rows = football_data_matches(token)
                for row in rows:
                    comp = row.get("competition") or {}
                    if "world" not in json.dumps(comp, ensure_ascii=False).lower():
                        continue
                    stage = str(row.get("stage") or "")
                    group = normalize_group_name(stage.replace("GROUP_", "").replace("_", " "))
                    external_matches.append({
                        "home_en": ((row.get("homeTeam") or {}).get("name") or ""),
                        "away_en": ((row.get("awayTeam") or {}).get("name") or ""),
                        "group": group,
                        "home_goals": to_int(((row.get("score") or {}).get("fullTime") or {}).get("home")),
                        "away_goals": to_int(((row.get("score") or {}).get("fullTime") or {}).get("away")),
                        "status": (row.get("status") or ""),
                        "date": (row.get("utcDate") or ""),
                    })
                snapshot_source = "football-data"
            except Exception:
                pass

    if external_matches:
        payload["standingsSnapshot"] = build_snapshot(payload, external_matches)
        payload["externalEnrichment"]["standingsSource"] = snapshot_source
    else:
        payload.setdefault("standingsSnapshot", [])
        payload["externalEnrichment"]["standingsSource"] = "local-only"

    data_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "date": args.date,
        "updatedAt": payload["externalEnrichment"]["updatedAt"],
        "standingsSource": payload["externalEnrichment"].get("standingsSource"),
        "matches": len(payload.get("matches", [])),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
