import re

import pandas as pd
from bs4 import BeautifulSoup

from src.helper import get_request, tr_to_list


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
