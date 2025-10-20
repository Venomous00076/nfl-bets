"""
Pull ESPN injuries (unofficial endpoints; safe to skip if they change).
"""
import requests, datetime as dt, pandas as pd
from ..db import ENGINE

# ESPN slugs for all 32 teams
TEAMS = [
    "ari","atl","bal","buf","car","chi","cin","cle","dal","den","det","gb",
    "hou","ind","jax","kc","lv","lac","lar","mia","min","ne","no","nyg",
    "nyj","phi","pit","sea","sf","tb","ten","wsh"
]
BASE = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{team}/injuries"

def fetch_team(team):
    r = requests.get(BASE.format(team=team), timeout=25)
    r.raise_for_status()
    j = r.json()
    rows=[]; snap=dt.datetime.utcnow()
    for cat in j.get("injuries", []):
        for item in cat.get("injuries", []):
            rows.append(dict(
                snapshot_ts=snap,
                team=team.upper(),
                player_id=item.get("athlete",{}).get("id"),
                status=item.get("status",""),
                position=item.get("position",""),
                is_out=("Out" in item.get("status",""))
            ))
    return rows

def run_espn_injuries():
    allr=[]
    for t in TEAMS:
        try:
            allr += fetch_team(t)
        except Exception:
            continue
    if allr:
        pd.DataFrame(allr).to_sql("injuries", ENGINE, if_exists="append", index=False, method="multi")

if __name__ == "__main__":
    run_espn_injuries()
