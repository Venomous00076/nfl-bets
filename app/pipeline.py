"""
End-to-end one-shot pipeline:
1) Ingest NFLsavant PBP (last 2 seasons)
2) Build recent-form features
3) Pull DraftKings odds (featured markets)
4) Build projections at the odds snapshot
5) Compute edges & persist recommendations
"""
import pandas as pd
from .etl.nflsavant import run_nflsavant_ingest
from .etl.odds_draftkings import run_odds_ingest
from .etl.espn_injuries import run_espn_injuries
from .features import run_features
from .models_core import build_projections, persist_projections
from .score_and_edge import run_edges_for_latest_snapshot
from .db import ENGINE

def latest_snapshot() -> str | None:
    q="SELECT snapshot_ts FROM odds_raw ORDER BY snapshot_ts DESC LIMIT 1"
    df = pd.read_sql(q, ENGINE)
    return df.iloc[0,0] if not df.empty else None

def run_all():
    print("[1/5] Ingest NFLsavant PBP...")
    run_nflsavant_ingest()

    print("[2/5] Build features (recent-form blend)...")
    run_features()

    print("[3/5] Pull DraftKings odds...")
    run_odds_ingest()

    print("[3b/5] (Optional) Pull ESPN injuries...")
    try:
        run_espn_injuries()
    except Exception:
        pass

    snap = latest_snapshot()
    if not snap:
        raise RuntimeError("No odds snapshot available (DraftKings).")
    print(f"[4/5] Build projections @ {snap}...")
    proj = build_projections(snapshot_ts=snap)
    persist_projections(proj, snapshot_ts=snap)

    print("[5/5] Compute edges & save recommendations...")
    snap2, recs = run_edges_for_latest_snapshot()
    print(f"Done. Snapshot={snap2}, recs={len(recs)}")

if __name__ == "__main__":
    run_all()
