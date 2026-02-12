from sqlalchemy import desc, func
from data.postgres.entities.user import User
from data.postgres.postgres_manager import db_manager


class ReactionsDao:
    def __init__(self):
        self.db = db_manager

    def update_reaction_count(self, user_id: int, amount: int):
        """Updates the reaction count, ensuring it never drops below 0."""
        with self.db.get_session() as session:
            user = session.get(User, user_id)
            if user:
                # Calculate new count, ensuring it stays non-negative
                user.reaction_count = max(0, (user.reaction_count or 0) + amount)
                session.commit()
            else:
                # If user doesn't exist, create them (mirroring Firestore .set logic)
                new_user = User(id=user_id, reaction_count=max(0, amount))
                session.add(new_user)
                session.commit()

    def get_reaction_count(self, user_id: int) -> int:
        """Returns the reaction count or 0 if user not found."""
        with self.db.get_session() as session:
            user = session.get(User, user_id)
            return user.reaction_count if user else 0

    def get_user_position(self, user_id: int) -> int | None:
        """Calculates leaderboard rank (1-based) by counting users with more reactions."""
        with self.db.get_session() as session:
            # First, get the specific user's count
            user_count = session.query(User.reaction_count).filter(User.id == user_id).scalar()

            if user_count is None:
                return None

            # Count how many users have a strictly higher reaction_count
            higher_count = session.query(func.count(User.id)).filter(
                User.reaction_count > user_count
            ).scalar()

            return higher_count + 1

    def get_reaction_leaderboard(self, limit: int = 10, offset: int = 0) -> list[dict]:
        """Fetches a paginated list of top users by reaction count."""
        with self.db.get_session() as session:
            users = (
                session.query(User)
                .order_by(desc(User.reaction_count))
                .filter(User.reaction_count > 0)
                .limit(limit)
                .offset(offset)
                .all()
            )

            return [
                {
                    "user_id": str(u.id),
                    "reaction_count": u.reaction_count
                } for u in users
            ]