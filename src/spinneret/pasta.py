"""PASTA (EDI repository) related operations"""
import requests
from lxml import etree
from io import BytesIO
from spinneret.utilities import user_agent


def list_data_package_scopes():
    """List data package scopes

    Returns
    -------
    list
        Data package scopes in the EDI repository
    """
    r = requests.get(
        url="https://pasta.lternet.edu/package/eml",
        headers=user_agent()
    )
    scopes = str.splitlines(r.text)
    return scopes


def list_data_package_identifiers(scope):
    """List data package identifiers

    Parameters
    ----------
    scope : str
        Data package scope

    Returns
    -------
    list
        Data package identifiers of `scope`
    """
    url = 'https://pasta.lternet.edu/package/eml/' + scope
    r = requests.get(url, headers=user_agent())
    identifiers = str.splitlines(r.text)
    return identifiers


def list_data_package_revisions(scope, identifier, filter='newest'):
    """List data package revisions

    Parameters
    ----------
    scope : str
        Data package scope
    identifier : int or str
        Data package identifier
    filter : str
        Filter results by "newest", "oldest", or None.

    Returns
    -------
    list
        Data package revision(s)
    """
    url = 'https://pasta.lternet.edu/package/eml/' + scope + '/' + identifier
    if filter is not None:
        url = url + '?filter=' + filter
    r = requests.get(url, headers=user_agent())
    revisions = str.splitlines(r.text)
    return revisions


def read_metadata(scope, identifier, revision=None, filter='newest'):
    """
    Read EML metadata

    Parameters
    ----------
    scope : str
        Data package scope
    identifier : int or str
        Data package identifier
    revision : int or str
        Data package revision
    filter : str
        Filter results by "newest", "oldest", or None.

    Returns
    -------
    EML metadata
        As an lxml.etree._ElementTree object.
    """
    url = 'https://pasta.lternet.edu/package/metadata/eml/' + scope + '/' + identifier
    if revision is not None:
        url = url + '/' + revision
    if filter is not None:
        url = url + '/' + filter
    r = requests.get(url, headers=user_agent())
    eml = etree.parse(BytesIO(r.content))
    return eml


if __name__ == "__main__":
    meta = read_metadata('edi', '1')
