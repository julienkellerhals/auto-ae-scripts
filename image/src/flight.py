import re

import pandas as pd
from bs4 import BeautifulSoup

from models.flights import Flights
from src.helper import get_request, post_request
from src.meta_data import AVAILABLE_AIRCRAFT, FLIGHTS


def get_flights(session_id: str, search_params: dict):
    list_flights_request_error = True
    slots_regex = r"\((\d*).*\)"
    flights_df = pd.DataFrame(columns=FLIGHTS)

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
            index=FLIGHTS,
        )
        flights_df = pd.concat([flights_df, flight.to_frame().T])
    return list_flights_request, flights_df


def get_flight_demand(session_id: str, flight: Flights) -> tuple[int, int, int]:
    flight_demand_f = 0
    flight_demand_c = 0
    flight_demand_y = 0

    if re.match(r"\w{3}", flight.airport) is not None:
        flight_details_request_error = True
        while flight_details_request_error:
            # flight details
            flight_details_request, flight_details_request_error, _ = get_request(
                url="http://ae31.airline-empires.com/" + flight.flight_url,
                cookies={"PHPSESSID": session_id},
            )

        route_details_page = BeautifulSoup(flight_details_request.text, "html.parser")
        high_charts_script = str(route_details_page.findAll("script")[10])
        raw_data = re.findall(r"data: \[\d*,\d*,\d*\]", high_charts_script)[0]

        flight_demand_f, flight_demand_c, flight_demand_y = [
            int(x) for x in re.findall(r"\d*,\d*,\d*", raw_data)[0].split(",")
        ]

    return flight_demand_f * 7, flight_demand_c * 7, flight_demand_y * 7


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
    auto_slot: bool,
    auto_terminal: bool,
    flight: Flights,
    new_flights_page,
    available_aircraft_df: pd.DataFrame,
) -> Flights:
    # get prices and ifs
    flight_info = new_flights_page.find("div", "prices")
    if flight_info is None:
        print("Error in page (no flights displayed / available)")
        return flight

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
    available_aircraft_df = available_aircraft_df.sort_values("frequency")
    if not available_aircraft_df.empty:
        print(available_aircraft_df)
    else:
        return flight

    if sum(available_aircraft_df["frequency"]) < flight.avg_freq:
        return flight

    add_flights_post_data = create_flight_post_data(
        departure_airport_code=departure_airport_code,
        target_airport=flight.airport,
        flight_info_prices=flight_info_prices,
        flight_info_ifs=flight_info_ifs,
    )

    flight = run_flight_creation(
        available_aircraft_df=available_aircraft_df,
        session_id=session_id,
        flight=flight,
        departure_airport_code=departure_airport_code,
        add_flights_post_data=add_flights_post_data,
    )

    return flight


def create_flight_post_data(
    departure_airport_code: str,
    target_airport: str,
    flight_info_prices: list[int],
    flight_info_ifs: list[int],
) -> dict:
    return {
        "city1": departure_airport_code,
        "city2": target_airport,
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


def run_flight_creation(
    available_aircraft_df: pd.DataFrame,
    session_id: str,
    flight: Flights,
    departure_airport_code: str,
    add_flights_post_data: dict,
    index: int = 0,
    current_freq: int = 0,
) -> Flights:
    current_aircraft = available_aircraft_df.iloc[index]

    if current_aircraft["frequency"] > flight.avg_freq - current_freq:
        # case when required frequency less than available
        add_flights_post_data["freq_" + current_aircraft["aircraft"]] = (
            flight.avg_freq - current_freq
        )

        error_message = add_flight(
            session_id=session_id,
            city1=departure_airport_code,
            city2=flight.airport,
            add_flight_post_data=add_flights_post_data,
        )

        if error_message is None:
            flight.flight_created = True
            return flight

        if error_message == "Not Enough Slots":
            # buy slots
            add_slots_request_error = True
            slots_lease_data = {"quicklease": f"Lease 1 {flight.airport}"}
            while add_slots_request_error:
                _, add_slots_request_error, _ = post_request(
                    url="http://ae31.airline-empires.com/rentgate.php",
                    cookies={"PHPSESSID": session_id},
                    data=slots_lease_data,
                )

            error_message = add_flight(
                session_id=session_id,
                city1=departure_airport_code,
                city2=flight.airport,
                add_flight_post_data=add_flights_post_data,
            )
            if error_message is None:
                flight.flight_created = True
                return flight
    else:
        # case when required frequency less than available
        add_flights_post_data["freq_" + current_aircraft["aircraft"]] = (
            current_aircraft["frequency"]
        )

        run_flight_creation(
            available_aircraft_df=available_aircraft_df,
            session_id=session_id,
            flight=flight,
            departure_airport_code=departure_airport_code,
            add_flights_post_data=add_flights_post_data,
            index=index + 1,
            current_freq=current_aircraft["frequency"] + current_freq,
        )
        return flight

    return flight


def add_flight(
    session_id: str,
    city1: str,
    city2: str,
    add_flight_post_data: dict,
) -> str | None:
    add_flight_request_error = True
    while add_flight_request_error:
        add_flight_response, add_flight_request_error, _ = post_request(
            url=f"http://ae31.airline-empires.com/route_details.php?city1={city1}&city2={city2}",
            cookies={"PHPSESSID": session_id},
            data=add_flight_post_data,
        )
        add_flight_page = BeautifulSoup(add_flight_response.text, "html.parser")

    error_message_container = add_flight_page.find(
        "div", class_="message_failure_withtitle"
    )
    if error_message_container is None:
        return None

    error_message_title = error_message_container.find(
        "div",
        class_="confirmationboxtitle",  # type: ignore
    )
    if error_message_title is None:
        return None

    return error_message_title.text
