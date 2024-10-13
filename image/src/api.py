import re
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from src.helper import get_request, post_request, tr_to_list


if TYPE_CHECKING:
    pass


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
                "Automatically buy terminal option is off. Flight may not be created due to slot restrictions!"
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
    # check if there is enough slots, else buy some
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
