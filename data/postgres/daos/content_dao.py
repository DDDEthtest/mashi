from typing import Optional
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete
from data.postgres.entities.contest import Contest
from data.postgres.postgres_manager import db_manager


class ContestDao:
    def __init__(self):
        self.db = db_manager

    def _upsert_contest(self, msg_id: int, **update_values):
        """
        Internal helper for atomic Upsert.
        If the msg_id exists, it updates provided fields.
        If not, it inserts.
        """
        with self.db.get_session() as session:
            stmt = insert(Contest).values(msg_id=msg_id, **update_values)

            # On conflict with the primary key (msg_id), update the fields
            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=['msg_id'],
                set_=update_values if update_values else {"msg_id": msg_id}
            )

            session.execute(upsert_stmt)
            session.commit()

    def init(self, msg_id: int):
        """
        Initializes the contest.
        Clears existing data first to ensure only one active contest exists.
        """
        self.reset()
        self._upsert_contest(msg_id)

    def reset(self):
        """Deletes the current contest record."""
        with self.db.get_session() as session:
            session.execute(delete(Contest))
            session.commit()

    def get_contest_id(self) -> Optional[int]:
        """Retrieves the current active contest message ID."""
        with self.db.get_session() as session:
            # Since it's a singleton, we just get the first row
            contest = session.query(Contest).first()
            return contest.msg_id if contest else None