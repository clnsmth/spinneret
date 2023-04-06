"""Get ENVO Classifications from Global Ecological Land Units Lookup"""
import requests
from spinneret.utilities import user_agent
import glob
import os.path
import pickle
from spinneret.eml import get_geographic_coverage
import pandas as pd


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


def convert_geographic_coverage(eml_dir, output_dir):
    """Convert EML geographicCoverage to ecosystem with USGS Global Ecosystem
    Lookup Service"""
    files = glob.glob(eml_dir + '*.xml')
    for file in files:
        res = []
        print(file)
        pkgid = os.path.splitext(os.path.basename(file))[0]
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
            attributes['packageId'] = pkgid
            attributes['geographicDescription'] = g.geographicDescription()
            res.append(attributes)
        with open(output_dir + pkgid + '.pkl', 'wb') as f:
            pickle.dump(res, f)
    return None


def combine_pkl_files(pkl_dir, output_dir):
    """Combine pickle files into into a single dataframe"""
    files = glob.glob(pkl_dir + '*.pkl')
    res = []
    for file in files:
        with open(file, 'rb') as f:
            res.append(pickle.load(f))
    res_flat = [item for sublist in res for item in sublist] # FIXME pop() json_extract() step in parse attributes
    # TODO cleanup code below
    df = pd.DataFrame(res_flat)
    df = df.explode('Landforms')
    df = df.explode('Landcover')
    df = df.explode('Climate_Re')
    # Split packageId on first '.' to get datasetId
    df['datasetId'] = df['packageId'].str.split('.', expand=True)[0]
    df['datasetNum'] = df['packageId'].str.split('.', expand=True)[1] + '.' + df['packageId'].str.split('.', expand=True)[2]
    df['datasetNum'] = df['datasetNum'].astype(float)
    # Sort by datasetId and datasetNum
    df = df.sort_values(by=['datasetId', 'datasetNum'])
    # Drop last 3 columns of dataframe
    df = df.iloc[:, :-2]
    # Move packageId to front of dataframe
    cols = df.columns.tolist()
    cols = ['packageId'] + cols[:3] + cols[4:]
    df = df[cols]
    # Write df to tsv
    df.to_csv(output_dir + 'globalelu.tsv', sep='\t', index=False)
    return df




if __name__ == "__main__":
    # res = convert_geographic_coverage(
    #     eml_dir='/Users/csmith/Data/edi/eml/',
    #     output_dir='/Users/csmith/Data/edi/tests/'
    # )

    res = combine_pkl_files(
        pkl_dir='/Users/csmith/Data/edi/tests/',
        output_dir='/Users/csmith/Data/edi/'
    )
