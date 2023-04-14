"""Utilities for the spinneret package"""


def user_agent():
    """Define the spinneret user agent in HTTP requests

    For use with the `header` parameter of the requests library.

    Returns
    -------
    dict
        User agent
    """
    header = {"user-agent": "spinneret Python package"}
    return header
