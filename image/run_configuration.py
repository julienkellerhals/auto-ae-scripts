from src.api import get_flights, add_hub, create_flight
from models.accounts import get_account_by_id
from models.configurations import get_configuration_by_id


def main(account_id: int, configuration_id: int) -> None:
    account = get_account_by_id(account_id)
    configuration = get_configuration_by_id(configuration_id)

    search_params = {
        "country": configuration["country"],
        "region": configuration["region"],
        "runway": configuration["min_runway"],
        "rangemin": configuration["min_range"],
        "rangemax": configuration["max_range"],
        "city": configuration["departure_airport_code"],
    }

    search_params = {k: ("" if v is None else v) for k, v in search_params.items()}

    _, flights_df = get_flights(account.session_id, search_params)

    available_flights_df = flights_df.loc[flights_df["flightCreated"] == False]  # noqa: E712

    if not available_flights_df.empty:
        print("Available flights")
        print(available_flights_df.to_string(index=False))

        # Add hub
        if configuration["auto_hub"] is True:
            add_hub(account.session_id, configuration["departure_airport_code"])

        for _, flight in available_flights_df.iterrows():
            create_flight(
                session_id=account.session_id,
                departure_airport_code=configuration["departure_airport_code"],
                aircraft=configuration["aircraft"],
                reduced_capacity_flag=False,
                auto_slot=configuration["auto_slot"],
                auto_terminal=configuration["auto_terminal"],
                min_frequency=configuration["min_frequency"],
                max_frequency=configuration["max_frequency"],
                flight=flight,
            )
    else:
        print("No new flights available.")


def handler(event, context):
    main(
        int(event["account_id"]),
        int(event["configuration_id"]),
    )
    return {"statusCode": 200, "body": event}


if __name__ == "__main__":
    ACCOUNT_ID = 0
    CONFIGURATION_ID = 0
    main(ACCOUNT_ID, CONFIGURATION_ID)
