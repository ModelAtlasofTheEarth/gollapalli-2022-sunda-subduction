import requests


def check_uri(uri):

    """
    Checks the availability or validity of a URI by making a HTTP GET request

    Parameters:
    - uri (str): The URI to check.

    Returns:
    'OK' if the request is successful, or an error message if not.
    """

    session = requests.Session()
    TIMEOUT = 10

    try:
        response = session.get(uri, timeout=TIMEOUT)
        response.raise_for_status()
        return "OK"
    except Exception as err:
        return str(err.args[0])
