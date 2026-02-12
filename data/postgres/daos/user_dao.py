from data.postgres.entities.user import User  # Adjust path as needed
from data.postgres.postgres_manager import db_manager
from sqlalchemy.exc import IntegrityError


class UserDao:
    def __init__(self):
        self.db = db_manager

    def connect_wallet(self, user_id: int, wallet: str):
        """Creates or updates a user's wallet using an 'upsert' pattern."""
        with self.db.get_session() as session:
            # We use session.get() for primary key lookups (cleaner than filter_by)
            user = session.get(User, user_id)

            if user:
                user.wallet = wallet
            else:
                user = User(id=user_id, wallet=wallet)
                session.add(user)

            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                # Handle the case where the wallet string is already taken by another ID
                raise ValueError(f"Wallet address '{wallet}' is already registered.")

    def disconnect_wallet(self, user_id: int):
        """Deletes the user record."""
        with self.db.get_session() as session:
            user = session.get(User, user_id)
            if user:
                session.delete(user)
                session.commit()

    def get_wallet(self, user_id: int) -> str | None:
        """Returns the wallet address if the user exists."""
        with self.db.get_session() as session:
            user = session.get(User, user_id)
            return user.wallet if user else None

    def check_if_wallet_taken(self, wallet: str) -> bool:
        """Checks if the wallet address is already in the database."""
        with self.db.get_session() as session:
            exists = session.query(User).filter_by(wallet=wallet).first()
            return exists is not None
