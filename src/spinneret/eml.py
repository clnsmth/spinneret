"""Get ENVO Classifications from Global Ecological Land Units Lookup"""
import requests


def json_extract(obj, key):
    """Recursively fetch values from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values


def identify(geometry=str, map_server=str, attributes=list):
    """
    Run an identify operation on a USGS map service resource and return the
    requested attributes

    For more see: https://rmgsc.cr.usgs.gov/arcgis/sdk/rest/index.html#/Identify_Map_Service/02ss000000m7000000/

    Parameters
    ----------
    geometry
    map_server
    attributes

    Returns
    -------

    """
    base = (
        "https://rmgsc.cr.usgs.gov/arcgis/rest/services/"
        + map_server
        + "/MapServer/identify"
    )
    payload = {
        "f": "json",
        "geometry": geometry,
        "geometryType": "esriGeometryPoint",
        "tolerance": 2,
        "mapExtent": "-2.865, 47.628, 5.321, 50.017",
        "imageDisplay": "600,550,96",
    }
    r = requests.get(base, params=payload, timeout=5)
    res = []
    for attribute in attributes:
        names = json_extract(r.json(), attribute)
        res.append(names.pop())
    # TODO Get SSSOM
    # TODO Table lookup
    return res


if __name__ == "__main__":
    res = identify(
        geometry="-1.361,49.004",
        map_server="wte",
        attributes=["Landforms", "Landcover", "Climate_Re"],
    )
    print(res)
