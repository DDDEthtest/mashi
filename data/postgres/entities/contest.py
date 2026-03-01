from sqlalchemy import Column, String, LargeBinary, BigInteger
from data.postgres.postgres_manager import Base


class Contest(Base):
    __tablename__ = 'contests'

    msg_id = Column(BigInteger, primary_key=True, autoincrement=False)
