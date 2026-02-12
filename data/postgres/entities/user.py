from sqlalchemy import Column, String, BigInteger, Integer
from data.postgres.postgres_manager import Base


class User(Base):
    __tablename__ = 'users'

    # autoincrement=False tells SQLAlchemy/Postgres NOT to generate this ID
    id = Column(BigInteger, primary_key=True, autoincrement=False)
    wallet = Column(String(128), nullable=False, unique=True)
    reaction_count = Column(Integer, default=0)