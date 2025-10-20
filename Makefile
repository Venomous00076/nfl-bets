.PHONY: up logs etl features odds injuries pipeline score api reset

up:
	docker compose up -d --build

logs:
	docker compose logs -f app

etl:
	docker compose exec app python -m app.etl.nflsavant

features:
	docker compose exec app python -m app.features

odds:
	docker compose exec app python -m app.etl.odds_draftkings

injuries:
	docker compose exec app python -m app.etl.espn_injuries

pipeline:
	docker compose exec app python -m app.pipeline

score:
	docker compose exec app python -c 'from app.score_and_edge import run_edges_for_latest_snapshot; s,df=run_edges_for_latest_snapshot(); print("snapshot:", s, "rows:", len(df))'

api:
	docker compose exec app uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload

reset:
	docker compose down -v
