from src.api import get_page_session, do_login, do_enter_world
from models.accounts import add_session_id


def main(username: str, password: str, world: str, airline: str, user_id: int) -> None:
    forum_session_id_request = get_page_session()
    world_request, airline_df = do_login(forum_session_id_request, username, password)
    php_session_id_request = do_enter_world(world, airline, airline_df, world_request)

    add_session_id(
        user_id=user_id,
        username=username,
        world=world,
        airline=airline,
        session_id=php_session_id_request.cookies.get("PHPSESSID"),
    )


def handler(event, context):
    main(
        event["username"],
        event["password"],
        event["world"],
        event["airline"],
        int(event["user_id"]),
    )
    return {"statusCode": 200, "body": event}
