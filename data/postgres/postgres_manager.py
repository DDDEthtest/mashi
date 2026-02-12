import psycopg
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import threading

Base = declarative_base()


class PostgresManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(PostgresManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, db_url: str):
        if hasattr(self, '_initialized') and self._initialized:
            return

        # 1. Ensure the physical database exists
        self._ensure_db_exists(db_url)

        # 2. Setup SQLAlchemy
        self.engine = create_engine(db_url, echo=False, pool_pre_ping=True)
        self.SessionFactory = sessionmaker(bind=self.engine)

        # 3. Create tables
        Base.metadata.create_all(self.engine)

        self._initialized = True

    def _ensure_db_exists(self, db_url: str):
        """Connects to 'postgres' db to create the target db if missing."""
        # Split URL to get the target DB name and the base connection string
        base_url, db_name = db_url.rsplit('/', 1)
        # Force connection to the default 'postgres' maintenance DB
        temp_url = f"{base_url}/postgres"

        # Psycopg3 requires autocommit mode to run CREATE DATABASE
        with psycopg.connect(temp_url.replace("postgresql+psycopg://", "postgresql://"), autocommit=True) as conn:
            with conn.cursor() as cur:
                # Check if db exists
                cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
                if not cur.fetchone():
                    print(f"Database '{db_name}' not found. Creating it...")
                    cur.execute(f'CREATE DATABASE "{db_name}"')

    def get_session(self):
        return self.SessionFactory()


# Usage remains the same
DB_URI = "postgresql+psycopg://postgres:postgres@localhost:5432/mashi"
db_manager = PostgresManager(DB_URI)