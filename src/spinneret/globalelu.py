"""Get ENVO Classifications from Global Ecological Land Units Lookup"""
import glob
import os.path
import pickle
import requests
import pandas as pd
from spinneret.utilities import user_agent
from spinneret.eml import get_geographic_coverage


def _json_extract(obj, key):
    """Recursively fetch values from nested JSON.

    Parameters
    ----------
    obj : dict
        A JSON object
    key : str
        The key to search for

    Returns
    -------
    arr : list
        A list of values for the given key
    """
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
    """Run an identify operation on a USGS map service resource and return the
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

    Examples
    --------
    >>> identify(
    ...     geometry='{"x":-122.5,"y":37.5,"spatialReference":{"wkid":4326}}',
    ...     geometry_type='esriGeometryPoint',
    ...     map_server='wte'
    ... )
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
        "imageDisplay": "600,550,96",
    }
    r = requests.get(base, params=payload, timeout=5, headers=user_agent())
    return r.json()


def parse_attributes(json, attributes):
    """Parse attributes of identify function's response

    Parameters
    ----------
    json : dict
        A dictionary of the JSON response from the identify operation.
    attributes : list
        A list of attributes to extract from the JSON response. These are
        defined in the map service's layer's definition.

    Returns
    -------
    res : dict
        A dictionary of the requested attributes and their values.

    Examples
    --------
    >>> parse_attributes(
    ...     json={
    ...         'displayFieldName': 'NAME',
    ...         'fieldAliases': {
    ...             'OBJECTID': 'OBJECTID',
    ...             'NAME': 'NAME',
    ...             'AREA': 'AREA',
    ...             'PERIMETER': 'PERIMETER',
    ...             'WTE_ID': 'WTE_ID',
    ...             'WTE_NAME': 'WTE_NAME',
    ...             'WTE_TYPE': 'WTE_TYPE',
    ...             'WTE_SUBTYPE': 'WTE_SUBTYPE',
    ...             'WTE_SUBTYPE2': 'WTE_SUBTYPE2'
    ...         },
    ...         'geometryType': 'esriGeometryPolygon',
    ...         'spatialReference': {
    ...             'wkid': 4326,
    ...             'latestWkid': 4326
    ...         }
    ...      },
    ...      attributes=['WTE_NAME', 'WTE_TYPE']
    ... )
    """
    res = {}
    for a in attributes:
        res[a] = _json_extract(json, a)
    return res


def convert_geographic_coverage(eml_dir, output_dir):
    """Convert geographic coverages of EML to WTE ecosystems and write to
    pickle file

    Parameters
    ----------
    eml_dir : str
        Path to directory containing EML files
    output_dir : str
        Path to directory to write output files

    Returns
    -------
    None

    Examples
    --------
    >>> convert_geographic_coverage(
    ...     eml_dir='data/eml/',
    ...     output_dir='data/pkl/'
    ... )
    """
    files = glob.glob(eml_dir + "*.xml")
    for file in files:
        res = []
        print(file)
        pkgid = os.path.splitext(os.path.basename(file))[0]
        geocov = get_geographic_coverage(file)
        if geocov is None:
            continue  # TODO return "no geographic coverage"
        for g in geocov:
            if g.geom_type() == "envelope" or g.geom_type() == "polygon":
                continue
            geom = g.to_esri_geometry()
            try:
                r = identify(
                    geometry=geom,
                    geometry_type=g.geom_type(schema="esri"),
                    map_server="wte",
                )
            except Exception as e:
                print(e)
                r = None  # TODO return error message for logging
            attributes = parse_attributes(
                attributes=["Landforms", "Landcover", "Climate_Re"], json=r
            )
            attributes["packageId"] = pkgid
            attributes["geographicDescription"] = g.geographicDescription()
            res.append(attributes)
        with open(output_dir + pkgid + ".pkl", "wb") as f:
            pickle.dump(res, f)


def combine_pkl_files(pkl_dir, output_dir):
    """Combine pickle files into a single dataframe and write to tsv file

    Parameters
    ----------
    pkl_dir : str
        Path to directory containing pickle files
    output_dir : str
        Path to directory to write output file

    Returns
    -------
    None

    Examples
    --------
    >>> combine_pkl_files(
    ...     pkl_dir='data/pkl/',
    ...     output_dir='data/tsv/'
    ... )
    """
    files = glob.glob(pkl_dir + "*.pkl")
    res = []
    for file in files:
        with open(file, "rb") as f:
            res.append(pickle.load(f))
    res_flat = [
        item for sublist in res for item in sublist
    ]  # FIXME pop() _json_extract() step in parse attributes
    # TODO cleanup code below
    df = pd.DataFrame(res_flat)
    df = df.explode("Landforms")
    df = df.explode("Landcover")
    df = df.explode("Climate_Re")
    # Split packageId on first '.' to get datasetId
    df["datasetId"] = df["packageId"].str.split(".", expand=True)[0]
    df["datasetNum"] = (
        df["packageId"].str.split(".", expand=True)[1]
        + "."
        + df["packageId"].str.split(".", expand=True)[2]
    )
    df["datasetNum"] = df["datasetNum"].astype(float)
    # Sort by datasetId and datasetNum
    df = df.sort_values(by=["datasetId", "datasetNum"])
    # Drop last 3 columns of dataframe
    df = df.iloc[:, :-2]
    # Move packageId to front of dataframe
    cols = df.columns.tolist()
    cols = ["packageId"] + cols[:3] + cols[4:]
    df = df[cols]
    # Write df to tsv
    df.to_csv(output_dir + "globalelu.tsv", sep="\t", index=False)
    return df


def summarize_wte_results(wte_results):
    """Summarize WTE results"""
    df = pd.read_csv(wte_results, sep="\t")
    cols = [
        "packageId",
        "Landforms",
        "Landcover",
        "Climate_Region",
        "geographicDescription",
    ]
    # Summarize gaps in data
    df_not_empty = df[cols].dropna(
        subset=["Landforms", "Landcover", "Climate_Region"]
    )
    total_rows_not_empty = df_not_empty.shape[0]
    total_rows = df.shape[0]
    percent_empty = ((total_rows - total_rows_not_empty) / total_rows) * 100
    print(f"{percent_empty:.2f}% of rows are empty")
    # Summarize by unique combinations of Landforms, Landcover, Climate_Region
    cols_groups = ["Landforms", "Landcover", "Climate_Region"]
    df_not_empty["count"] = 1
    df_grouped = df_not_empty.groupby(cols_groups).count().reset_index()
    df_grouped = df_grouped.sort_values(by="count", ascending=False)
    # Summary plots of the data
    df_not_empty["Landforms"].value_counts().plot(
        kind="bar",
        title="Landforms",
        xlabel="Landforms",
        ylabel="Number of geographic coverages (sampling sites)",
    )
    df_not_empty["Landcover"].value_counts().plot(
        kind="bar",
        title="Landcover",
        xlabel="Landcover",
        ylabel="Number of geographic coverages (sampling sites)",
    )
    df_not_empty["Climate_Region"].value_counts().plot(
        kind="bar",
        title="Climate_Region",
        xlabel="Climate_Region",
        ylabel="Number of geographic coverages (sampling sites)",
    )


if __name__ == "__main__":
    # res = convert_geographic_coverage(
    #     eml_dir='/Users/csmith/Data/edi/eml/',
    #     output_dir='/Users/csmith/Data/edi/tests/'
    # )

    res = combine_pkl_files(
        pkl_dir="/Users/csmith/Data/edi/tests/",
        output_dir="/Users/csmith/Data/edi/"
    )
