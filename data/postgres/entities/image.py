from sqlalchemy import Column, String, LargeBinary
from data.postgres.postgres_manager import Base


class Image(Base):
    __tablename__ = 'images'

    url = Column(String(1000), primary_key=True)
    # Changed to nullable=True
    data = Column(LargeBinary, nullable=True)
    webp_data = Column(LargeBinary, nullable=True)
    svg_data = Column(LargeBinary, nullable=True)