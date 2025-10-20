"""
Fetch odds from The Odds API (v4), filter to DraftKings, and save to odds_raw.
"""
import requests, pandas as pd, datetime as dt
from ..config import settings
from ..db import ENGINE

BASE = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"

def fetch_now():
    params = dict(
        apiKey=settings.ODDS_API_KEY,
        regions=settings.REGIONS,
        markets=settings.MARKETS,
        oddsFormat="american",
        dateFormat="iso",
    )
    r = requests.get(BASE, params=params, timeout=45)
    r.raise_for_status()
    return r.json()

def normalize(payload) -> pd.DataFrame:
    rows = []
    snap = dt.datetime.utcnow().isoformat() + "Z"
    for ev in payload:
        eid = ev["id"]
        home = ev.get("home_team")
        away = ev.get("away_team")
        commence = ev.get("commence_time")
        for bk in ev.get("bookmakers", []):
            if bk.get("title") != "DraftKings":
                continue
            for mk in bk.get("markets", []):
                mkt = mk["key"]  # h2h/spreads/totals
                ts  = mk.get("last_update")
                for out in mk.get("outcomes", []):
                    rows.append({
                        "snapshot_ts": snap,
                        "event_id": eid,
                        "book": "DraftKings",
                        "market": mkt,
                        "outcome": out.get("name"),
                        "price_american": out.get("price"),
                        "point": out.get("point"),
                        "line_ts": ts,
                        "home_team": home,
                        "away_team": away,
                        "commence_time": commence
                    })
    return pd.DataFrame(rows)

def save(df: pd.DataFrame):
    if not len(df): return
    df.to_sql("odds_raw", ENGINE, if_exists="append", index=False, method="multi")

def run_odds_ingest():
    data = fetch_now()
    df = normalize(data)
    save(df)

if __name__ == "__main__":
    run_odds_ingest()
