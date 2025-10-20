import re

# Canonical team codes (aligned to common PBP posteam codes)
TEAM_CODE_TO_NAME = {
    "ARI": "Arizona Cardinals",
    "ATL": "Atlanta Falcons",
    "BAL": "Baltimore Ravens",
    "BUF": "Buffalo Bills",
    "CAR": "Carolina Panthers",
    "CHI": "Chicago Bears",
    "CIN": "Cincinnati Bengals",
    "CLE": "Cleveland Browns",
    "DAL": "Dallas Cowboys",
    "DEN": "Denver Broncos",
    "DET": "Detroit Lions",
    "GB":  "Green Bay Packers",
    "HOU": "Houston Texans",
    "IND": "Indianapolis Colts",
    "JAX": "Jacksonville Jaguars",
    "KC":  "Kansas City Chiefs",
    "LV":  "Las Vegas Raiders",
    "LAC": "Los Angeles Chargers",
    "LAR": "Los Angeles Rams",
    "MIA": "Miami Dolphins",
    "MIN": "Minnesota Vikings",
    "NE":  "New England Patriots",
    "NO":  "New Orleans Saints",
    "NYG": "New York Giants",
    "NYJ": "New York Jets",
    "PHI": "Philadelphia Eagles",
    "PIT": "Pittsburgh Steelers",
    "SEA": "Seattle Seahawks",
    "SF":  "San Francisco 49ers",
    "TB":  "Tampa Bay Buccaneers",
    "TEN": "Tennessee Titans",
    "WAS": "Washington Commanders",
}

# Main mapping from full names (e.g., DraftKings strings) -> codes
NAME_TO_TEAM_CODE = {
    "Arizona Cardinals": "ARI",
    "Atlanta Falcons": "ATL",
    "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF",
    "Carolina Panthers": "CAR",
    "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN",
    "Cleveland Browns": "CLE",
    "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN",
    "Detroit Lions": "DET",
    "Green Bay Packers": "GB",
    "Houston Texans": "HOU",
    "Indianapolis Colts": "IND",
    "Jacksonville Jaguars": "JAX",
    "Kansas City Chiefs": "KC",
    "Las Vegas Raiders": "LV",
    "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR",
    "Miami Dolphins": "MIA",
    "Minnesota Vikings": "MIN",
    "New England Patriots": "NE",
    "New Orleans Saints": "NO",
    "New York Giants": "NYG",
    "New York Jets": "NYJ",
    "Philadelphia Eagles": "PHI",
    "Pittsburgh Steelers": "PIT",
    "Seattle Seahawks": "SEA",
    "San Francisco 49ers": "SF",
    "Tampa Bay Buccaneers": "TB",
    "Tennessee Titans": "TEN",
    "Washington Commanders": "WAS",
}

# Extra aliases often seen across APIs (ESPN, occasional alt text)
ALIASES = {
    "Washington Football Team": "WAS",
    "LA Chargers": "LAC",
    "Los Angeles C": "LAC",
    "LA Rams": "LAR",
    "St. Louis Rams": "LAR",  # legacy but we just normalize to LAR
    "Oakland Raiders": "LV",  # legacy -> LV
    "San Diego Chargers": "LAC",  # legacy -> LAC
    "Jax Jaguars": "JAX",
    "New Orleans": "NO",
    "New England": "NE",
    "Tampa Bay": "TB",
    "San Francisco": "SF",
    "Green Bay": "GB",
    "Kansas City": "KC",
    "New York Jets": "NYJ",
    "New York Giants": "NYG",
    "Washington": "WAS",
}

def clean_name(name: str) -> str:
    return re.sub(r'\s+', ' ', name or "").strip()

def dk_to_code(team_name: str) -> str | None:
    n = clean_name(team_name)
    if n in NAME_TO_TEAM_CODE:
        return NAME_TO_TEAM_CODE[n]
    if n in ALIASES:
        return ALIASES[n]
    # Try partial city-only matches (e.g., "Green Bay")
    for full, code in NAME_TO_TEAM_CODE.items():
        if n.lower() == full.lower().split(" ")[0] + " " + full.lower().split(" ")[1] if " " in full else n.lower():
            return code
        if n.lower() == full.lower().split(" ")[0]:
            return code
    # Last resort: exact case-insensitive full match
    for full, code in NAME_TO_TEAM_CODE.items():
        if n.lower() == full.lower():
            return code
    return None

def code_to_name(code: str) -> str:
    return TEAM_CODE_TO_NAME.get(code, code)

ALL_TEAM_CODES = list(TEAM_CODE_TO_NAME.keys())
ALL_TEAM_NAMES = list(NAME_TO_TEAM_CODE.keys())
