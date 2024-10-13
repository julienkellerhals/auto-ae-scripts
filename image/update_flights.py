from src.flight import get_flights
from models.flights import add_flight
from models.accounts import get_account_by_id
from models.configurations import get_configuration_by_id


def main(configuration_id: int) -> None:
    configuration = get_configuration_by_id(configuration_id)
    account = get_account_by_id(configuration["account_id"])

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
    add_flight(configuration_id, flights_df)


def handler(event, context):
    main(
        int(event["configuration_id"]),
    )
    return {"statusCode": 200, "body": event}


if __name__ == "__main__":
    CONFIGURATION_ID = 0
    main(CONFIGURATION_ID)
