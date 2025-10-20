CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS raw_pbp (
  season int,
  game_id text,
  play_id bigint,
  posteam text,
  defteam text,
  qtr int,
  down int,
  ydstogo int,
  yardline_100 int,
  play_type text,
  yards_gained int,
  epa numeric,
  success boolean,
  score_home int,
  score_away int,
  game_date date,
  PRIMARY KEY (game_id, play_id)
);

CREATE TABLE IF NOT EXISTS games (
  season int,
  week int,
  game_id text PRIMARY KEY,
  home_team text,
  away_team text,
  kickoff_ts timestamptz
);

CREATE TABLE IF NOT EXISTS injuries (
  snapshot_ts timestamptz,
  team text,
  player_id text,
  status text,
  position text,
  is_out boolean,
  PRIMARY KEY(snapshot_ts, player_id)
);

CREATE TABLE IF NOT EXISTS odds_raw (
  snapshot_ts timestamptz,
  event_id text,
  book text,
  market text,
  outcome text,
  price_american int,
  point numeric,
  line_ts timestamptz,
  home_team text,
  away_team text,
  commence_time timestamptz,
  PRIMARY KEY(snapshot_ts, event_id, book, market, outcome, point)
);

CREATE TABLE IF NOT EXISTS team_features (
  season int,
  team text,           -- standardized team code (e.g., KC, DAL)
  feat jsonb,
  asof_game text,
  PRIMARY KEY(season, team, asof_game)
);

CREATE TABLE IF NOT EXISTS projections (
  season int,
  game_id text,
  home_team text,      -- standardized team code
  away_team text,      -- standardized team code
  proj_home_pts numeric,
  proj_away_pts numeric,
  proj_spread numeric,
  proj_total numeric,
  home_wp numeric,
  asof_snapshot timestamptz,
  PRIMARY KEY(season, game_id, asof_snapshot)
);

CREATE TABLE IF NOT EXISTS recommendations (
  snapshot_ts timestamptz,
  game_id text,
  home_team text,
  away_team text,
  market text,
  selection text,      -- e.g., home, away, home +3.5, over 46.5
  best_book text,
  best_price int,
  line_point numeric,
  model_prob numeric,
  edge numeric,
  kelly_frac numeric,
  confidence text,
  notes text,
  PRIMARY KEY(snapshot_ts, game_id, market, selection, line_point)
);
