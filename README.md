Put below in a .env file changing what you want to change.

# Postgres (leave as-is unless you changed compose)
DATABASE_URL=postgresql+psycopg2://nfl:nfl@db:5432/nfl

# The Odds API (your key)
ODDS_API_KEY=GETAPIKEY

# Odds fetch settings (DraftKings lives in US regions)
REGIONS=us,us2
MARKETS=h2h,spreads,totals

# Recent-form emphasis (last few games window)
RECENT_GAMES=Change to amount of games in the past you want

END .env file

To start do -
# 1)
sudo docker-compose build
# 2)
sudo docker-compose up -d
# 3)
sudo docker-compose exec db psql -U nfl -d nfl -c "SELECT now();"
# 4)
sudo docker-compose exec app python -m app.etl.odds_draftkings
# 5) DraftKings odds (fills odds_raw)
sudo docker-compose exec app python -m app.etl.odds_draftkings

# 6) (first-time only) seed team_features if empty
sudo docker-compose exec db psql -U nfl -d nfl -t -A -c "SELECT COUNT(*) FROM team_features;"
# If it prints 0, run:
sudo docker-compose exec -T app python - <<'PY'
import datetime as dt, json, pandas as pd
from sqlalchemy import text
import sys
sys.path.append("/srv/app")
from app.db import ENGINE
from app.util_team_names import ALL_TEAM_CODES

season = dt.datetime.utcnow().year
rows=[]
for code in sorted(ALL_TEAM_CODES):
    feat = dict(epa=0.0, sr=0.5, rush_rate=0.45, pass_rate=0.55)
    rows.append(dict(season=season, team=code, feat=json.dumps(feat), asof_game=f"BOOTSTRAP-{season}"))
pd.DataFrame(rows).to_sql("team_features", ENGINE, if_exists="append", index=False, method="multi")
print("seeded:", len(rows))
PY

# 7) end-to-end pipeline (features -> projections -> recommendations)
sudo docker-compose exec app python -m app.pipeline

# Set your week window in local (America/Chicago) dates
export START=2025-10-20   # Monday

export END=2025-10-26     # Sunday

Once everything is set up doing above, run this command to see predictions
# FINAL COMMAND TO SEE ODDS
sudo docker-compose exec -T db psql -U nfl -d nfl -t -A -c "
WITH name_map(team_full, code) AS (
  VALUES
  ('Arizona Cardinals','ARI'), ('Atlanta Falcons','ATL'), ('Baltimore Ravens','BAL'), ('Buffalo Bills','BUF'),
  ('Carolina Panthers','CAR'), ('Chicago Bears','CHI'), ('Cincinnati Bengals','CIN'), ('Cleveland Browns','CLE'),
  ('Dallas Cowboys','DAL'), ('Denver Broncos','DEN'), ('Detroit Lions','DET'), ('Green Bay Packers','GB'),
  ('Houston Texans','HOU'), ('Indianapolis Colts','IND'), ('Jacksonville Jaguars','JAX'), ('Kansas City Chiefs','KC'),
  ('Las Vegas Raiders','LV'), ('Los Angeles Chargers','LAC'), ('Los Angeles Rams','LAR'), ('Miami Dolphins','MIA'),
  ('Minnesota Vikings','MIN'), ('New England Patriots','NE'), ('New Orleans Saints','NO'), ('New York Giants','NYG'),
  ('New York Jets','NYJ'), ('Philadelphia Eagles','PHI'), ('Pittsburgh Steelers','PIT'), ('San Francisco 49ers','SF'),
  ('Seattle Seahawks','SEA'), ('Tampa Bay Buccaneers','TB'), ('Tennessee Titans','TEN'), ('Washington Commanders','WAS')
),
latest_recs AS (SELECT MAX(snapshot_ts) AS snap FROM recommendations),
games AS (
  SELECT DISTINCT
         mh.code AS home_code,
         ma.code AS away_code,
         o.commence_time
  FROM odds_raw o
  JOIN name_map mh ON mh.team_full = o.home_team
  JOIN name_map ma ON ma.team_full = o.away_team
  WHERE (o.commence_time AT TIME ZONE 'America/Chicago')::date
        BETWEEN '${START}' AND '${END}'
)
SELECT COALESCE(
  json_agg(x.r ORDER BY (x.r->>'edge')::numeric DESC NULLS LAST),
  '[]'::json
)
FROM (
  SELECT json_build_object(
           'kickoff',    g.commence_time,      -- from odds_raw
           'market',     r.market,
           'home',       r.home_team,
           'away',       r.away_team,
           'book',       r.best_book,
           'pick',       r.selection,
           'point',      r.line_point,
           'price',      r.best_price,
           'edge',       r.edge,
           'kelly',      r.kelly_frac,
           'confidence', r.confidence
         ) AS r
  FROM recommendations r
  JOIN latest_recs lr ON r.snapshot_ts = lr.snap
  JOIN games g ON g.home_code = r.home_team AND g.away_code = r.away_team
  WHERE r.market IN ('h2h','spreads','totals')
) x;
" | jq '.'
