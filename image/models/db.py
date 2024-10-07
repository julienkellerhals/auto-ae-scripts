import os

from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase


connection_string = URL.create(
    "postgresql",
    username=os.environ.get("DB_USERNAME"),
    password=os.environ.get("DB_PASSWORD"),
    host=os.environ.get("DB_URL"),
    database=os.environ.get("DATABASE"),
)

ENGINE = create_engine(connection_string, connect_args={"sslmode": "require"})


class Base(DeclarativeBase):
    pass
