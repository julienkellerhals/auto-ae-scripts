from datetime import datetime

import pandas as pd
from sqlalchemy import select
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
    inserted_at: Mapped[datetime]
    updated_at: Mapped[datetime]


def get_aircraft_by_name_range_min_runway(
    aircraft: int,
    _range: int,
    min_runway: int,
    account_id: int,
    user_id: int,
    session: Session | None = None,
) -> Aircraft | None:
    if session is None:
        session = Session(ENGINE)

    stmt = (
        select(Aircraft)
        .where(Aircraft.aircraft == aircraft)
        .where(Aircraft.range == _range)
        .where(Aircraft.min_runway == min_runway)
        .where(Aircraft.account_id == account_id)
        .where(Aircraft.user_id == user_id)
    )

    return session.scalar(stmt)


def add_aircraft(account_id: int, aircraft_stats: pd.DataFrame, user_id: int):
    session = Session(ENGINE)

    for _, aircraft in aircraft_stats.iterrows():
        aircraft = Aircraft(
            aircraft=aircraft["aircraft"],
            range=aircraft["range"],
            min_runway=aircraft["min_runway"],
            account_id=account_id,
            user_id=user_id,
            inserted_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(aircraft)
    session.commit()


def update_aircraft(
    account_id: int, aircraft_stats: pd.DataFrame, user_id: int
) -> None:
    session = Session(ENGINE)

    for _, aircraft in aircraft_stats.iterrows():
        db_aircraft = get_aircraft_by_name_range_min_runway(
            aircraft["aircraft"],
            aircraft["range"],
            aircraft["min_runway"],
            account_id,
            user_id,
        )

        if db_aircraft is None:
            new_aircraft = Aircraft(
                aircraft=aircraft["aircraft"],
                range=aircraft["range"],
                min_runway=aircraft["min_runway"],
                account_id=account_id,
                user_id=user_id,
                inserted_at=datetime.now(),
                updated_at=datetime.now(),
            )
            session.add(new_aircraft)
    session.commit()
