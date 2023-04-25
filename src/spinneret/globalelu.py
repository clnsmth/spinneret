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


class Base:
    """A class to manage the data model containing information about the
    dataset, location, and ecosystem."""

    def __init__(self):
        self.data = {
            "dataset": None,
            "location": []
        }

    def set_dataset(self, dataset):
        self.data["dataset"] = dataset

    def add_location(self, location):
        self.data["location"].append(location.data)


class Location:

    def __init__(self):
        self.data = {
            "identifier": None,
            "description": None,
            "geometry_type": None,
            "comments": [],
            "ecosystem": []
        }

    def set_identifier(self, identifier):
        self.data["identifier"] = identifier

    def set_description(self, description):
        self.data["description"] = description

    def set_geometry_type(self, geometry_type):
        self.data["geometry_type"] = geometry_type

    def add_comments(self, comments):
        self.data["comments"].append(comments)

    def add_ecosystem(self, ecosystem):
        self.data["ecosystem"].append(ecosystem.data)


class Ecosystem:

    def __init__(self):
        self.data = {
            "source": None,
            "version": None,
            "comments": [],
            "attributes": None
        }

    def set_source(self, source):
        self.data["source"] = source

    def set_version(self, version):
        self.data["version"] = version

    def add_comments(self, comments):
        self.data["comments"].append(comments)

    def set_attributes(self, response, source):
        if source == 'wte':
            attributes_list = ["Temperatur", "Moisture", "Landcover",
                               "Landforms", "Climate_Re", "ClassName"]
            # TODO Iterate through attributes list and add standard attribute fields

            # TODO define get_annotation(source, sssom) for looking up attribute annotations from sssom
            for attribute in self.data["attributes"].keys():
                self.data["attributes"][attribute]["label"] = response.get_attributes(
                    ["Label"]
                )[0]
                self.data["attributes"][attribute]["annotation"] = response.get_attributes(
                    ["Annotation"]
                )[0]

    def add_attributes(self, attributes):
        # This simply adds the attributes to the ecosystem data model
        pass









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
    # Iterate over EML files (i.e. datasets)
    for file in files:
        file_name = os.path.splitext(os.path.basename(file))[0]
        # Initialize DataModel-base and add the dataset identifier
        base = Base()
        base.set_dataset(file_name)
        # Don't overwrite existing json files unless specified
        if os.path.isfile(os.path.join(output_dir, file_name + ".json")) and not overwrite:
            continue
        print(file)
        # Get metadata for dataset location
        gc = get_geographic_coverage(file)
        if gc is None:  # No geographic coverage (location) found. Continue to next dataset.
            with open(output_dir + file_name + ".json", "w") as f:
                json.dump(res.append(base.data), f)
            continue
        for g in gc:
            # TODO Initialize a new DataModel-location
            # TODO Add location metadata to DataModel-location
            location = Location()
            location.set_description(g.description())
            location.set_geometry_type(g.geom_type())
            if g.geom_type() is not "point":
                location.add_comments("Envelopes and polygons are unsupported at this time.")
                continue
            # Identify the geometry's ecosystem
            if g.geom_type() == "point":
                try:
                    r = identify(
                        geometry=g.to_esri_geometry(),
                        geometry_type=g.geom_type(schema="esri"),
                        map_server="wte",
                    )
                except ConnectionError:
                    r = None
                if r is not None:
                    ecosystem = Ecosystem()
                    ecosystem.set_source("wte")
                    ecosystem.set_attributes(response=r, source="wte")
                    location.add_ecosystem(ecosystem)
                else:
                    continue
        with open(os.path.join(output_dir, file_name + ".json"), "w") as f:
            json.dump(base.data, f)


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
    with open("data/sssom/wte-envo.sssom.tsv", "r") as f:
        sssom = pd.read_csv(f, sep="\t")
    # Load WTE json files from json_dir and add ENVO terms
    files = glob.glob(json_dir + "*.json")
    if not files:
        raise FileNotFoundError("No json files found")
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            wte = json.load(f)
            # Iterate over list of WTE ecosystems
            for w in wte["WTE"][0]["results"]:
                res = {}
                # Landforms
                lf = w["attributes"]["Landforms"]
                if len(lf) > 0:
                    envo_lf = sssom.loc[sssom['subject_label'] == lf, 'object_id'].iloc[0]
                    res["ENVO_Landforms"] = envo_lf
                else:
                    res["ENVO_Landforms"] = lf

                lc = w["attributes"]["Landcover"]
                if len(lc) > 0:
                    envo_lc = sssom.loc[sssom['subject_label'] == lc, 'object_id'].iloc[0]
                    res["ENVO_Landcover"] = envo_lc
                else:
                    res["ENVO_Landcover"] = lc

                mo = w["attributes"]["Moisture"]
                if len(mo) > 0:
                    envo_mo = sssom.loc[sssom['subject_label'] == mo, 'object_id'].iloc[0]
                    res["ENVO_Moisture"] = envo_mo
                else:
                    res["ENVO_Moisture"] = mo

                te = w["attributes"]["Temperatur"]
                if len(te) > 0:
                    envo_te = sssom.loc[sssom['subject_label'] == te, 'object_id'].iloc[0]
                    res["ENVO_Temperatur"] = envo_te
                else:
                    res["ENVO_Temperatur"] = te

                if len(te) > 0 and len(mo) > 0:
                    res["ENVO_Climate_Re"] = envo_te + '|' + envo_mo
                else:
                    res["ENVO_Climate_Re"] = []
                print('42')
                wte["WTE"][0]["results"]






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
            # res.append(json.load(f)['results'])
            j = json.load(f)
            wte = j['WTE'][0]['results']
            res_attr = {}
            if len(wte) > 0: # Not empty
                # Parse wte
                attributes = ["Landforms", "Landcover", "Climate_Re", "Moisture", "Temperatur"]
                for a in attributes:
                    res_attr[a] = _json_extract(wte, a)
            else:
                res_attr = {'Landforms': [], 'Landcover': [], 'Climate_Re': [], 'Moisture': [], 'Temperatur': []}
            # Combine with additional metadata
            edi = j['WTE'][0]['additional_metadata']
            res_attr.update(edi)
            res.append(res_attr)

    # res_flat = [item for sublist in res for item in sublist]
    # Attributes of an identify operation may list multiple values. These
    # values are stored as a list, which need to be unnested into separate
    # rows.
    # df = pd.DataFrame(res_flat)
    df = pd.DataFrame(res)
    df = df.explode("Landforms")
    df = df.explode("Landcover")
    df = df.explode("Climate_Re")
    df = df.explode("Moisture")
    df = df.explode("Temperatur")
    df = df.explode("geographicDescription")
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
            "Moisture",
            "Temperatur",
            "file",
            "geographicDescription",
            "geometry",
            "comments"
        ]
    ]
    # df = df.rename(columns={"Climate_Re": "Climate_Region"})
    # Add "water" to the Landcover column if the comments column contains
    # "Is an aquatic ecosystem."
    df.loc[df["comments"].str.contains("Is an aquatic ecosystem."), "Landcover"] = "water"
    with open("data/sssom/wte-envo.sssom.tsv", "r") as f:
        sssom = pd.read_csv(f, sep="\t")
    # Convert the subject_label column to lowercase
    sssom["subject_label"] = sssom["subject_label"].str.lower()
    # Convert the Landforms column to lowercase
    df["Landforms"] = df["Landforms"].str.lower()
    # Convert the Landcover column to lowercase
    df["Landcover"] = df["Landcover"].str.lower()
    # Convert the Climate_Re column to lowercase
    df["Climate_Re"] = df["Climate_Re"].str.lower()
    # Convert the Moisture column to lowercase
    df["Moisture"] = df["Moisture"].str.lower()
    # Convert the Temperatur column to lowercase
    df["Temperatur"] = df["Temperatur"].str.lower()

    # Match values in the "Landforms" column to ENVO terms using the sssom
    # dataframe.
    df["ENVO_Landforms"] = df["Landforms"].map(sssom.set_index("subject_label")["object_id"])
    # Mach values in the "Landcover" column to ENVO terms using the sssom
    # dataframe.
    df["ENVO_Landcover"] = df["Landcover"].map(sssom.set_index("subject_label")["object_id"])
    # Mach values in the "Moisture" column to ENVO terms using the sssom
    # dataframe.
    df["ENVO_Moisture"] = df["Moisture"].map(sssom.set_index("subject_label")["object_id"])
    # Mach values in the "Temperatur" column to ENVO terms using the sssom
    # dataframe.
    df["ENVO_Temperatur"] = df["Temperatur"].map(sssom.set_index("subject_label")["object_id"])
    # Combine the "ENVO_Moisture" and "ENVO_Temperatur" columns into a single
    # column named "ENVO_Climate_Re" with a pipe (|) delimiter.
    df["ENVO_Climate_Re"] = df["ENVO_Moisture"] + "|" + df["ENVO_Temperatur"]
    # Drop the "ENVO_Moisture" and "ENVO_Temperatur" columns.
    df = df.drop(columns=["ENVO_Moisture", "ENVO_Temperatur", "Moisture", "Temperatur"])
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
    cols_eco = ["Landforms", "Landcover", "Climate_Re"]
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
    res = eml_to_wte_json(
        eml_dir="/Users/csmith/Code/spinneret/src/spinneret/data/eml/",
        output_dir="/Users/csmith/Code/spinneret/src/spinneret/data/json/",
        overwrite=True
    )
    # res = eml_to_wte_json(
    #     eml_dir="/Users/csmith/Data/edi/eml/",
    #     output_dir="/Users/csmith/Data/edi/json/",
    #     overwrite=False
    # )

    # # Add ENVO terms to WTE json files
    # add_envo(
    #     json_dir="data/json/",
    #     output_dir="spinneret/data/json_envo/"
    # )

    # # Combine json files into a single dataframe
    # df = wte_json_to_df(json_dir="/Users/csmith/Data/edi/json/")
    # # print(df)

    # # Write df to tsv
    # output_dir = "/Users/csmith/Data/edi/"
    # df.to_csv(output_dir + "globalelu.tsv", sep="\t", index=False)

    # # Summarize WTE results
    # res = summarize_wte_results(df)
    # print(res)
