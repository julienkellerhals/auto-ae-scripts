import numpy as np

from src.api import add_hub, create_flight, get_flight_demand, get_available_aircraft
from models.flights import (
    get_flight_by_id,
    add_flight_demand,
    add_frequency,
    set_configuration_criteria,
)
from models.accounts import get_account_by_id
from models.configurations import get_configuration_by_id


def main(flight_id: int) -> None:
    flight = get_flight_by_id(flight_id)
    configuration = get_configuration_by_id(flight.configuration_id)
    account = get_account_by_id(configuration["account_id"])

    # Add hub
    if configuration["auto_hub"] is True:
        add_hub(account.session_id, configuration["departure_airport_code"])

    # Demand
    flight_demand_f, flight_demand_c, flight_demand_y = get_flight_demand(
        account.session_id, flight
    )
    add_flight_demand(flight_id, flight_demand_f, flight_demand_c, flight_demand_y)
    flight.flight_demand_f = flight_demand_f
    flight.flight_demand_c = flight_demand_c
    flight.flight_demand_y = flight_demand_y

    # Availability
    available_aircraft_df, new_flights_page = get_available_aircraft(
        session_id=account.session_id,
        departure_airport_code=configuration["departure_airport_code"],
        target_airport_code=flight.airport,
    )

    if available_aircraft_df is None:
        return

    # find correct aircraft
    if configuration["aircraft"] == "" or configuration["aircraft"] is None:
        return

    available_aircraft_df = available_aircraft_df.loc[
        available_aircraft_df["type"] == configuration["aircraft"]
    ]
    if available_aircraft_df.empty:
        print("No aircraft of this type available for this route")
        return

    available_aircraft_df = available_aircraft_df.loc[
        available_aircraft_df["reducedCapacity"] == False
    ]

    if available_aircraft_df.empty:
        print("No aircraft of this type available for this route")
        return

    available_aircraft_df["seatReqF"] = flight.flight_demand_f
    available_aircraft_df["seatReqC"] = flight.flight_demand_c
    available_aircraft_df["seatReqY"] = flight.flight_demand_y

    available_aircraft_df["freqF"] = (
        available_aircraft_df["seatReqF"] / available_aircraft_df["seatF"]
    )
    available_aircraft_df["freqC"] = (
        available_aircraft_df["seatReqC"] / available_aircraft_df["seatC"]
    )
    available_aircraft_df["freqY"] = (
        available_aircraft_df["seatReqY"] / available_aircraft_df["seatY"]
    )

    available_aircraft_df = available_aircraft_df.replace([np.inf, -np.inf], np.nan)
    available_aircraft_df["avgFreq"] = (
        available_aircraft_df[["freqF", "freqC", "freqY"]].mean(axis=1) + 0.5
    )
    available_aircraft_df["avgFreq"] = available_aircraft_df["avgFreq"].apply(np.ceil)

    add_frequency(
        flight_id,
        max(available_aircraft_df["freqF"]),
        max(available_aircraft_df["freqC"]),
        max(available_aircraft_df["freqY"]),
        max(available_aircraft_df["avgFreq"]),
    )
    flight.freq_f = max(available_aircraft_df["freqF"])
    flight.freq_c = max(available_aircraft_df["freqC"])
    flight.freq_y = max(available_aircraft_df["freqY"])
    flight.avg_freq = max(available_aircraft_df["avgFreq"])

    # Check if criteria are met
    if configuration["min_frequency"] is not None:
        if flight.avg_freq < int(configuration["min_frequency"]):
            set_configuration_criteria(flight_id, False)
            flight.configuration_criteria = False

    if configuration["max_frequency"] is not None:
        if flight.avg_freq > int(configuration["max_frequency"]):
            set_configuration_criteria(flight_id, False)
            flight.configuration_criteria = False

    if flight.configuration_criteria:
        create_flight(
            session_id=account.session_id,
            departure_airport_code=configuration["departure_airport_code"],
            auto_slot=configuration["auto_slot"],
            auto_terminal=configuration["auto_terminal"],
            flight=flight,
            new_flights_page=new_flights_page,
            available_aircraft_df=available_aircraft_df,
        )


def handler(event, context):
    main(
        int(event["flight_id"]),
    )
    return {"statusCode": 200, "body": event}


if __name__ == "__main__":
    FLIGHT_ID = 0
    main(FLIGHT_ID)
