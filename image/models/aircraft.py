from datetime import datetime

import pandas as pd
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column

from models.db import Base
from models.db import ENGINE


class Aircraft(Base):
    __tablename__ = "aircraft"
    id: Mapped[int] = mapped_column(primary_key=True)
    aircraft: Mapped[str]
    range: Mapped[int]
    min_runway: Mapped[int]
    account_id: Mapped[int]
    user_id: Mapped[int]
    inserted_at: Mapped[str]
    updated_at: Mapped[str]


def add_aircraft(account_id: int, aircraft_stats: pd.DataFrame, user_id: int):
    session = Session(ENGINE)

    for _, aircraft in aircraft_stats.iterrows():
        aircraft = Aircraft(
            aircraft=aircraft["aircraft"],
            range=aircraft["range"],
            min_runway=aircraft["min_runway"],
            account_id=account_id,
            user_id=user_id,
            inserted_at=str(datetime.now()),
            updated_at=str(datetime.now()),
        )
        session.add(aircraft)
        session.commit()
