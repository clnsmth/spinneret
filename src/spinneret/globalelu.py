"""Get ENVO Classifications from Global Ecological Land Units Lookup"""
import glob
import os.path
import json
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


class Response:
    """A class to parse the response from the identify operation

    Parameters
    ----------
    json : dict
        A dictionary of the JSON response from the identify operation.
    """

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

    def get_comments(self):
        """List of comments about the response

        Returns
        -------
        comments : str
            A string of comments about the response.
        """
        pv = _json_extract(self.json, "Pixel Value")
        if len(pv) == 0:  # pv == []
            return "Is unknown ecosystem (outside the WTE area)."
        if len(pv) > 0 and pv[0] == "NoData":
            return "Is an aquatic ecosystem."
        return "Is a terrestrial ecosystem."


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
    r = requests.get(base, params=payload, timeout=10, headers=user_agent())
    return Response(r.json())


def eml_to_wte_json(eml_dir, output_dir, overwrite=False):
    """Convert geographic coverages of EML to WTE ecosystems and write to
    json file

    Parameters
    ----------
    eml_dir : str
        Path to directory containing EML files
    output_dir : str
        Path to directory to write output files
    overwrite : bool, optional
        Overwrite existing json files, by default False

    Returns
    -------
    None

    Notes
    -----
    An empty json file indicates no geographic coverage was found. The
    presence of a json file in the `output_dir` indicates the input file was
    processed.

    Examples
    --------
    # >>> eml_to_wte_json(
    # ...     eml_dir='data/eml/',
    # ...     output_dir='data/json/'
    # ... )
    """
    files = glob.glob(eml_dir + "*.xml")
    if not files:
        raise FileNotFoundError("No EML files found")
    # List EML files without matching json files
    files = [
        f
        for f in files
        if not os.path.isfile(os.path.join(output_dir, os.path.splitext(os.path.basename(f))[0] + ".json"))
    ]

    for file in files:
        res = []
        print(file)
        fname = os.path.splitext(os.path.basename(file))[0]
        if os.path.isfile(os.path.join(output_dir, fname + ".json")) and not overwrite:
            continue
        gc = get_geographic_coverage(file)
        if gc is None:  # No geographic coverage found
            a = {}
            # a["Landforms"] = []
            # a["Landcover"] = []
            # a["Climate_Re"] = []
            results = [
                {"attributes": {
                    "Landforms": [],
                    "Landcover": [],
                    "Climate_Re": [],
                    "Moisture": [],
                    "Temperatur": []
                }
                }
            ]
            a["file"] = fname
            a["geometry"] = []
            a["geographicDescription"] = []
            a["comments"] = "No geographic coverage found"
            res.append({"results": results, "additional_metadata": a})
            with open(output_dir + fname + ".json", "w") as f:
                json.dump({'WTE': res}, f)
            continue
        for g in gc:
            if g.geom_type() == "point":  # Geographic coverage is a point
                try:
                    r = identify(
                        geometry=g.to_esri_geometry(),
                        geometry_type=g.geom_type(schema="esri"),
                        map_server="wte",
                    )
                except ConnectionError:
                    r = None
                if r is not None:
                    # a = r.get_attributes( # TODO move to subsequent step (df)
                    #     attributes=["Landforms", "Landcover", "Climate_Re"]
                    # )
                    a = {}
                    a["file"] = fname
                    a["geometry"] = g.geom_type()
                    a["geographicDescription"] = g.description()
                    a["comments"] = r.get_comments()  # TODO apply this method in a subsequent step

                    res.append({"results": r.json['results'], "additional_metadata": a})
                else:
                    continue
            else:  # Geographic coverage is an envelope or polygon
                a = {}
                results = [
                    {"attributes": {
                        "Landforms": [],
                        "Landcover": [],
                        "Climate_Re": [],
                        "Moisture": [],
                        "Temperatur": []
                    }
                    }
                ]
                # a["Landforms"] = []
                # a["Landcover"] = []
                # a["Climate_Re"] = []
                a["file"] = fname
                a["geometry"] = g.geom_type()
                a["geographicDescription"] = g.description()
                a["comments"] = "Envelopes and polygons are not supported"
                res.append({"results": results, "additional_metadata": a})
        with open(os.path.join(output_dir, fname + ".json"), "w") as f:
            json.dump({'WTE': res}, f)


def add_envo(json_dir, output_dir):
    """Add ENVO terms to WTE json files

    Parameters
    ----------
    json_dir : str
        Path to directory containing WTE json files
    output_dir : str
        Path to directory to write output files

    Returns
    -------
    None
    """
    # Load WTE to ENVO mapping
    with open("src/spinneret/data/sssom/wte_to_envo.sssom.tsv", "r") as f:
        sssom = pd.read_csv(f, sep="\t")
    # Load WTE json files from json_dir and add ENVO terms
    files = glob.glob(json_dir + "*.json")
    if not files:
        raise FileNotFoundError("No json files found")
    for file in files:
        res = {}
        with open(file, "r", encoding="utf-8") as f:
            wte = json.load(f)['WTE']
            # Iterate over list of WTE ecosystems
            # Get Landforms, Landcover, Moisture, and Temperatur attributes
            res["ENVO_Landforms"] = []
            res["ENVO_Landcover"] = []
            res["ENVO_Moisture"] = []
            res["ENVO_Temperatur"] = []




def wte_json_to_df(json_dir):
    """Combine WTE json files into a single dataframe

    Parameters
    ----------
    json_dir : str
        Path to directory containing json files

    Returns
    -------
    df : pandas.DataFrame
        A dataframe of the WTE ecosystems

    Examples
    --------
    # >>> df = wte_json_to_wte_df(json_dir='data/json/')
    """
    files = glob.glob(json_dir + "*.json")
    if not files:
        raise FileNotFoundError("No json files found")
    res = []
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            res.append(json.load(f)['results'])
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
    df = df[
        [
            "Landforms",
            "Landcover",
            "Climate_Re",
            "file",
            "geographicDescription",
            "comments",
        ]
    ]
    df = df.rename(columns={"Climate_Re": "Climate_Region"})
    return df


def summarize_wte_results(wte_df):
    """Summarize WTE results

    Parameters
    ----------
    wte_df : pandas.DataFrame
        A dataframe of the WTE ecosystems created by `wte_json_to_df`

    Returns
    -------
    res : dict
        A dictionary of the WTE results

    Examples
    --------
    # >>> df = globalelu.wte_json_to_df(json_dir="src/spinneret/data/json/")
    # >>> res = summarize_wte_results(df)
    """
    res = {}
    cols = wte_df.columns.tolist()
    cols_eco = ["Landforms", "Landcover", "Climate_Region"]
    # Match success rate of the identify operation
    df = wte_df[cols].dropna(subset=cols_eco)
    res["Successful matches (percent)"] = (df.shape[0] / wte_df.shape[0]) * 100
    other_metrics = {
        "Terrestrial ecosystems (number)": "Is a terrestrial ecosystem.",
        "Aquatic ecosystems (number)": "Is an aquatic ecosystem.",
        "Unsupported geometries (number)": "Envelopes and polygons are not supported",
        "Out of bounds geometries (number)": "Is unknown ecosystem (outside the WTE area).",
        "No geographic coverage (number)": "No geographic coverage found",
    }
    for key, value in other_metrics.items():
        i = wte_df["comments"] == value
        res[key] = wte_df[i].shape[0]

    # List the number of aquatic ecosystems
    # i = wte_df["comments"] == "Is an aquatic ecosystem."
    # res["aquatic_ecosystem"] = wte_df[i].shape[0]
    # # List the number of unknown ecosystems
    # i = wte_df["comments"] == "Is unknown ecosystem (outside the WTE area)."
    # res["out_of_bounds"] = wte_df[i].shape[0]
    # # List the number of terrestrial ecosystems
    # i = wte_df["comments"] == "Is a terrestrial ecosystem."
    # res["terrestrial_ecosystem"] = wte_df[i].shape[0]
    # # List the number of no geographic coverage found
    # i = wte_df["comments"] == "No geographic coverage found"
    # res["no_geographic_coverage"] = wte_df[i].shape[0]
    # List the number of unsupported geometries
    # i = wte_df["comments"] == "Envelopes and polygons are not supported"
    # res["unsupported_geometry"] = wte_df[i].shape[0]
    # Summarize by unique combinations of Landforms, Landcover, Climate_Region
    for col in cols_eco:
        df["count"] = 1
        df_grouped = df.groupby(col).count().reset_index()
        df_grouped = df_grouped.sort_values(by="count", ascending=False)
        res[col] = df_grouped.set_index(col).to_dict()["count"]
    return res


if __name__ == "__main__":

    print("42")

    # Transform EML to WTE ecosystems and write to json file
    # res = eml_to_wte_json(
    #     eml_dir="/Users/csmith/Code/spinneret/src/spinneret/data/eml/",
    #     output_dir="/Users/csmith/Code/spinneret/src/spinneret/data/json/",
    #     overwrite=True
    # )
    res = eml_to_wte_json(
        eml_dir="/Users/csmith/Data/edi/eml/",
        output_dir="/Users/csmith/Data/edi/json/",
        overwrite=True
    )

    # # Add ENVO terms to WTE json files
    # add_envo(
    #     json_dir="/Users/csmith/Code/spinneret/src/spinneret/data/json/",
    #     output_dir="/Users/csmith/Code/spinneret/src/spinneret/data/json_envo/"
    # )

    # # Combine json files into a single dataframe
    # df = wte_json_to_df(json_dir="data/json/")
    # print(df)

    # Write df to tsv
    # df.to_csv(output_dir + "globalelu.tsv", sep="\t", index=False)
