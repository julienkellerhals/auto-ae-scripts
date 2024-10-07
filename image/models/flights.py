import sys
from typing import Optional
from datetime import datetime

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import Session
from sqlalchemy.orm import mapped_column

from models.db import Base
from models.db import ENGINE


class Flights(Base):
    __tablename__ = "flights"
    id: Mapped[int] = mapped_column(primary_key=True)
    airport: Mapped[str]
    flight_url: Mapped[str]
    slots: Mapped[int]
    gates_available: Mapped[bool]
    freq_f: Mapped[float]
    flight_demand_f: Mapped[int]
    freq_c: Mapped[float]
    flight_demand_c: Mapped[int]
    freq_y: Mapped[float]
    flight_demand_y: Mapped[int]
    avg_freq: Mapped[float]
    configuration_criteria: Mapped[Optional[bool]]
    flight_created: Mapped[bool]
    configuration_id: Mapped[int]
    inserted_at: Mapped[datetime]
    updated_at: Mapped[datetime]


def get_flight_by_id(
    _id: int,
    session: Session | None = None,
) -> Flights:
    if session is None:
        session = Session(ENGINE)

    stmt = select(Flights).where(Flights.id == _id)

    flight = session.scalar(stmt)

    if flight is None:
        sys.exit()

    return flight


def add_flight(configuration_id: int, flights: pd.DataFrame) -> None:
    session = Session(ENGINE)

    for _, flight in flights.iterrows():
        f = Flights(
            airport=flight["airport"],
            flight_url=flight["flightUrl"],
            slots=flight["slots"],
            gates_available=flight["gatesAvailable"],
            freq_f=None,
            flight_demand_f=None,
            freq_c=None,
            flight_demand_c=None,
            freq_y=None,
            flight_demand_y=None,
            avg_freq=None,
            configuration_criteria=None,
            flight_created=flight["flightCreated"],
            configuration_id=configuration_id,
            inserted_at=datetime.now(),
            updated_at=datetime.now(),
        )
        session.add(f)
    session.commit()


def add_flight_demand(
    flight_id: int, flight_demand_f: int, flight_demand_c: int, flight_demand_y: int
) -> None:
    session = Session(ENGINE)

    flight = get_flight_by_id(flight_id, session)

    if flight is None:
        sys.exit()

    flight.flight_demand_f = flight_demand_f
    flight.flight_demand_c = flight_demand_c
    flight.flight_demand_y = flight_demand_y
    session.commit()


def add_frequency(
    flight_id: int,
    frequency_f: float,
    frequency_c: float,
    frequency_y: float,
    average_frequency: float,
) -> None:
    session = Session(ENGINE)

    flight = get_flight_by_id(flight_id, session)

    if flight is None:
        sys.exit()

    flight.freq_f = frequency_f
    flight.freq_c = frequency_c
    flight.freq_y = frequency_y
    flight.avg_freq = average_frequency
    session.commit()


def set_configuration_criteria(
    flight_id: int,
    state: bool,
) -> None:
    session = Session(ENGINE)

    flight = get_flight_by_id(flight_id, session)

    if flight is None:
        sys.exit()

    flight.configuration_criteria = state
    session.commit()
