from sqlalchemy import Column, BigInteger, DateTime
from sqlalchemy.sql import func
from data.postgres.postgres_manager import Base

class Mashup(Base):
    __tablename__ = 'mashups'

    # Using BigInteger for Discord/Telegram IDs
    msg_id = Column(BigInteger, primary_key=True, autoincrement=False)
    channel_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())