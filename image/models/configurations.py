import sys
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column

from models.db import Base
from models.db import ENGINE
from models.aircraft import Aircraft


class Configurations(Base):
    __tablename__ = "configurations"
    id: Mapped[int] = mapped_column(primary_key=True)
    country: Mapped[Optional[str]]
    region: Mapped[Optional[str]]
    min_range: Mapped[Optional[int]]
    max_range: Mapped[Optional[int]]
    departure_airport_code: Mapped[str]
    auto_slot: Mapped[bool]
    auto_terminal: Mapped[bool]
    auto_hub: Mapped[bool]
    min_frequency: Mapped[Optional[int]]
    max_frequency: Mapped[Optional[int]]
    account_id: Mapped[int]
    user_id: Mapped[int]
    aircraft_id: Mapped[int]


def get_configuration_by_id(_id: int) -> dict:
    session = Session(ENGINE)

    stmt = select(Configurations).where(Configurations.id == _id)

    configuration = session.scalar(stmt)

    if configuration is None:
        sys.exit()

    stmt = select(Aircraft).where(Aircraft.id == configuration.aircraft_id)

    aircraft = session.scalar(stmt)

    if aircraft is None:
        sys.exit()

    return {**configuration.__dict__, **aircraft.__dict__}
