from src.aircraft import get_aircraft_stats
from models.accounts import get_account_by_id
from models.aircraft import update_aircraft


def main(account_id: int, user_id: int) -> None:
    account = get_account_by_id(account_id)

    aircraft_stats_df = get_aircraft_stats(account.session_id)
    update_aircraft(account_id, aircraft_stats_df, user_id)


def handler(event, context):
    main(
        int(event["account_id"]),
        int(event["user_id"]),
    )
    return {"statusCode": 200, "body": event}


if __name__ == "__main__":
    ACCOUNT_ID = 0
    USER_ID = 0
    main(ACCOUNT_ID, USER_ID)
