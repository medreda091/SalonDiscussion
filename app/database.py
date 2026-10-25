"""Configuration de la base de données (SQLite par défaut).

L'URL peut être surchargée avec la variable d'environnement DATABASE_URL,
par exemple pour les tests ou pour passer à PostgreSQL en production.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./salon.db")

# SQLite demande un réglage particulier pour être utilisé depuis plusieurs threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Fournit une session de base de données à chaque requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
