from sqlalchemy import Column, LargeBinary, String

from data.postgres.postgres_manager import Base


class Composite(Base):
    __tablename__ = 'composites'

    wallet = Column(String(255), primary_key=True)
    type = Column(String(50), nullable=False)
    data = Column(LargeBinary, nullable=False)