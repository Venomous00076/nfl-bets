from pydantic import BaseModel
import os

class Settings(BaseModel):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    ODDS_API_KEY: str = os.getenv("ODDS_API_KEY")
    REGIONS: str = os.getenv("REGIONS", "us,us2")
    MARKETS: str = os.getenv("MARKETS", "h2h,spreads,totals")
    RECENT_GAMES: int = int(os.getenv("RECENT_GAMES", "4"))

settings = Settings()
