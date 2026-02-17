from typing import Optional
from sqlalchemy.dialects.postgresql import insert
from data.postgres.entities.image import Image
from data.postgres.postgres_manager import db_manager


class ImageDao:
    def __init__(self):
        self.db = db_manager

    def _upsert_image(self, url: str, **update_values):
        """
        Internal helper to perform an atomic Upsert.
        If the URL exists, it updates only the provided fields.
        If the URL does not exist, it inserts a new record.
        """
        with self.db.get_session() as session:
            # Create the base insert statement
            stmt = insert(Image).values(url=url, **update_values)

            # Define the 'ON CONFLICT' behavior
            # index_elements must match your Primary Key or Unique Constraint
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=['url'],
                set_=update_values
            )

            session.execute(upsert_stmt)
            session.commit()

    def add_image(self, url: str, byte_data: bytes):
        """Adds or updates the original image data."""
        self._upsert_image(url, data=byte_data)

    def add_webp_image(self, url: str, webp_data: bytes):
        """Adds or updates the WebP version without losing other data."""
        self._upsert_image(url, webp_data=webp_data)

    def add_svg_image(self, url: str, svg_data: bytes):
        """Adds or updates the SVG version without losing other data."""
        self._upsert_image(url, svg_data=svg_data)

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