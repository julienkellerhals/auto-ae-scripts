import requests
from bs4.element import Tag
from requests.models import Response


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
