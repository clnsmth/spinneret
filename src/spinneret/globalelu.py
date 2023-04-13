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

    # TODO Return none if the key is absent
    values = extract(obj, arr, key)
    return values


class Response:

    def __init__(self, json):
        self.json = json

    def get_attributes(self, attributes):
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

        """
        res = {}
        for a in attributes:
            res[a] = _json_extract(self.json, a)
        return res


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
    # >>> identify(
    # ...     geometry='{"x":-122.5,"y":37.5,"spatialReference":{"wkid":4326}}',
    # ...     geometry_type='esriGeometryPoint',
    # ...     map_server='wte'
    # ... )
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
    return Response(r.json())


def eml_to_wte_pkl(eml_dir, output_dir):
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

    Notes
    -----
    An empty pickle file indicates no geographic coverage was found. The
    presence of a pickle file in the `output_dir` indicates the input file was
    processed.

    Examples
    --------
    # >>> eml_to_wte_pkl(
    # ...     eml_dir='data/eml/',
    # ...     output_dir='data/pkl/'
    # ... )
    """
    files = glob.glob(eml_dir + "*.xml")
    for file in files:
        res = []
        print(file)
        fname = os.path.splitext(os.path.basename(file))[0]
        gc = get_geographic_coverage(file)
        if gc is None:
            with open(output_dir + fname + ".pkl", "wb") as f:
                pickle.dump(res, f)
        for g in gc:
            if g.geom_type() == "envelope" or g.geom_type() == "polygon":
                # TODO This block of code can be removed once support is added
                #  for polygons and envelopes.
                with open(output_dir + fname + ".pkl", "wb") as f:
                    pickle.dump(res, f)
            try:
                r = identify(
                    geometry=g.to_esri_geometry(),
                    geometry_type=g.geom_type(schema="esri"),
                    map_server="wte"
                )
            except Exception as e:
                print(e)
                r = None
            # TODO Get water attributes
            a = r.get_attributes(
                attributes=["Landforms", "Landcover", "Climate_Re"]
            )
            a["file"] = fname
            a["geographicDescription"] = g.description()
            res.append(a)
        with open(os.path.join(output_dir, fname + ".pkl"), "wb") as f:
            pickle.dump(res, f)


def wte_pkl_to_df(pkl_dir):
    """Combine WTE pickle files into a single dataframe

    Parameters
    ----------
    pkl_dir : str
        Path to directory containing pickle files

    Returns
    -------
    df : pandas.DataFrame
        A dataframe of the WTE ecosystems

    Examples
    --------
    # >>> df = wte_pkl_to_wte_df(pkl_dir='data/pkl/')
    """
    files = glob.glob(pkl_dir + "*.pkl")
    res = []
    for file in files:
        with open(file, "rb") as f:
            res.append(pickle.load(f))
    res_flat = [item for sublist in res for item in sublist]
    # Attributes of an identify operation may list multiple values. These
    # values are stored as a list, which need to be unnested into separate
    # rows.
    df = pd.DataFrame(res_flat)
    df = df.explode("Landforms")
    df = df.explode("Landcover")
    df = df.explode("Climate_Re")
    # Sorting datasets by a packageId's scope and identifier is provides an
    # intuitive ordering for browsing by information managers.
    df["scope"] = df["file"].str.split(".", expand=True)[0]
    df["identifier"] = (
        df["file"].str.split(".", expand=True)[1]
        + "."
        + df["file"].str.split(".", expand=True)[2]
    )
    df["identifier"] = df["identifier"].astype(float)
    df = df.sort_values(by=["scope", "identifier"])
    df = df[["Landforms", "Landcover", "Climate_Re", "file", "geographicDescription"]]
    df = df.rename(columns={"Climate_Re": "Climate_Region"})
    return df


def summarize_wte_results(wte_df):
    """Summarize WTE results

    Parameters
    ----------
    wte_df : pandas.DataFrame
        A dataframe of the WTE ecosystems created by `wte_pkl_to_df`

    Returns
    -------
    res : dict
        A dictionary of the WTE results

    Examples
    --------
    # >>> df = globalelu.wte_pkl_to_df(pkl_dir="src/spinneret/data/pkl/")
    # >>> res = summarize_wte_results(df)
    """
    res = {}
    cols = wte_df.columns.tolist()
    cols_eco = ["Landforms", "Landcover", "Climate_Region"]
    # Characterize success rate of the identify operation
    df = wte_df[cols].dropna(subset=cols_eco)
    res["percent_success"] = (df.shape[0] / wte_df.shape[0]) * 100
    # Summarize by unique combinations of Landforms, Landcover, Climate_Region
    for col in cols_eco:
        df["count"] = 1
        df_grouped = df.groupby(col).count().reset_index()
        df_grouped = df_grouped.sort_values(by="count", ascending=False)
        res[col] = df_grouped.set_index(col).to_dict()["count"]
    return res






if __name__ == "__main__":

    print('42')

    # Run identify() on all EML files in eml_dir and write to pickle files
    # res = eml_to_wte_pkl(
    #     eml_dir="/Users/csmith/Data/edi/eml/",
    #     output_dir="/Users/csmith/Data/edi/pkl/"
    # )

    # # Combine pickle files into a single dataframe and write to tsv file
    # df = wte_pkl_to_df(
    #     pkl_dir="/Users/csmith/Data/edi/tests/",
    #     output_dir="/Users/csmith/Data/edi/"
    # )

    # Write df to tsv
    # df.to_csv(output_dir + "globalelu.tsv", sep="\t", index=False)
