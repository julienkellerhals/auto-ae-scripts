from src.api import get_page_session, do_login
from models.accounts import update_airlines


def main(username: str, password: str, user_id: int) -> None:
    forum_session_id_request = get_page_session()
    _, airlines_df = do_login(forum_session_id_request, username, password)
    update_airlines(username, user_id, airlines_df)


def handler(event, context):
    main(event["username"], event["password"], int(event["user_id"]))
    return {"statusCode": 200, "body": event}
