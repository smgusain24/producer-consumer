from .db import engine, Base, SessionLocal
from . import models

def create_tables():
    Base.metadata.create_all(bind=engine)

create_tables()

def get_db():
    _db = SessionLocal()
    try:
        yield _db
    finally:
        _db.close()

