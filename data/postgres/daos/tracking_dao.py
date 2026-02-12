from data.postgres.entities.mashup import Mashup
from data.postgres.postgres_manager import db_manager

class TrackingDao:
    def __init__(self):
        self.db = db_manager

    def insert_mashup(self, msg_id: int, channel_id: int):
        """Inserts a new mashup record."""
        with self.db.get_session() as session:
            # .merge() handles the "set" logic (insert or overwrite)
            new_mashup = Mashup(msg_id=msg_id, channel_id=channel_id)
            session.merge(new_mashup)
            session.commit()

    def delete_mashup(self, msg_id: int):
        """
        Deletes the mashup by msg_id.
        Replaces the complex Firestore collection_group scan.
        """
        with self.db.get_session() as session:
            mashup = session.get(Mashup, msg_id)
            if mashup:
                session.delete(mashup)
                session.commit()

    def get_mashups_by_month(self, month: int, year: int):
        """
        Bonus: Replicates your 'MM-YYYY' logic by filtering
        the created_at column.
        """
        from sqlalchemy import extract
        with self.db.get_session() as session:
            return session.query(Mashup).filter(
                extract('month', Mashup.created_at) == month,
                extract('year', Mashup.created_at) == year
            ).all()