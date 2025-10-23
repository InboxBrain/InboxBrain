import os
from sqlalchemy import create_engine

DB_DSN = os.getenv("DB_DSN", "mysql+pymysql://app:app@mysql:3306/inboxbrain")
engine = create_engine(DB_DSN, pool_pre_ping=True, pool_recycle=3600)
