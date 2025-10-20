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
