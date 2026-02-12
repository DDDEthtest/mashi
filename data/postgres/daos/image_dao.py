from data.postgres.entities.image import Image
from data.postgres.postgres_manager import db_manager
from typing import Optional

class ImageDao:
    def __init__(self):
        self.db = db_manager

    def add_image(self, url: str, byte_data: bytes):
        """Adds or updates the original image data."""
        with self.db.get_session() as session:
            img = session.get(Image, url)
            if img:
                img.data = byte_data
            else:
                session.add(Image(url=url, data=byte_data))
            session.commit()

    def add_webp_image(self, url: str, webp_data: bytes):
        """Adds or updates the WebP version without losing original/SVG data."""
        with self.db.get_session() as session:
            img = session.get(Image, url)
            if img:
                img.webp_data = webp_data
            else:
                session.add(Image(url=url, webp_data=webp_data))
            session.commit()

    def add_svg_image(self, url: str, svg_data: bytes):
        """Adds or updates the SVG version without losing original/WebP data."""
        with self.db.get_session() as session:
            img = session.get(Image, url)
            if img:
                img.svg_data = svg_data
            else:
                session.add(Image(url=url, svg_data=svg_data))
            session.commit()

    def get_image(self, url: str) -> Optional[bytes]:
        with self.db.get_session() as session:
            img = session.get(Image, url)
            return img.data if img else None

    def get_webp_image(self, url: str) -> Optional[bytes]:
        with self.db.get_session() as session:
            img = session.get(Image, url)
            return img.webp_data if img else None

    def get_svg_image(self, url: str) -> Optional[bytes]:
        with self.db.get_session() as session:
            img = session.get(Image, url)
            return img.svg_data if img else None