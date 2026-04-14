from typing import Optional
from sqlalchemy.dialects.postgresql import insert
from data.postgres.entities.composite import Composite
from data.postgres.postgres_manager import db_manager

class CompositeDao:
    def __init__(self) -> None:
        self.db = db_manager

    def _upsert_composite(self, wallet: str, **update_values) -> None:
        """
        Internal helper to perform an atomic Upsert for composite data.
        """
        with self.db.get_session() as session:
            stmt = insert(Composite).values(wallet=wallet, **update_values)

            # Update the data and type if a conflict on wallet occurs
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=['wallet'],
                set_=update_values
            )

            session.execute(upsert_stmt)
            session.commit()

    def add_composite_data(self, wallet: str, data_type: str, byte_data: bytes) -> None:
        """Adds or updates the binary data and its type for a wallet."""
        self._upsert_composite(wallet, type=data_type, data=byte_data)

    def get_composite_data(self, wallet: str) -> Optional[bytes]:
        """Retrieves the binary data for a specific wallet."""
        with self.db.get_session() as session:
            composite = session.get(Composite, wallet)
            return composite.data if composite else None

    def get_composite_type(self, wallet: str) -> Optional[str]:
        """Retrieves the type string for a specific wallet."""
        with self.db.get_session() as session:
            composite = session.get(Composite, wallet)
            return composite.type if composite else None

    def delete_composite(self, wallet: str) -> bool:
        """
        Deletes a composite record by wallet ID.
        Returns True if a record was deleted, False otherwise.
        """
        with self.db.get_session() as session:
            # Using session.get and session.delete for simplicity
            obj = session.get(Composite, wallet)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False