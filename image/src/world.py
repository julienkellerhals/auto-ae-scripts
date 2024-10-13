import pandas as pd
from bs4 import BeautifulSoup

from src.helper import get_request, post_request


def get_page_session():
    # get page session id
    session_request_error = True
    while session_request_error:
        print("Getting homepage cookies ...")
        forum_session_id_req, session_request_error, _ = get_request(
            url="http://www.airline-empires.com/index.php?/page/home.html"
        )
    return forum_session_id_req


def login(forum_session_id_req, username, password):
    login_request_error = True

    while login_request_error:
        print("Logging in ...")
        login_request, login_request_error, _ = post_request(
            url="http://www.airline-empires.com/index.php",
            cookies=forum_session_id_req.cookies,
            params={
                "app": "core",
                "module": "global",
                "section": "login",
                "do": "process",
            },
            data={
                "auth_key": "880ea6a14ea49e853634fbdc5015a024",
                "ips_username": username,
                "ips_password": password,
            },
        )
    return login_request


def get_world(login_request):
    world_request_error = True
    airline_cols = [
        "worldName",
        "name",
        "idleAircraft",
        "DOP",
        "cash",
        "worldId",
        "userId",
    ]
    airline_df = pd.DataFrame(columns=airline_cols)

    # get worlds
    while world_request_error:
        worldReq, world_request_error, errorCode = get_request(
            url="http://www.airline-empires.com/index.php?app=ae",
            cookies=login_request.cookies,
        )
        if errorCode == 401:
            break

    if not world_request_error:
        worldPage = BeautifulSoup(worldReq.text, "html.parser")
        htmlWorldList = worldPage.find_all("div", "category_block block_wrap")
        for world in htmlWorldList:
            worldName = world.find("h3", "maintitle").text
            worldTable = world.find("table")
            airlinesTable = worldTable.find_all("tr", "row1")

            for airlineTable in airlinesTable:
                airlineName = airlineTable.find_all("td")[2].text.strip()
                airlineIdleAircraft = airlineTable.find_all("td")[5].text
                airlineDOP = airlineTable.find_all("td")[7].text
                airlineCash = airlineTable.find_all("td")[8].text
                airlineWorldId = (
                    airlineTable.find_all("input")[0].attrs["value"].strip()
                )
                airlineUserId = airlineTable.find_all("input")[1].attrs["value"].strip()

                airline = pd.Series(
                    [
                        worldName,
                        airlineName,
                        airlineIdleAircraft,
                        airlineDOP,
                        airlineCash,
                        airlineWorldId,
                        airlineUserId,
                    ],
                    index=airline_cols,
                )
                airline_df = pd.concat([airline_df, airline.to_frame().T])

        print(
            airline_df.to_string(
                columns=["worldName", "name", "idleAircraft", "DOP", "cash"],
                index=False,
            )
        )

    return worldReq, airline_df, world_request_error


def do_login(forum_session_id_request, username: str, password: str):
    login_error = True
    while login_error:
        login_request = login(forum_session_id_request, username, password)
        world_request, airline_df, login_error = get_world(login_request)

    return world_request, airline_df


def enter_world(worldReq, gameServer):
    phpSessidReqError = True
    while phpSessidReqError:
        # enter world and get php session
        phpSessidReq, phpSessidReqError, _ = post_request(
            url="http://www.airline-empires.com/index.php?app=ae&module=gameworlds&section=enterworld",
            cookies=worldReq.cookies,
            data=gameServer,
        )
    return phpSessidReq


def do_enter_world(
    world_name: str, airline_name: str, airline_df: pd.DataFrame, world_request
):
    world_id = (
        airline_df[["worldId"]]
        .loc[
            (airline_df["worldName"] == world_name)
            & (airline_df["name"] == airline_name)
        ]
        .to_string(header=False, index=False)
        .strip()
    )
    user_id = (
        airline_df[["userId"]]
        .loc[
            (airline_df["worldName"] == world_name)
            & (airline_df["name"] == airline_name)
        ]
        .to_string(header=False, index=False)
        .strip()
    )

    game_server = {"world": world_id, "userid": user_id}

    php_session_id_request = enter_world(world_request, game_server)
    return php_session_id_request
