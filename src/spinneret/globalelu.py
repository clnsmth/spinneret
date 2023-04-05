"""Get ENVO Classifications from Global Ecological Land Units Lookup"""
import requests
from spinneret.utilities import user_agent
import glob
import os.path
import pickle
from spinneret.eml import get_geographic_coverage


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


def identify(geometry=str, geometry_type=str, map_server=str):
    """
    Run an identify operation on a USGS map service resource and return the
    requested attributes

    For more see: https://rmgsc.cr.usgs.gov/arcgis/sdk/rest/index.html#/Identify_Map_Service/02ss000000m7000000/

    Parameters
    ----------
    geometry : str
        An ESRI geometry in JSON format.
        for more information.
    geometry_type : str
        The `geometryType` parameter corresponding to `geometry`.
    map_server : str
        The map server to query.

    Returns
    -------
    response : dict
        A dictionary of the JSON response from the identify operation.
    """
    base = (
        "https://rmgsc.cr.usgs.gov/arcgis/rest/services/"
        + map_server
        + "/MapServer/identify"
    )
    payload = {
        "f": "json",
        "geometry": geometry,
        "geometryType": geometry_type,
        "tolerance": 2,
        "mapExtent": "-2.865, 47.628, 5.321, 50.017",
        "imageDisplay": "600,550,96"
    }
    r = requests.get(base, params=payload, timeout=5, headers=user_agent())
    return r.json()


def parse_attributes(attributes, json):
    """Parse attributes from JSON response"""
    res = {}
    for a in attributes:
        res[a] = json_extract(json, a)
    return res


def annotate_eml(eml_dir, output_dir):
    """Annotate EML metadata with USGS Global Ecosystem Lookup Service"""
    res = []
    files = glob.glob(eml_dir + '*.xml')
    for file in files:
        geocov = get_geographic_coverage(file)
        if geocov is None:
            continue  # TODO return "no geographic coverage"
        for g in geocov:
            if g._geom_type() == 'envelope' or g._geom_type() == 'polygon':
                continue
            geom = g.to_esri_geometry()
            try:
                r = identify(
                    geometry=geom,
                    geometry_type=g._geom_type(schema='esri'),
                    map_server='wte'
                )
            except Exception as e:
                print(e)
                r = None # TODO return error message for logging
            attributes = parse_attributes(
                attributes=["Landforms", "Landcover", "Climate_Re"],
                json=r
            )
            attributes['packageId'] = os.path.splitext(os.path.basename(file))[0]
            attributes['geographicDescription'] = g.geographicDescription()
            res.append(attributes)
    return res




if __name__ == "__main__":
    res = annotate_eml(
        eml_dir='/Users/csmith/Data/edi/eml/',
        output_dir='/Users/csmith/Data/edi/tests/'
    )
    with open('/Users/csmith/Data/edi/tests/res.pkl', 'wb') as f:
        pickle.dump(res, f)
