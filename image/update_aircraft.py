from src.api import get_aircraft_stats
from models.accounts import get_account_by_id
from models.aircraft import add_aircraft


def main(account_id: int, user_id: int) -> None:
    account = get_account_by_id(account_id)

    aircraft_stats_df = get_aircraft_stats(account.session_id)
    add_aircraft(account_id, aircraft_stats_df, user_id)


def handler(event, context):
    main(
        int(event["account_id"]),
        int(event["user_id"]),
    )
    return {"statusCode": 200, "body": event}
