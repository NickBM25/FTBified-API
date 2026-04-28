from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv
from sqlmodel import Session
import os

# Load environment variables from .env
load_dotenv()

# Fetch variables
USER = os.getenv("DB_USER")
PASSWORD = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOSTNAME")
PORT = os.getenv("DB_PORT")
DBNAME = os.getenv("DB_NAME")

# Construct the SQLAlchemy connection string
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"

# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    connect_args={"sslmode": "require", "sslrootcert": "disable"}
)

def get_session():
    with Session(engine) as session:
        yield session

if __name__ == "__main__":
    # Test the connection
    try:
        with engine.connect() as connection:
            print("Connection successful!")
    except Exception as e:
        print(f"Failed to connect: {e}")