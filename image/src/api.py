import re
from typing import TYPE_CHECKING

import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests.models import Response

from meta_data import AVAILABLE_AIRCRAFT


if TYPE_CHECKING:
    pass


def tr_to_list(tr: Tag):
    row_list = []
    for td in tr:
        if td != "\n":
            row_list.append(td.text)
    return row_list


def get_request(url: str, cookies=None, params=None) -> tuple[Response, bool, str]:
    request_error = True
    error_code = None

    try:
        r = requests.get(url=url, cookies=cookies, params=params, timeout=210)
        r.raise_for_status()
        request_error = False
    except requests.exceptions.Timeout as e:
        print("request timed-out")
        print(e)
    except requests.exceptions.ConnectionError as e:
        print("connection error")
        print(e)
    except requests.exceptions.HTTPError as e:
        error_code = r.status_code
        print(e)
    except requests.exceptions.ChunkedEncodingError as e:
        print("connection error")
        print(e)
    return r, request_error, error_code


def post_request(url: str, cookies: dict, params: dict = {}, data: dict = {}):
    request_error = True
    error_code = None

    try:
        r = requests.post(url, params=params, cookies=cookies, data=data, timeout=210)
        r.raise_for_status()
        request_error = False
    except requests.exceptions.Timeout as e:
        print("request timed-out")
        print(e)
    except requests.exceptions.ConnectionError as e:
        print("connection error")
        print(e)
    except requests.exceptions.HTTPError as e:
        error_code = r.status_code
        print(e)
    except requests.exceptions.ChunkedEncodingError as e:
        print("connection error")
        print(e)
    return r, request_error, error_code


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

    php_session_id_request = enterWorld(world_request, game_server)
    return php_session_id_request


def enterWorld(worldReq, gameServer):
    phpSessidReqError = True
    while phpSessidReqError:
        # enter world and get php session
        phpSessidReq, phpSessidReqError, _ = post_request(
            url="http://www.airline-empires.com/index.php?app=ae&module=gameworlds&section=enterworld",
            cookies=worldReq.cookies,
            data=gameServer,
        )
    return phpSessidReq


def doEnterWorld(args, airlineDf, worldReq):
    tryServer = True
    while tryServer:
        # TODO Problem if airline has the same name on different server
        worldId = (
            airlineDf[["worldId"]]
            .loc[airlineDf["name"] == airlineName]
            .to_string(header=False, index=False)
            .strip()
        )
        userId = (
            airlineDf[["userId"]]
            .loc[airlineDf["name"] == airlineName]
            .to_string(header=False, index=False)
            .strip()
        )
        if "Empty DataFrame" not in worldId and "Empty DataFrame" not in userId:
            tryServer = False
        else:
            print("Airline does not exist, retry.")
    gameServer = {"world": worldId, "userid": userId}

    # enter world
    print(f"entering world {worldId} with {airlineName}")
    phpSessidReq = enterWorld(worldReq, gameServer)
    return phpSessidReq


def get_aircraft_stats(session_id: str):
    mainPageReqError = True
    getAircraftsReqError = True
    aircraftStatsCol = ["aircraft", "range", "min_runway"]
    aircraftStatsDf = pd.DataFrame(columns=aircraftStatsCol)

    while mainPageReqError:
        mainPageReq, mainPageReqError, _ = get_request(
            url="http://ae31.airline-empires.com/main.php",
            cookies={"PHPSESSID": session_id},
        )
    mainPage = BeautifulSoup(mainPageReq.text, "lxml")
    airlineDetailsHref = mainPage.find("a", text="Airline Details").attrs["href"]

    while getAircraftsReqError:
        getAircraftsReq, getAircraftsReqError, _ = get_request(
            url=("http://ae31.airline-empires.com/" + airlineDetailsHref),
            cookies={"PHPSESSID": session_id},
        )

    aircraftListPage = BeautifulSoup(getAircraftsReq.text, "lxml")
    aircraftHrefList = aircraftListPage.find_all(
        "a", href=re.compile(r"acdata.php\?aircraft*")
    )
    dedupAircraftHrefList = list(dict.fromkeys(aircraftHrefList))

    for aircraftHref in dedupAircraftHrefList:
        aircraftDetailReqError = True

        while aircraftDetailReqError:
            getAircraftDetailReq, aircraftDetailReqError, _ = get_request(
                url=("http://ae31.airline-empires.com/" + aircraftHref.attrs["href"]),
                cookies={"PHPSESSID": session_id},
            )

        aircraftDetailPage = BeautifulSoup(getAircraftDetailReq.text, "lxml")
        aircraftName = aircraftDetailPage.find_all("div", class_="pagetitle")[
            0
        ].text.replace(" Aircraft Information", "")
        engineInfoTable = aircraftDetailPage.find_all("table")[-1]

        maxRangeEngineSeries = pd.Series(["", 0, 0], index=aircraftStatsCol)
        for tr in engineInfoTable.find_all("tr")[1:]:
            engineTableRow = tr_to_list(tr)
            engineRange = int(re.sub(r" mi.*", "", engineTableRow[7]).replace(",", ""))
            engineMinRunway = int(engineTableRow[9].replace(",", ""))

            aircraftStats = pd.Series(
                [aircraftName, engineRange, engineMinRunway], index=aircraftStatsCol
            )

            if maxRangeEngineSeries["range"] < aircraftStats["range"]:
                maxRangeEngineSeries = aircraftStats
        aircraftStatsDf = pd.concat(
            [aircraftStatsDf, maxRangeEngineSeries.to_frame().T]
        )
    return aircraftStatsDf


def get_flights(session_id: str, search_params: dict):
    list_flights_request_error = True
    slots_regex = r"\((\d*).*\)"
    flights_cols = ["airport", "flightUrl", "flightCreated", "slots", "gatesAvailable"]
    flights_df = pd.DataFrame(columns=flights_cols)

    while list_flights_request_error:
        list_flights_request, list_flights_request_error, _ = get_request(
            url="http://ae31.airline-empires.com/rentgate.php",
            cookies={"PHPSESSID": session_id},
            params=search_params,
        )
    flight_list_page = BeautifulSoup(list_flights_request.text, "html.parser")
    flight_list_table = flight_list_page.find_all("form")[1]
    flight_list = flight_list_table.find_all("tr")[1:]

    for flight_row in flight_list:
        airport = flight_row.find_all("td")[0].text

        try:
            flight_url = flight_row.find_all("td")[5].find("a").attrs["href"]
        except AttributeError as e:
            print(
                f"Flight from {search_params['city']} to {airport} cannot be researched"
            )
            print(e)

        if flight_row.find_all("td")[5].find("div") is None:
            flight_created = False
        else:
            flight_created = True

        try:
            slots = re.search(slots_regex, flight_row.find_all("td")[6].text).group(1)
        except AttributeError:
            slots = None

        if flight_row.find_all("td")[10].find("input") is None:
            gates_available = False
        else:
            gates_available = True

        flight = pd.Series(
            [airport, flight_url, flight_created, slots, gates_available],
            index=flights_cols,
        )
        flights_df = pd.concat([flights_df, flight.to_frame().T])
    return list_flights_request, flights_df


def get_flight_demand(session_id: str, flight) -> list[int]:
    if re.match(r"\w{3}", flight["airport"]) is not None:
        flight_details_request_error = True
        while flight_details_request_error:
            # flight details
            flight_details_request, flight_details_request_error, _ = get_request(
                url="http://ae31.airline-empires.com/" + flight["flightUrl"],
                cookies={"PHPSESSID": session_id},
            )

        route_details_page = BeautifulSoup(flight_details_request.text, "html.parser")
        high_charts_script = str(route_details_page.findAll("script")[10])
        raw_data = re.findall(r"data: \[\d*,\d*,\d*\]", high_charts_script)[0]
        flight_demand = [
            int(x) for x in re.findall(r"\d*,\d*,\d*", raw_data)[0].split(",")
        ]

        print(
            f"{flight['airport']:20} {flight_demand[0]:10} {flight_demand[1]:10} {flight_demand[2]:10}"
        )
    else:
        flight_demand = [0, 0, 0]
    return flight_demand


def get_available_aircraft(
    session_id: str, departure_airport_code: str, target_airport_code: str
):
    available_aircraft_df = pd.DataFrame(columns=AVAILABLE_AIRCRAFT)

    # aircraft details
    route_aircraft_post_data = {
        "city1": departure_airport_code,
        "city2": target_airport_code,
        "addflights": 1,
        "addflights_filter_actype": 0,
        "addflights_filter_hours": 1,
        "glairport": departure_airport_code,
        "qty": 1,
    }
    available_aircraft_req_error = True

    while available_aircraft_req_error:
        # look for available aircraft
        # post data required in order to see all available aircraft
        available_aircraft_req, available_aircraft_req_error, _ = post_request(
            url="http://ae31.airline-empires.com/route_details.php",
            params={
                "city1": route_aircraft_post_data["city1"],
                "city2": route_aircraft_post_data["city2"],
            },
            cookies={"PHPSESSID": session_id},
            data=route_aircraft_post_data,
        )

    available_aircraft_page = BeautifulSoup(available_aircraft_req.text, "html.parser")
    new_flights_page = available_aircraft_page.find("div", {"id": "newflights"})
    available_aircraft_table = new_flights_page.find(
        "td", text="Type"
    ).parent.parent.find_all("tr", recursive=False)[1:]

    for available_aircraft_row in available_aircraft_table:
        reduced_capacity = False

        aircraft_data: list = available_aircraft_row.find_all("td", recursive=False)

        if (
            aircraft_data[0].text
            == "You do not have any aircraft available to serve this route."
        ):
            return

        frequency = aircraft_data[0].find_all("option")[-1:][0].text
        aircraft_id = aircraft_data[1].text
        aircraft_type = aircraft_data[2].text

        try:
            seat_f = int(aircraft_data[3].find_all("td")[-3:-2][0].text.strip(" F"))
        except IndexError:
            seat_f = 0

        try:
            seat_c = int(aircraft_data[3].find_all("td")[-2:-1][0].text.strip(" C"))
        except IndexError:
            seat_c = 0

        try:
            seat_y = int(aircraft_data[3].find_all("td")[-1:][0].text.strip(" Y"))
        except IndexError:
            seat_y = 0

        if aircraft_data[4].find_all("span") != []:
            reduced_capacity = True

        hours = aircraft_data[5].text
        aircraft = pd.Series(
            [
                frequency,
                aircraft_id,
                aircraft_type,
                seat_f,
                seat_c,
                seat_y,
                reduced_capacity,
                hours,
            ],
            index=AVAILABLE_AIRCRAFT,
        )

        available_aircraft_df = pd.concat(
            [available_aircraft_df, aircraft.to_frame().T]
        )

    # type conversion
    available_aircraft_df["frequency"] = available_aircraft_df["frequency"].astype(int)
    available_aircraft_df["seatF"] = available_aircraft_df["seatF"].astype(int)
    available_aircraft_df["seatC"] = available_aircraft_df["seatC"].astype(int)
    available_aircraft_df["seatY"] = available_aircraft_df["seatY"].astype(int)
    available_aircraft_df["hours"] = available_aircraft_df["hours"].astype(int)

    return available_aircraft_df, new_flights_page


def create_flight(
    session_id: str,
    departure_airport_code: str,
    aircraft: str,
    reduced_capacity_flag: bool,
    auto_slot: bool,
    auto_terminal: bool,
    min_frequency: int | None,
    max_frequency: int | None,
    flight: pd.Series,
):
    flight_demand: list[int] = get_flight_demand(
        session_id=session_id,
        flight=flight,
    )

    available_aircraft_df, new_flights_page = get_available_aircraft(
        session_id=session_id,
        departure_airport_code=departure_airport_code,
        target_airport_code=flight["airport"],
    )

    if available_aircraft_df is None:
        return

    # find correct aircraft
    if aircraft == "" or aircraft is None:
        return

    available_aircraft_df = available_aircraft_df.loc[
        available_aircraft_df["type"] == aircraft
    ]
    if available_aircraft_df.empty:
        print("No aircraft of this type available for this route")
        return

    if reduced_capacity_flag is False:
        available_aircraft_df = available_aircraft_df.loc[
            available_aircraft_df["reducedCapacity"] == False
        ]

    if available_aircraft_df.empty:
        print("No aircraft of this type available for this route")
        return

    # find required frequency compared to the demand
    flight_demand_series = pd.Series(
        flight_demand, index=["seatReqF", "seatReqC", "seatReqY"]
    )
    flight_demand_series = flight_demand_series * 7
    available_aircraft_df["seatReqF"] = flight_demand_series["seatReqF"]
    available_aircraft_df["seatReqC"] = flight_demand_series["seatReqC"]
    available_aircraft_df["seatReqY"] = flight_demand_series["seatReqY"]

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

    # get prices and ifs
    flight_info = new_flights_page.find("div", "prices")
    if flight_info is None:
        print("Error in page (no flights displayed / available)")
        return

    flight_info = flight_info.contents[0]
    flight_info_prices = []
    try:
        for all_flight_prices in flight_info.contents[3].findAll("input"):
            flight_info_prices.append(all_flight_prices.attrs["value"])
    except:
        pass

    flight_info_ifs = []
    try:
        for all_flight_ifs in flight_info.contents[4].findAll("option"):
            try:
                all_flight_ifs.attrs["selected"]
                flight_info_ifs.append(all_flight_ifs.attrs["value"])
            except KeyError:
                pass
    except:
        for all_flight_ifs in flight_info.find_all("a"):
            flight_info_ifs.append(all_flight_ifs.attrs["href"].split("id=")[-1:][0])

    # find planes to use
    available_aircraft_df = available_aircraft_df.sort_values("hours")
    if not available_aircraft_df.empty:
        print(available_aircraft_df)

    tot_passenger_y = 0
    tot_frequency = 0
    add_flights_post_data = {
        "city1": departure_airport_code,
        "city2": flight["airport"],
        "addflights": 1,
        "addflights_filter_actype": 0,
        "addflights_filter_hours": 1,
        "price_new_f": flight_info_prices[0],
        "price_new_c": flight_info_prices[1],
        "price_new_y": flight_info_prices[2],
        "ifs_id_f": flight_info_ifs[0],
        "ifs_id_c": flight_info_ifs[1],
        "ifs_id_y": flight_info_ifs[2],
        "confirmaddflights": "Add Flights",
        "glairport": departure_airport_code,
        "qty": 1,
    }
    for _, available_aircraft_row in available_aircraft_df.iterrows():
        min_frequency_check = True
        max_frequency_check = True

        if min_frequency is not None:
            if available_aircraft_row["avgFreq"] < int(min_frequency):
                min_frequency_check = False
                print(
                    f"\t{available_aircraft_row['type']} exceeded min defined frequency. No flights were added"
                )
                if aircraft != "":
                    break

        if max_frequency is not None:
            if available_aircraft_row["avgFreq"] > int(max_frequency):
                max_frequency_check = False
                print(
                    f"\t{available_aircraft_row['type']} exceeded max defined frequency. No flights were added"
                )
                if aircraft != "":
                    break

        if min_frequency_check and max_frequency_check:
            if available_aircraft_row["frequency"] >= available_aircraft_row["avgFreq"]:
                # case when required frequency less than available
                add_flights_post_data["freq_" + available_aircraft_row["aircraft"]] = (
                    available_aircraft_row["avgFreq"]
                )

                # check slots
                origin_slot_available = check_origin_slot(
                    session_id=session_id,
                    autoSlots=auto_slot,
                    autoTerminal=auto_terminal,
                    airport=departure_airport_code,
                )

                target_slot_available = check_target_slot(
                    session_id=session_id,
                    autoSlots=auto_slot,
                    autoTerminal=auto_terminal,
                    airport=flight["airport"],
                    airportSlots=flight["slots"],
                    flightReqSlots=available_aircraft_row["avgFreq"],
                    gatesAvailable=flight["gatesAvailable"],
                )

                if origin_slot_available & target_slot_available:
                    # add flight
                    add_flight(
                        session_id=session_id,
                        city1=departure_airport_code,
                        city2=flight["airport"],
                        addFlightsPostData=add_flights_post_data,
                        frequency=available_aircraft_row["avgFreq"],
                    )
                return
            else:
                if (
                    tot_frequency + available_aircraft_row["frequency"]
                ) > available_aircraft_row["avgFreq"]:
                    # case when enough flights were added
                    add_flights_post_data[
                        "freq_" + available_aircraft_row["aircraft"]
                    ] = available_aircraft_row["avgFreq"] - tot_frequency
                    tot_frequency += available_aircraft_row["avgFreq"] - tot_frequency
                else:
                    # continue adding flights
                    add_flights_post_data[
                        "freq_" + available_aircraft_row["aircraft"]
                    ] = available_aircraft_row["frequency"]
                    tot_frequency += available_aircraft_row["frequency"]
                tot_passenger_y += (
                    available_aircraft_row["seatY"]
                    * available_aircraft_row["frequency"]
                )
                # check if the demand is meat (only checks Economy)
                if tot_passenger_y >= flight_demand_series["seatReqY"]:
                    # check slots, see func
                    origin_slot_available = check_origin_slot(
                        session_id=session_id,
                        autoSlots=auto_slot,
                        autoTerminal=auto_terminal,
                        airport=departure_airport_code,
                    )

                    target_slot_available = check_target_slot(
                        session_id=session_id,
                        autoSlots=auto_slot,
                        autoTerminal=auto_terminal,
                        airport=flight["airport"],
                        airportSlots=flight["slots"],
                        flightReqSlots=available_aircraft_row["avgFreq"],
                        gatesAvailable=flight["gatesAvailable"],
                    )

                    if origin_slot_available & target_slot_available:
                        # add flight
                        add_flight(
                            session_id=session_id,
                            city1=departure_airport_code,
                            city2=flight["airport"],
                            addFlightsPostData=add_flights_post_data,
                            frequency=available_aircraft_row["avgFreq"],
                        )
                    return


def check_origin_slot(session_id: str, autoSlots, autoTerminal, airport):
    mainPageReqError = True
    gateUtilisationReqError = True
    getTerminalsReqError = True
    addTerminalReqError = True
    slotsAvailable = True

    while mainPageReqError:
        mainPageReq, mainPageReqError, _ = get_request(
            url="http://ae31.airline-empires.com/main.php",
            cookies={"PHPSESSID": session_id},
        )
    mainPage = BeautifulSoup(mainPageReq.text, "html.parser")
    airlineDetailsHref = mainPage.find("a", text="Airline Details").attrs["href"]

    while gateUtilisationReqError:
        gateUtilisationReq, gateUtilisationReqError, _ = get_request(
            url=("http://ae31.airline-empires.com/" + airlineDetailsHref),
            cookies={"PHPSESSID": session_id},
        )
    gateUtilisationPage = BeautifulSoup(gateUtilisationReq.text, "lxml")
    # TODO implement part when there is no bought slot from this airport
    gateUtilisationTable = gateUtilisationPage.find(id="airline_airport_list")
    gateTableHeaders = tr_to_list(gateUtilisationTable.find_all("tr")[0].findAll("td"))
    gateTableRowList = []
    for tr in gateUtilisationTable.find_all("tr")[1:]:
        gateTableRow = tr_to_list(tr)
        gateTableRowList.append(dict(zip(gateTableHeaders, gateTableRow)))
    gateUtilisationDf = pd.DataFrame(gateTableRowList)
    gateUtilisationDf = gateUtilisationDf.astype(
        dict(zip(gateTableHeaders, ["str", "str", "int", "str"]))
    )
    gateAmount = (
        gateUtilisationDf.loc[gateUtilisationDf["Code"] == airport]["Gates"] + 5
    )
    gateUtilisation = int(
        gateUtilisationDf.loc[gateUtilisationDf["Code"] == airport]["Utilization"]
        .to_string(index=False)
        .lstrip()
        .split("%")[0]
    )

    # Terminal buying threshold
    if gateUtilisation >= 80:
        slotsAvailable = False
        if autoTerminal == "y":
            while getTerminalsReqError:
                getTerminalReq, getTerminalsReqError, _ = get_request(
                    url="http://ae31.airline-empires.com/termmarket.php",
                    cookies={"PHPSESSID": session_id},
                )
            getTerminalPage = BeautifulSoup(getTerminalReq.text, "html.parser")
            buildTerminalData = {
                "qty": gateAmount,
                "id": airport,
                "price": "0",
                "action": "go",
            }
            while addTerminalReqError:
                _, addTerminalReqError, _ = get_request(
                    url="http://ae31.airline-empires.com/buildterm.php",
                    cookies={"PHPSESSID": session_id},
                    params=buildTerminalData,
                )
            slotsAvailable = True
        else:
            print(
                "Automatically buy termial option is off. Flight may not be created due to slot restrictions!"
            )
    return slotsAvailable


def check_target_slot(
    session_id,
    autoSlots,
    autoTerminal,
    airport,
    airportSlots,
    flightReqSlots,
    gatesAvailable,
):
    addSlotsReqError = True
    getTerminalsReqError = True
    addTerminalReqError = True
    slotsAvailable = True
    try:
        airportSlots = int(airportSlots)
    except TypeError:
        airportSlots = 0
    # check if there is enought slots, else buy some
    # +2 is to force to buy new slots / terminal when its almost full
    # because the termmarket page does not display terminal used at 100%
    # and passing from correct page would require a lot of request
    if airportSlots < (flightReqSlots + 2):
        slotsAvailable = False
        # check if auto slot is on
        if autoSlots is True:
            if gatesAvailable:
                slotsLeaseData = {"quicklease": "Lease 1 {}".format(airport)}
                while addSlotsReqError:
                    _, addSlotsReqError, _ = post_request(
                        url="http://ae31.airline-empires.com/rentgate.php",
                        cookies={"PHPSESSID": session_id},
                        data=slotsLeaseData,
                    )
                slotsAvailable = True
            else:
                if autoTerminal is True:
                    while getTerminalsReqError:
                        getTerminalReq, getTerminalsReqError, _ = get_request(
                            url="http://ae31.airline-empires.com/termmarket.php",
                            cookies={"PHPSESSID": session_id},
                        )
                    getTerminalPage = BeautifulSoup(getTerminalReq.text, "html.parser")
                    # Not safe, redo
                    try:
                        gateAmount = (
                            int(getTerminalPage.find(text=airport).next.next.next) + 5
                        )
                    except AttributeError:
                        gateAmount = 5
                    buildTerminalData = {
                        "qty": gateAmount,
                        "id": airport,
                        "price": "0",
                        "action": "go",
                    }
                    while addTerminalReqError:
                        _, addTerminalReqError, _ = get_request(
                            url="http://ae31.airline-empires.com/buildterm.php",
                            cookies={"PHPSESSID": session_id},
                            params=buildTerminalData,
                        )
                    slotsAvailable = True
                else:
                    print("No slots available, buy terminal instead")
                slotsAvailable = False
    return slotsAvailable


def add_hub(session_id: str, airport: str) -> None:
    add_terminal_req_error = True
    add_hub_req_error = True
    build_terminal_data = {"qty": "5", "id": airport, "price": "0", "action": "go"}
    while add_terminal_req_error:
        _, add_terminal_req_error, _ = get_request(
            url="http://ae31.airline-empires.com/buildterm.php",
            cookies={"PHPSESSID": session_id},
            params=build_terminal_data,
        )

    add_hub_data = {"hub": airport, "hubaction": "Open+Hub"}
    while add_hub_req_error:
        _, add_hub_req_error, _ = get_request(
            url="http://ae31.airline-empires.com/newhub.php",
            cookies={"PHPSESSID": session_id},
            params=add_hub_data,
        )


def add_flight(session_id, city1, city2, addFlightsPostData, frequency):
    addFlightsReqError = True
    while addFlightsReqError:
        _, addFlightsReqError, _ = post_request(
            url="http://ae31.airline-empires.com/route_details.php?city1={}&city2={}".format(
                city1, city2
            ),
            cookies={"PHPSESSID": session_id},
            data=addFlightsPostData,
        )
    print("\tAdded {} flight(s)".format(int(frequency)))


def getRoutes(session_id, startIdx):
    routesCols = [
        "routeId",
        "city1",
        "city2",
        "distance",
        "frequency",
        "loadFactorF",
        "loadFactorC",
        "loadFactorY",
        "priceF",
        "priceC",
        "priceY",
        "profit",
        "details",
    ]
    routesDf = pd.DataFrame(columns=routesCols)

    getRoutesReqError = True
    while getRoutesReqError:
        getRoutesReq, getRoutesReqError, _ = get_request(
            url="http://ae31.airline-empires.com/routes.php?city=all&order=desc&arr_dep=all&next={}".format(
                startIdx
            ),
            cookies={"PHPSESSID": session_id},
        )
    getRoutesPage = BeautifulSoup(getRoutesReq.text, "html.parser")
    routes = getRoutesPage.find_all("form", id="routes")
    for route in routes:
        routeInfos = route.find_all("td")
        routeId = routeInfos[0].find("input").attrs["id"]
        city1 = routeInfos[2].find_all("a")[0].text
        city2 = routeInfos[2].find_all("a")[1].text
        distance = routeInfos[3].text
        frequency = routeInfos[4].text.split("x Weekly")[0]
        try:
            loadFactorF = re.findall(r"\D*(\d+)\D*", routeInfos[5].text)[0]
        except IndexError:
            loadFactorF = np.nan
        try:
            loadFactorC = re.findall(r"\D*(\d+)\D*", routeInfos[6].text)[0]
        except IndexError:
            loadFactorC = np.nan
        try:
            loadFactorY = re.findall(r"\D*(\d+)\D*", routeInfos[7].text)[0]
        except IndexError:
            loadFactorY = np.nan
        try:
            priceF = re.findall(r"\D*(\d+)\D*", routeInfos[8].text)[0]
        except IndexError:
            priceF = np.nan
        try:
            priceC = re.findall(r"\D*(\d+)\D*", routeInfos[9].text)[0]
        except IndexError:
            priceC = np.nan
        try:
            priceY = re.findall(r"\D*(\d+)\D*", routeInfos[10].text)[0]
        except IndexError:
            priceY = np.nan
        profit = re.findall(r"[^-]?(-?\d+)\D*", routeInfos[11].text)[0]
        details = routeInfos[12].find("a").attrs["href"]
        routeSeries = pd.Series(
            [
                routeId,
                city1,
                city2,
                distance,
                frequency,
                loadFactorF,
                loadFactorC,
                loadFactorY,
                priceF,
                priceC,
                priceY,
                profit,
                details,
            ],
            index=routesCols,
        )
        routesDf = pd.concat([routesDf, routeSeries.to_frame().T])
    return routesDf


def closeRoutes(session_id, routesDf):
    closeRoutesData = {
        "checkedroutes[]": [],
        "routeaction": "close",
        "closeroute": "close",
        "massact": "go",
    }
    for _, route in routesDf.iterrows():
        closeRoutesData["checkedroutes[]"].append(route["routeId"])
    closeRoutesReqError = True
    while closeRoutesReqError:
        _, closeRoutesReqError, _ = post_request(
            url="http://ae31.airline-empires.com/routes.php",
            cookies={"PHPSESSID": session_id},
            data=closeRoutesData,
        )
