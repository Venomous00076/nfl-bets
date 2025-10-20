"""
Pull PBP from NFLsavant.
We auto-discover season CSV links from the About page and ingest the last two seasons for MVP.
"""
import io, re, requests, pandas as pd
from sqlalchemy import text
from ..db import ENGINE

ABOUT_URL = "https://nflsavant.com/about.php"

def discover_csv_links() -> list[str]:
    r = requests.get(ABOUT_URL, timeout=30)
    r.raise_for_status()
    return sorted(set(re.findall(r'https://[^"]+pbp_data/\d{4}regular\.csv', r.text)))

def load_csv(url: str) -> pd.DataFrame:
    r = requests.get(url, timeout=90); r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    keep = ["season","game_id","play_id","posteam","defteam","qtr","down","ydstogo",
            "yardline_100","play_type","yards_gained","epa","success",
            "total_home_score","total_away_score","date"]
    keep = [c for c in keep if c in df.columns]
    df = df[keep].copy()
    df.rename(columns={"total_home_score":"score_home",
                       "total_away_score":"score_away",
                       "date":"game_date"}, inplace=True)
    df["success"] = df["success"].fillna(False).astype(bool)
    return df

def upsert_pbp(df: pd.DataFrame):
    df.to_sql("raw_pbp", ENGINE, if_exists="append", index=False, method="multi", chunksize=5000)

def run_nflsavant_ingest():
    links = discover_csv_links()
    for url in links[-2:]:  # last two seasons
        print("Downloading:", url)
        df = load_csv(url)
        upsert_pbp(df)
    with ENGINE.begin() as conn:
        conn.execute(text("ANALYZE raw_pbp"))

if __name__ == "__main__":
    run_nflsavant_ingest()
