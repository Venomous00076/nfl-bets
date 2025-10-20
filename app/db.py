from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from .config import settings

ENGINE: Engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
