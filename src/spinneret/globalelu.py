"""Get ENVO Classifications from Global Ecological Land Units Lookup"""
import glob
import os.path
import json
import requests
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
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
        self.data = {"dataset": None, "location": []}

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
            "ecosystem": [],
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
            "attributes": None,
        }

    def set_source(self, source):
        self.data["source"] = source

    def set_version(self, version):
        self.data["version"] = version

    def add_comments(self, comments):
        self.data["comments"].append(comments)

    def add_attributes(self, attributes):
        self.data["attributes"] = attributes.data


class Attributes:
    def __init__(self, source):
        if source == "wte":
            self.data = {
                "Temperatur": {"label": None, "annotation": None},
                "Moisture": {"label": None, "annotation": None},
                "Landcover": {"label": None, "annotation": None},
                "Landforms": {"label": None, "annotation": None},
                "Climate_Re": {"label": None, "annotation": None},
                "ClassName": {"label": None, "annotation": None},
            }
        elif source == "ecu":
            self.data = {
                "Slope": {"label": None, "annotation": None},
                "Sinuosity": {"label": None, "annotation": None},
                "Erodibility": {"label": None, "annotation": None},
                "Temperature and Moisture Regime": {"label": None, "annotation": None},
                "River Discharge": {"label": None, "annotation": None},
                "Wave Height": {"label": None, "annotation": None},
                "Tidal Range": {"label": None, "annotation": None},
                "Marine Physical Environment": {"label": None, "annotation": None},
                "Turbidity": {"label": None, "annotation": None},
                "Chlorophyll": {"label": None, "annotation": None},
                "CSU_Descriptor": {"label": None, "annotation": None}
            }

    def set_attributes(self, response, source):
        attributes = Attributes(source=source)
        if source == "wte":
            attributes.set_wte_attributes(response)
            self.data = attributes.data
        elif source == "ecu":
            attributes.set_ecu_attributes(response)
            self.data = attributes.data

    @staticmethod
    def get_annotation(label, source):
        if source == "wte":
            with open(
                    "src/spinneret/data/sssom/wte-envo.sssom.tsv",
                    mode="r",
                    encoding="utf-8"
            ) as f:
                sssom = pd.read_csv(f, sep="\t")
            sssom["subject_label"] = sssom["subject_label"].str.lower()
        elif source == "ecu":
            return "Placeholder"  # TODO - add ECU sssom and parse
        res = sssom.loc[
            sssom["subject_label"] == label.lower(),
            "object_id"
        ].values[0]
        return res

    def set_wte_attributes(self, response):
        for attribute in self.data.keys():
            label = response.get_attributes([attribute])[attribute][0]
            if attribute == "Climate_Re":
                # Climate_Re is a composite class composed of Temperatur
                # and Moisture classes.
                annotation = (
                    "("
                    + self.data["Temperatur"].get("annotation")
                    + "|"
                    + self.data["Moisture"].get("annotation")
                    + ")"
                )
                self.data[attribute] = {
                    "label": label,
                    "annotation": annotation
                }
            elif attribute == "ClassName":
                # ClassName is a composite class composed of Temperatur,
                # Moisture, Landcover, and Landforms classes.
                annotation = (
                    "("
                    + self.data["Temperatur"].get("annotation")
                    + "|"
                    + self.data["Moisture"].get("annotation")
                    + ")"
                    + "|"
                    + self.data["Landcover"].get("annotation")
                    + "|"
                    + self.data["Landforms"].get("annotation")
                )
                self.data[attribute] = {
                    "label": label,
                    "annotation": annotation
                }
            else:
                # All other classes are single classes, which resolve to
                # terms listed in the SSSOM file, and which compose the
                # composite classes of Climate_Re and ClassName.
                self.data[attribute] = {
                    "label": label,
                    "annotation": self.get_annotation(label, source="wte"),
                }
        self.data = self.data


    def set_ecu_attributes(self, unique_ecosystem_attributes):
        # There is only one attribute for ECU, CSU_Descriptor, which is
        # composed of 10 atomic attributes.
        descriptors = unique_ecosystem_attributes
        # Atomize: Split on commas and remove whitespace
        descriptors = descriptors.split(",")
        descriptors = [g.strip() for g in descriptors]
        atomic_attribute_labels = self.data.keys()
        # Zip descriptors and atomic attribute labels
        ecosystems = [dict(zip(atomic_attribute_labels, descriptors))]
        # Iterate over atomic attributes and set labels and annotations
        ecosystem = ecosystems[0]
        # attributes = {}
        # self.data
        for attribute in ecosystem.keys():
            label = ecosystem.get(attribute)
            self.data[attribute] = {
                "label": label,
                "annotation": self.get_annotation(label, source="ecu"),
            }
        # Add composite CSU_Description class and annotation.
        # Get ecosystems values and join with commas
        # TODO Fix issue where an attribute from the initialized list returned by
        #  Attributes() was missing for some reason and thus an annotation couldn't
        #  be found for it. If arbitrary joining of empties to the annotation string
        #  is done, then the annotation may be wrong. Best to just leave it out.
        CSU_Descriptor = [f.get("label") for f in self.data.values()]
        # Knock of the last one, which is CSU_Descriptor
        CSU_Descriptor = CSU_Descriptor[:-1]
        CSU_Descriptor = ", ".join(CSU_Descriptor)
        CSU_Descriptor_annotation = [f.get("annotation") for f in self.data.values()]
        # Knock of the last one, which is CSU_Descriptor
        CSU_Descriptor_annotation = CSU_Descriptor_annotation[:-1]
        CSU_Descriptor_annotation = "|".join(CSU_Descriptor_annotation)
        self.data["CSU_Descriptor"] = {
            "label": CSU_Descriptor,
            "annotation": CSU_Descriptor_annotation
        }
        # Append to results
        self.data = self.data


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
        """Recursively get attributes of a response from an identify or query
        opperation.

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
        # TODO Get attributes/features by source? This would simplify the
        #  methods calls, unless this functionality is needed elsewhere (e.g.
        #  getting other names from response dictionaries).
        res = {}
        for a in attributes:
            res[a] = _json_extract(self.json, a)
        return res

    def get_comments(self, source):
        """List of comments about the response

        Returns
        -------
        comments : str
            A string of comments about the response.
        None if no comments are found.
        """
        if source == "wte":
            pv = _json_extract(self.json, "Pixel Value")
            if len(pv) == 0:
                return "WTE: Location is out of bounds."
            if len(pv) > 0 and pv[0] == "NoData":
                return "WTE: Location is an area of water."
            return "WTE: Location is a terrestrial ecosystem."
        return None

    def has_ecosystem(self, source):
        if source == "wte":
            res = _json_extract(self.json, "Pixel Value")
            if len(res) == 0:
                return False
            if len(res) > 0 and res[0] == "NoData":
                return False
            return True
        elif source == "ecu":
            res = len(self.json["features"])
            if res == 0:
                return False
            if res > 0:
                return True
        return None

    def get_unique_ecosystems(self, source):
        # TODO Note this paralells get_attributes() in some ways. May want to
        #  rename this function after that one. They serve slightly different
        #  purposes. The current name of this function is a bit misleading.
        #  A better name may be create_ecosystem_attribute_iterable().
        if source == 'wte':
            pass
        if source == 'ecu':
            attribute = "CSU_Descriptor"
            descriptors = self.get_attributes([attribute])[attribute]
            descriptors = set(descriptors)
            return descriptors



def identify(geometry=str, geometry_type=str, map_server=str):
    """Run an identify operation on a USGS map service resource and return the
    requested attributes

    For more see: https://rmgsc.cr.usgs.gov/arcgis/sdk/rest/index.html#/Identify_Map_Service/02ss000000m7000000/

    Parameters
    ----------
    geometry : str
        An ESRI geometry in JSON format.
    geometry_type : str
        The `geometryType` parameter corresponding to `geometry`.
    map_server : str
        The map server to query. Options are `wte`.

    Returns
    -------
    Response

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


def query(geometry=str, geometry_type=str, map_server=str):
    """Run a query operation on a USGS map service resource and return the
    requested attributes

    For more see: https://rmgsc.cr.usgs.gov/arcgis/sdk/rest/index.html#//02ss0000000r000000

    Parameters
    ----------
    geometry : str
        An ESRI geometry in JSON format.
    geometry_type : str
        The `geometryType` parameter corresponding to `geometry`.
    map_server : str
        The map server to query. Options are `ecu`.

    Returns
    -------
    Response
    """
    # Convert "ecu" to query parameters. The "ecu" abstraction is used to
    # align the UX with usage of "wte".
    if map_server == "ecu":
        layer = "0"
        map_server = "gceVector"
        # Convert point geometries to envelopes. This is necessary because
        # the query map service does not support point geometries.
        # TODO Move this block out a level to operate on all map servers?
        if geometry_type == "esriGeometryPoint" or geometry_type == "point":
            # A buffer radius of 0.5 km should gaurantee overlap of coastal
            # sampling locations, represented by point geometries, and location
            # of ECUs. This is a conservative estimate of the spatial
            # accuracy between the point location and nearby ECUs.
            geometry = convert_point_to_envelope(geometry, buffer=0.5)
            geometry_type = "esriGeometryEnvelope"
    base = (
        "https://rmgsc.cr.usgs.gov/arcgis/rest/services/" +
        map_server +
        "/MapServer/" +
        layer +
        "/query"
    )
    payload = {
        "f": "geojson",
        "geometry": geometry,
        "geometryType": geometry_type,
        "where": "1=1",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "false",
        "returnTrueCurves": "false",
        "returnIdsOnly": "false",
        "returnCountOnly": "false",
        "returnZ": "false",
        "returnM": "false",
        "returnDistinctValues": "true",
        "returnExtentOnly": "false"
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
        output_file_path = os.path.join(output_dir, file_name + ".json")
        # Initialize the DataModel Base object, which forms the basis of the
        # return object
        base = Base()
        base.set_dataset(file_name)
        # Don't overwrite existing json files unless specified
        if os.path.isfile(output_file_path) and not overwrite:
            continue
        print(file)
        # Get metadata for dataset location
        gc = get_geographic_coverage(file)
        if gc is None:  # No geographic coverage (location) found
            with open(output_file_path, "w", encoding='utf-8') as f:
                json.dump(base.data, f)
            continue
        for g in gc:
            # Build a location object for each geographic coverage and add it
            # to the base object
            location = Location()
            location.set_description(g.description())
            location.set_geometry_type(g.geom_type())
            if g.geom_type() != "point":
                location.add_comments(
                    "Envelopes and polygons are unsupported at this time."
                )
                base.add_location(location)
                continue
            # Identify the ecosystem(s) at the location.
            # TODO Query all map servers with the same geometry, and append
            #  results to the location object.

            # TODO Wrap the code below into a single function
            # Start of get_ecosystem("wte") ----------------------------------
            # Inputs are the geometry and geometry type and location object
            if g.geom_type() == "point":
                location.add_comments("WTE: Was queried.")
                try:
                    r = identify(
                        geometry=g.to_esri_geometry(),
                        geometry_type=g.geom_type(schema="esri"),
                        map_server="wte",
                    )
                except ConnectionError:
                    r = None
                # TODO Iterate over ecosystems in response and returns a list
                #  of ecosystems.
                #  The resultant list of ecosystems should be appended to the
                #  location via add_ecosystem().
                # TODO Convert response to iterable. Deduplicate ecosystems
                #  then iterate over the list to build ecosystem objects.
                if r is not None:
                    # Build the ecosystem object and add it to the location. If
                    # the location could not be resolved, or has no ecosystems,
                    # add an explanatory comment to the location object to
                    # facilitate understanding and analysis.
                    if not r.has_ecosystem(source="wte"):
                        location.add_comments(r.get_comments("wte"))
                        base.add_location(location)
                        continue
                    ecosystem = Ecosystem()
                    ecosystem.set_source("wte")
                    ecosystem.set_version(None)
                    attributes = Attributes(source="wte")
                    attributes.set_attributes(response=r, source="wte")
                    ecosystem.add_attributes(attributes)
                    location.add_ecosystem(ecosystem)
                else:
                    continue
            # End of get_ecosystem("wte") ------------------------------------

            # TODO Wrap the code below into a single function
            # Start of get_ecosystem("ecu") ----------------------------------
            # Inputs are the geometry and geometry type and location object
            # Iteration over ecosystems is required
            # TODO Develop this
            # End of get_ecosystem("ecu") ------------------------------------

            # Add the location, and its ecosystems, to the base object.
            base.add_location(location)
        # Write the base object to a json file. Empty locations indicate no
        # ecosystems were found at the location. Empty ecosystems indicate the
        # location has no resolvable ecosystems.
        with open(output_file_path, "w", encoding='utf-8') as f:
            json.dump(base.data, f)


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
            wte = j["WTE"][0]["results"]
            res_attr = {}
            if len(wte) > 0:  # Not empty
                # Parse wte
                attributes = [
                    "Landforms",
                    "Landcover",
                    "Climate_Re",
                    "Moisture",
                    "Temperatur",
                ]
                for a in attributes:
                    res_attr[a] = _json_extract(wte, a)
            else:
                res_attr = {
                    "Landforms": [],
                    "Landcover": [],
                    "Climate_Re": [],
                    "Moisture": [],
                    "Temperatur": [],
                }
            # Combine with additional metadata
            edi = j["WTE"][0]["additional_metadata"]
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
            "comments",
        ]
    ]
    # df = df.rename(columns={"Climate_Re": "Climate_Region"})
    # Add "water" to the Landcover column if the comments column contains
    # "Is an aquatic ecosystem."
    df.loc[
        df["comments"].str.contains("Is an aquatic ecosystem."), "Landcover"
    ] = "water"
    with open("data/sssom/wte-envo.sssom.tsv", "r", encoding='utf-8') as f:
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
    df["ENVO_Landforms"] = df["Landforms"].map(
        sssom.set_index("subject_label")["object_id"]
    )
    # Mach values in the "Landcover" column to ENVO terms using the sssom
    # dataframe.
    df["ENVO_Landcover"] = df["Landcover"].map(
        sssom.set_index("subject_label")["object_id"]
    )
    # Mach values in the "Moisture" column to ENVO terms using the sssom
    # dataframe.
    df["ENVO_Moisture"] = df["Moisture"].map(
        sssom.set_index("subject_label")["object_id"]
    )
    # Mach values in the "Temperatur" column to ENVO terms using the sssom
    # dataframe.
    df["ENVO_Temperatur"] = df["Temperatur"].map(
        sssom.set_index("subject_label")["object_id"]
    )
    # Combine the "ENVO_Moisture" and "ENVO_Temperatur" columns into a single
    # column named "ENVO_Climate_Re" with a pipe (|) delimiter.
    df["ENVO_Climate_Re"] = df["ENVO_Moisture"] + "|" + df["ENVO_Temperatur"]
    # Drop the "ENVO_Moisture" and "ENVO_Temperatur" columns.
    df = df.drop(
        columns=["ENVO_Moisture", "ENVO_Temperatur", "Moisture", "Temperatur"]
    )
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
    for col in cols_eco:
        df["count"] = 1
        df_grouped = df.groupby(col).count().reset_index()
        df_grouped = df_grouped.sort_values(by="count", ascending=False)
        res[col] = df_grouped.set_index(col).to_dict()["count"]
    return res


def convert_point_to_envelope(point, buffer=0.5):
    """Convert an esriGeometryPoint to an esriGeometryEnvelope

    Parameters
    ----------
    point : dict
        An esriGeometryPoint
    buffer : float
        The distance in kilometers to buffer the point. The buffer is a radius
        around the point. The default is 0.5.

    Returns
    -------
    str : ESRI JSON envelope geometry

    Notes
    -----
    This function assumes the coordinate reference system of the input
    geometry is EPSG:4326.
    """
    point = json.loads(point)
    df = pd.DataFrame([{'longitude': point["x"], 'latitude': point["y"]}])
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(
            df.longitude,
            df.latitude
        ),
        crs='EPSG:4326'
    )
    # TODO Verify the consequences of projecting to an arbitrary CRS
    #  for sake of buffering.
    gdf = gdf.to_crs("EPSG:32634")  # A CRS in units of meters
    gdf.geometry = gdf.geometry.buffer(buffer*1000)  # Convert to meters
    bounds = gdf.to_crs("EPSG:4326").bounds
    envelope = {
        "xmin": bounds.minx[0],
        "ymin": bounds.miny[0],
        "xmax": bounds.maxx[0],
        "ymax": bounds.maxy[0],
        "spatialReference": point["spatialReference"]
    }
    return json.dumps(envelope)


if __name__ == "__main__":

    print("42")

    # # Transform EML to WTE ecosystems and write to json file
    # res = eml_to_wte_json(
    #     eml_dir="/Users/csmith/Code/spinneret/src/spinneret/data/eml/",
    #     output_dir="/Users/csmith/Code/spinneret/src/spinneret/data/json/",
    #     overwrite=True
    # )
    # res = eml_to_wte_json(
    #     eml_dir="/Users/csmith/Data/edi/eml/",
    #     output_dir="/Users/csmith/Data/edi/json/",
    #     overwrite=True
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
