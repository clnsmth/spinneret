"""Get ENVO Classifications from Global Ecological Land Units Lookup"""
import glob
import os.path
import json
import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from spinneret.utilities import user_agent
from spinneret.eml import get_geographic_coverage
import matplotlib.pyplot as plt


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
            "geometry_type": None,  # TODO This is the actual geometry type (e.g. point) rather than the ESRI representation (e.g. envelope with same lat min/max and lon min/max), because this is used for diagnostic purposes and understanding if the underlying sampling space is a point or envelope.
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
        # Don't add empty comments. They are not useful.
        if comments is None:
            pass
        elif isinstance(comments, list):
            if len(comments) == 0:
                pass
            for comment in comments:
                # Append each comment to the list of comments, so we don't
                # end up with nested lists in the location comments attribute.
                self.data["comments"].append(comment)
        else:
            self.data["comments"].append(comments)


    def add_ecosystem(self, ecosystem):
        # TODO should not add anything if is an empty list or None,?
        for item in ecosystem:
            self.data["ecosystem"].append(item)


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
        # TODO should not add anything if is an empty list or None,
        self.data["comments"].append(comments)

    def add_attributes(self, attributes):
        # TODO should not add anything if is an empty list or None,?
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
        elif source == "emu":
            self.data = {
                "OceanName": {"label": None, "annotation": None},
                "Depth": {"label": None, "annotation": None},
                "Temperature": {"label": None, "annotation": None},
                "Salinity": {"label": None, "annotation": None},
                "Dissolved Oxygen": {"label": None, "annotation": None},
                "Nitrate": {"label": None, "annotation": None},
                "Phosphate": {"label": None, "annotation": None},
                "Silicate": {"label": None, "annotation": None},
                "EMU_Descriptor": {"label": None, "annotation": None}
            }

    def set_attributes(self, unique_ecosystem_attributes, source):
        attributes = Attributes(source=source)
        if source == "wte":
            attributes.set_wte_attributes(unique_ecosystem_attributes)
            self.data = attributes.data
        elif source == "ecu":
            attributes.set_ecu_attributes(unique_ecosystem_attributes)
            self.data = attributes.data
        elif source == "emu":
            attributes.set_emu_attributes(unique_ecosystem_attributes)
            self.data = attributes.data

    def set_wte_attributes(self, unique_ecosystem_attributes):
        if len(unique_ecosystem_attributes) == 0:
            return None
        for attribute in self.data.keys():
            label = unique_ecosystem_attributes[attribute]
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
                    "annotation": self.get_annotation(label, source="wte")
                }
        self.data = self.data


    def set_ecu_attributes(self, unique_ecosystem_attributes):
        """Set attributes for ECU.

        Parameters
        ----------
        unique_ecosystem_attributes : str
            Dictionary of unique ecosystem attributes.
        """
        if len(unique_ecosystem_attributes) == 0:
            return None
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

    def set_emu_attributes(self, unique_ecosystem_attributes):
        if len(unique_ecosystem_attributes) == 0:
            return None
        # There are two attributes for EMU, OceanName and Name_2018, the latter
        # of which is composed of 7 atomic attributes.
        attributes = json.loads(unique_ecosystem_attributes)["attributes"]
        # Get OceanName
        ocean_name = attributes.get("OceanName")
        # Atomize Name_2018: Split on commas and remove whitespace
        descriptors = attributes.get("Name_2018")
        descriptors = descriptors.split(",")
        descriptors = [g.strip() for g in descriptors]
        # Add ocean name to front of descriptors list in preparation for the zipping operation below
        descriptors = [ocean_name] + descriptors
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
                "annotation": self.get_annotation(label, source="emu")
            }
        # Add composite EMU_Description class and annotation.
        # Get ecosystems values and join with commas
        # TODO Fix issue where an attribute from the initialized list returned by
        #  Attributes() was missing for some reason and thus an annotation couldn't
        #  be found for it. If arbitrary joining of empties to the annotation string
        #  is done, then the annotation may be wrong. Best to just leave it out.
        EMU_Descriptor = [f.get("label") for f in self.data.values()]
        # Knock of the last one, which is EMU_Descriptor
        EMU_Descriptor = EMU_Descriptor[:-1]

        # FIXME: This is a hack to deal with the fact that some of the
        #  attributes are None. This is a problem with the data, not the
        #  code. The code should be fixed to deal with this. This is related
        #  to the FIXMEs in convert_codes_to_values. The issue can be
        #  reproduced by running on the geographic coverage in the file
        #  knb-lter-sbc.100.11.xml.
        if None in EMU_Descriptor:
            EMU_Descriptor = ["n/a" if f is None else f for f in EMU_Descriptor]

        EMU_Descriptor = ", ".join(EMU_Descriptor)
        EMU_Descriptor_annotation = [f.get("annotation") for f in self.data.values()]
        # Knock of the last one, which is EMU_Descriptor
        EMU_Descriptor_annotation = EMU_Descriptor_annotation[:-1]

        # FIXME: This is a hack to deal with the fact that some of the
        #  attributes are None. Not sure why this is happening. Recreate this
        #  issue by running on geographic coverage in the file knb-lter-sbc.100.11.xml
        if None in EMU_Descriptor_annotation:
            EMU_Descriptor_annotation = ["Placeholder" if f is None else f for f in EMU_Descriptor_annotation]

        EMU_Descriptor_annotation = "|".join(EMU_Descriptor_annotation)
        self.data["EMU_Descriptor"] = {
            "label": EMU_Descriptor,
            "annotation": EMU_Descriptor_annotation
        }
        # Append to results
        self.data = self.data

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
        elif source == "emu":
            return "Placeholder"  # TODO - add EMU sssom and parse
        # FIXME This commented code isn't working when run on local files
        # res = sssom.loc[
        #     sssom["subject_label"] == label.lower(),
        #     "object_id"
        # ].values[0]
        # return res
        return "Placeholder"

class Response:
    """A class to parse the response from the identify operation

    Parameters
    ----------
    json : dict
        A dictionary of the JSON response from the identify operation.
    """

    def __init__(self, json, geometry):
        self.json = json
        self.geometry = geometry


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
            if len(pv) > 0 and pv[0] == "NoData":
                return "WTE: Location is an area of water."
        return None

    def has_ecosystem(self, source):
        if source == "wte":
            res = _json_extract(self.json, "Pixel Value")
            if len(res) == 0:
                return False
            if len(res) > 0 and res[0] == "NoData":
                return False
            return True
        elif source == "ecu" or source == "emu":
            # FIXME: This produces an error when running the geographic coverage
            #  in the file knb-lter-ntl.420.2.
            res = len(self.json["features"])
            if res == 0:
                return False
            if res > 0:
                return True
        return None

    def get_unique_ecosystems(self, source):
        """Get unique ecosystems from a response

        Parameters
        ----------
        source : str
            The source of the response. Either "wte" or "ecu".

        Returns
        -------
        res : list
            A list of unique ecosystems in the response, in the format of the
            response object (i.e. not parsed to data model).
        """
        #  TODO Note this parallels get_attributes() in some ways. May want to
        #   rename this function after that one. They serve slightly different
        #   purposes. The current name of this function is a bit misleading.
        #   A better name may be create_ecosystem_attribute_iterable(), or
        #   get_unique_ecosystem_attributes().
        if source == 'wte':
            # Parse the attributes of the ecosystems listed in the response
            # object in a form that can be compared and used to render the list
            # of unique ecosystems returned by the identify operation.
            if not self.has_ecosystem(source="wte"):
                return list()
            descriptors = []
            attributes = Attributes(source="wte").data.keys()
            results = self.json.get("results")
            for result in results:
                res = dict()
                for attribute in attributes:
                    res[attribute] = result['attributes'].get(attribute)
                res = json.dumps(res)
                descriptors.append(res)
            descriptors = set(descriptors)
            descriptors = [json.loads(d) for d in descriptors]
            return descriptors
        elif source == 'ecu':
            if not self.has_ecosystem(source="ecu"):
                return list()
            attribute = "CSU_Descriptor"
            descriptors = self.get_attributes([attribute])[attribute]
            descriptors = set(descriptors)
            descriptors = list(descriptors)
            return descriptors
        elif source == 'emu':
            if not self.has_ecosystem(source="emu"):
                return list()
            # FIXME? - get_ecosystems_for_geometry_z_values does two things:
            #  1. gets ecosystems for z values
            #  2. gets unique ecosystems
            #  This doesn't follow the pattern for WTE and ECU, where all
            #  ecosystems are first retrieved, then unique ecosystems are
            #  derived. Either this function should be split into two, or the
            #  WTE and ECU function's get and unique operations should be
            #  combined into one.
            self.convert_codes_to_values(
                source="emu")  # FIXME? This pattern differs from WTE and ECU implementations. Change? See implementation notes.
            descriptors = self.get_ecosystems_for_geometry_z_values(source="emu")  # FIXME? This pattern differs from WTE and ECU implementations. Change? See implementation notes.
            return descriptors

    def get_ecosystems(self, source):
        if source == "wte":
            res = self.get_wte_ecosystems()
        elif source == "ecu":
            res = self.get_ecu_ecosystems()
        elif source == "emu":
            res = self.get_emu_ecosystems()
        return res

    def get_wte_ecosystems(self):
        ecosystems = []
        unique_wte_ecosystems = self.get_unique_ecosystems(source="wte")
        for unique_wte_ecosystem in unique_wte_ecosystems:
            ecosystem = Ecosystem()
            ecosystem.set_source("wte")
            ecosystem.set_version(None)
            attributes = Attributes(source="wte")
            attributes.set_attributes(unique_ecosystem_attributes=unique_wte_ecosystem,
                                      source="wte")
            ecosystem.add_attributes(attributes)
            ecosystems.append(ecosystem.data)
        return ecosystems

    def get_ecu_ecosystems(self):
        ecosystems = []
        unique_ecu_ecosystems = self.get_unique_ecosystems(source="ecu")
        for unique_ecu_ecosystem in unique_ecu_ecosystems:
            ecosystem = Ecosystem()
            ecosystem.set_source("ecu")
            ecosystem.set_version(None)
            attributes = Attributes(source="ecu")
            attributes.set_attributes(unique_ecosystem_attributes=unique_ecu_ecosystem,
                                      source="ecu")
            ecosystem.add_attributes(attributes)
            ecosystems.append(ecosystem.data)
        return ecosystems

    def get_emu_ecosystems(self):
        ecosystems = []
        unique_emu_ecosystems = self.get_unique_ecosystems(source="emu")
        for unique_emu_ecosystem in unique_emu_ecosystems:
            ecosystem = Ecosystem()
            ecosystem.set_source("emu")
            ecosystem.set_version(None)
            attributes = Attributes(source="emu")
            attributes.set_attributes(unique_ecosystem_attributes=unique_emu_ecosystem,
                                      source="emu")
            ecosystem.add_attributes(attributes)
            ecosystems.append(ecosystem.data)
        return ecosystems

    def convert_codes_to_values(self, source):
        # Convert the codes listed under the Name_2018 and OceanName
        # attributes to the descriptive string values so the EMU
        # response object more closely resembles the ECU and WTE
        # response objects and can be processed in the same way. This is a
        # tradeoff between processing the response object in a way that is
        # consistent with the other response objects (supporting readability)
        # and processing the response object in a way that may be more
        # efficient. Profiling has not yet been conducted on this.
        if source == "emu":
            # Create the code-value map for OceanName
            field_names = [field["name"] for field in self.json["fields"]]
            i = field_names.index("OceanName")
            ocean_name_map = pd.DataFrame(
                self.json.get("fields")[i].get("domain").get("codedValues")
            )
            # Create the code-value map for Name_2018
            i = field_names.index("Name_2018")
            name_2018_map = pd.DataFrame(
                self.json.get("fields")[i].get("domain").get("codedValues")
            )
            # Iterate over the features array replacing OceanName and
            # Name_2018 codes with corresponding values in the maps
            for i in range(len(self.json.get("features"))):
                # OceeanName
                code = self.json.get("features")[i]["attributes"]["OceanName"]

                # FIXME: Not all locations have OceanName values (e.g. is a
                #  bay or lake). There is probably a better value to use here.
                #  To recreate this issue run on the geographic coverage
                #  present in knb-lter-bes.5025.1.xml
                if code is None:
                    value = "Not an ocean"
                else:
                    value = ocean_name_map.loc[
                        ocean_name_map["code"] == code, "name"
                    ].iloc[0]

                self.json.get("features")[i]["attributes"]["OceanName"] = value
                # Name_2018
                code = self.json.get("features")[i]["attributes"]["Name_2018"]

                # FIXME Not all locations have Name_2018 values (not sure why
                #  this is the case). To recreate this issue run on the
                #  geographic coverage present in knb-lter-sbc.100.11.xml,
                #  edi.99.5.xml.
                try:
                    value = name_2018_map.loc[
                        name_2018_map["code"] == code, "name"
                    ].iloc[0]
                except IndexError:
                    value = "n/a"
                self.json.get("features")[i]["attributes"]["Name_2018"] = value

    def get_ecosystems_for_geometry_z_values(self, source="emu"):
        if source == "emu":
            # - Get the z values from the geometry attribute of the response object
            geometry = json.loads(self.geometry)
            zmin = geometry.get("zmin")
            zmax = geometry.get("zmax")
            res = []
            if zmin is None or zmax is None:  # Case when no z values are provided
                for item in self.json["features"]:
                    parsed = {
                        "attributes": {
                            "OceanName": item['attributes']['OceanName'],
                            "Name_2018": item['attributes']['Name_2018']
                        }
                    }
                    res.append(json.dumps(parsed))
            else:  # Case when z values are present
                for item in self.json["features"]:
                    top = item['attributes']['UnitTop']
                    bottom = item['attributes']['UnitBottom']
                    # Case where zmin and zmax are equal
                    if (zmax <= top and zmax >= bottom) and (zmin <= top and zmin >= bottom):
                        parsed = {
                            "attributes": {
                                "OceanName": item['attributes']['OceanName'],
                                "Name_2018": item['attributes']['Name_2018']
                            }
                        }
                        res.append(json.dumps(parsed))
                    # Case where zmin and zmax are not equal (a depth interval)
                    if (zmax <= top and zmax >= bottom) or (zmin <= top and zmin >= bottom):
                        parsed = {
                            "attributes": {
                                "OceanName": item['attributes']['OceanName'],
                                "Name_2018": item['attributes']['Name_2018']
                            }
                        }
                        res.append(json.dumps(parsed))
            # Get the unique set of ecosystems (don't want duplicates) and convert back to a list as preferred by subsequent operations
            res = set(res)
            res = list(res)
            return res


def identify(geometry=str, map_server=str):
    """Run an identify operation on a USGS map service resource and return the
    requested attributes

    For more see: https://rmgsc.cr.usgs.gov/arcgis/sdk/rest/index.html#/Identify_Map_Service/02ss000000m7000000/

    Parameters
    ----------
    geometry : str
        An ESRI geometry in JSON format. If a geometry contains Z values, they
        must be in units of meters to meet downstream processing assumptions.
        The coordinate reference system of the input should be EPSG:4326.
        Not doing so may result in spurious results.
    map_server : str
        The map server to query. Options are `wte`.

    Returns
    -------
    Response

    Notes
    -----
    Point locations should be represented as envelopes, i.e. where xmin=xmax,
    xmin=xmax, and zmin=zmax. Z can be null.
    """
    base = (
        "https://rmgsc.cr.usgs.gov/arcgis/rest/services/"
        + map_server
        + "/MapServer/identify"
    )
    payload = {
        "f": "json",
        "geometry": geometry,
        "geometryType": _get_geometry_type(geometry),
        "tolerance": 2,
        "mapExtent": "-2.865, 47.628, 5.321, 50.017",
        "imageDisplay": "600,550,96"
    }
    r = requests.get(base, params=payload, timeout=10, headers=user_agent())
    return Response(json=r.json(), geometry=geometry)


def query(geometry=str, map_server=str):
    """Run a query operation on a USGS map service resource and return the
    requested attributes

    For more see: https://rmgsc.cr.usgs.gov/arcgis/sdk/rest/index.html#//02ss0000000r000000

    Parameters
    ----------
    geometry : str
        An ESRI geometry in JSON format. If a geometry contains Z values, they
        must be in units of meters to meet downstream processing assumptions.
        The coordinate reference system of the input should be EPSG:4326.
        Not doing so may result in spurious results.
    map_server : str
        The map server to query. Options are `ecu`.

    Returns
    -------
    Response

    Notes
    -----
    Point locations should be represented as envelopes, i.e. where xmin=xmax,
    xmin=xmax, and zmin=zmax. Z can be null. The results will be the same. Usage of
    `esriGeometryEnvelope`/`envelope` is used in place of esriGeometryPoint because
    it behaves the same and it allows for the
    expression of zmin and zmax, which in the case of some map services, such
    as `emu`, it is necessary to return all ecosystems occurring within an
    elevation range, rather than only a point location.
    """
    # Convert "ecu" to query parameters. The "ecu" abstraction is used to
    # align the UX with usage of "wte".
    if map_server == "ecu":
        layer = "0"
        map_server = "gceVector"
        # Convert point geometries to envelopes. This is necessary because
        # the query map service does not support point geometries.
        if _is_point_location(geometry):
            # A buffer radius of 0.5 km should gaurantee overlap of coastal
            # sampling locations, represented by point geometries, and location
            # of ECUs. This is a conservative estimate of the spatial
            # accuracy between the point location and nearby ECUs.
            geometry = convert_point_to_envelope(geometry, buffer=0.5)  # TODO Rename to add_buffer? Doing so may keep from confounding the fact that the input geometry may either represent a true point or an envelope
        payload = {
            "f": "geojson",
            "geometry": geometry,
            "geometryType": _get_geometry_type(geometry),
            "where": "1=1",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "returnTrueCurves": "false",
            "returnIdsOnly": "false",
            "returnCountOnly": "false",
            "returnZ": "false",
            "returnM": "false",
            # "returnDistinctValues": "true",
            "returnExtentOnly": "false"
        }
        base = (
                "https://rmgsc.cr.usgs.gov/arcgis/rest/services/" +
                map_server +
                "/MapServer/" +
                layer +
                "/query"
        )
    elif map_server == 'emu':
        layer = "0"
        map_server = "EMU_2018"
        # Note, the map service query form contains these parameters and
        # values, which are not included in the payload below because they
        # are not defined in the query-feature-service-layer documentation:
        #   - Return Geodetic: false
        #   - Feature Encoding: esriDefault
        #   - Apply VCS Projection: false
        #   - Return Unique IDs Only: false
        #   - Return Count Only: false
        #   - Return Query Geometry: false
        #   - Cache Hint: false
        payload = {
            "f": "json",  # GEOJSON doesn't return OceanName and Name_2018
            "geometry": geometry,
            "geometryType": _get_geometry_type(geometry),
            "where": "1=1",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "UnitTop,UnitBottom,OceanName,Name_2018",
            "distance": "10",
            "units": "esriSRUnit_NauticalMile",
            "multipatchOption": "xyFootprint",
            "outSR": '{"wkid":4326}',
            "returnIdsOnly": "false",
            "returnZ": "false",
            "returnM": "false",
            "returnExceededLimitFeatures": "true",
            "sqlFormat": "none",
            "orderByFields": "UnitTop desc",
            "returnDistinctValues": "false",
            "returnExtentOnly": "false"
        }
        base = (
                "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/" +
                map_server +
                "/FeatureServer/" +
                layer +
                "/query"
        )
    r = requests.get(base, params=payload, timeout=10, headers=user_agent())
    return Response(json=r.json(), geometry=geometry)


def convert_point_to_envelope(geometry, buffer=None):
    """Convert an esriGeometryPoint to an esriGeometryEnvelope

    Parameters
    ----------
    geometry : dict
        An esriGeometryEnvelope representing a point
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
    if not _is_point_location(geometry) or buffer is None:
        return geometry
    geometry = json.loads(geometry)
    df = pd.DataFrame([{'longitude': geometry["xmin"], 'latitude': geometry["ymin"]}])
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
    gdf = gdf.to_crs("EPSG:4326")  # Convert back to EPSG:4326
    bounds = gdf.bounds
    # TODO Update values of geometry object
    geometry["xmin"] = bounds.minx[0]
    geometry["ymin"] = bounds.miny[0]
    geometry["xmax"] = bounds.maxx[0]
    geometry["ymax"] = bounds.maxy[0]
    return json.dumps(geometry)


def _get_geometry_type(geometry):
    """Get the geometry type from the response object's geometry attribute

    Parameters
    ----------
    geometry : str
        The ESRI geometry object

    Returns
    -------
    str : The geometry type

    Notes
    -----
    This function determines the geometry type by looking for distinguishing
    properties of the ESRI geometry object.
    """
    geometry = json.loads(geometry)
    if geometry.get("x") is not None:
        return "esriGeometryPoint"
    elif geometry.get("xmin") is not None:
        return "esriGeometryEnvelope"
    elif geometry.get("rings") is not None:
        return "esriGeometryPolygon"
    else:
        return None

def _is_point_location(geometry):
    """Is a geometry a point location? Points are represented as envelopes, but
    it is useful to know if the geometry is a point location for some internal
    processes

    Parameters
    ----------
    geometry : str
        The ESRI geometry object

    Returns
    -------
    bool : True if the geometry is a point location, False otherwise
    """
    if _get_geometry_type(geometry) != "esriGeometryEnvelope":
        return False
    geometry = json.loads(geometry)
    if geometry.get('xmin') == geometry.get('xmax') and \
            geometry.get('ymin') == geometry.get('ymax'):
        return True
    return False

def _polygon_or_envelope_to_points(geometry):
    """Convert a polygon or envelope to a list of points

    Parameters
    ----------
    geometry : str
        The ESRI geometry object

    Returns
    -------
    list : A list of ESRI envelope geometries (as str) representing point locations
    (i.e. xmin == xmax and ymin == ymax). Note, this is a design decision.

    Notes
    -----
    For improving the results from the WTE identify responses. Currently, the
    identify operation returns the midpoint of the envelope. This function
    returns the vertices of a polygon or envelope in addition to the centroid.
    This function could likely be improved.

    Currently, this only operates on the outer ring of a polygon. Inner rings
    are not considered. A warning is thrown if inner rings are present, because
    the centroid will be incorrect.
    """
    geometry_type = _get_geometry_type(geometry)
    geometry = json.loads(geometry)
    # TODO-merge: Create xy series based on whether the geometry is a polygon
    #  or a envelope.
    if geometry_type == "esriGeometryPolygon":
        # Create a GeoSeries with the vertices of the polygon
        bounds = []
        for xy_pair in geometry.get("rings")[0]:
            x, y = xy_pair
            bounds.append((x, y))
        # Bump off the last one since it is the same as the first
        bounds.pop()
        # TODO Throw a warning when inner ring is present, because the centriod
        #  will be incorrect.
    elif geometry_type == "esriGeometryEnvelope":
        # Create a GeoSeries with the four corners of the envelope
        bounds = [
            (geometry.get("xmin"), geometry.get("ymin")),
            (geometry.get("xmax"), geometry.get("ymin")),
            (geometry.get("xmax"), geometry.get("ymax")),
            (geometry.get("xmin"), geometry.get("ymax"))
        ]
    # Construct point geometries from the envelope corners
    res = []
    for corner in bounds:
        res.append(
            json.dumps(
                {
                    "xmin": corner[0],
                    "ymin": corner[1],
                    "xmax": corner[0],
                    "ymax": corner[1],
                    "zmin": geometry.get("zmin"),
                    "zmax": geometry.get("zmax"),
                    "spatialReference": geometry.get("spatialReference")
                }
            )
        )
    # Get the centroid of the geometry
    shape = gpd.GeoSeries(Polygon(bounds))
    centroid = shape.centroid
    # TODO Use one single consistent approach to transferring values to the
    #  result for simplicity.
    res.append(
        json.dumps(
            {
                "xmin": centroid.x[0],
                "ymin": centroid.y[0],
                "xmax": centroid.x[0],
                "ymax": centroid.y[0],
                "zmin": geometry.get("zmin"),
                "zmax": geometry.get("zmax"),
                "spatialReference": geometry.get("spatialReference")
            }
        )
    )
    return res


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
            # Identify all ecosystems at the location (i.e. for the geometry)


            # Query the WTE map server
            if g.geom_type() == "point":
                location.add_comments("WTE: Was queried.")
                try:
                    r = identify(
                        geometry=g.to_esri_geometry(),
                        map_server="wte"
                    )
                except ConnectionError:
                    r = None
                    location.add_comments("WTE: Connection error. Please try again.")  # TODO: This should be more informative
                if r is not None:
                    # Build the ecosystem object and add it to the location.
                    if r.has_ecosystem(source="wte"):
                        ecosystems = r.get_ecosystems(source="wte")
                        location.add_ecosystem(ecosystems)
                    else:
                        # Add an explanatory comment if not resolved, to
                        # facilitate understanding and analysis.
                        location.add_comments(r.get_comments("wte"))
            # FIXME-WTE: Below is a draft implementation supporting identify
            #  operations on the WTE map server for envelope types. This should
            #  be extended to polygons and then merged with the above code
            #  block to in a way that is consistent (as possible) with the
            #  queries of ECU and EMU map servers, so all three can be wrapped
            #  in a single function for sake of simplicity.
            #  The current implmentation uses iteration over the point geometries
            #  representing the envelope, collecting the results in a list,
            #  then finally appending to the location object.
            #  A POTENTIAL SOLUTION here is to:
            #  - allow envelope and polygon geometries into the identify operation
            #  - convert the envelope to a polygon geometries into points
            #  - perform iteration on the geometries
            #  - construct an r.json response object that incorporates the results
            #    and which mimicks the natural server response (but with a list
            #    of ecosystem attributes, one from each identify)
            #  - resume processing as normal.
            #  The advantage of this approach is that it is consistent with the
            #  point implementation for WTE and all query operations for ECU
            #  and EMU. Additionally, understanding of the code is simplified
            #  by placing this as close as possible to the identify operation
            #  rather than creating long drawnout code blocks and logic that
            #  is too much to keep in mind at once.
            #  Testing currently occurs in:
            #  - test/test_globalelu.py::test_eml_to_wte_json_wte_envelope
            if g.geom_type() == "envelope" or g.geom_type() == "polygon":
                location.add_comments("WTE: Was queried.")
                points = _polygon_or_envelope_to_points(g.to_esri_geometry())  # Differs from the point implementation
                ecosystems_in_envelope = []  # Differs from the point implementation
                ecosystems_in_envelope_comments = []  # Differs from the point implementation
                for point in points:  # Differs from the point implementation
                    try:
                        r = identify(
                            geometry=point,
                            map_server="wte"
                        )
                    except ConnectionError:
                        r = None
                        location.add_comments("WTE: Connection error. Please try again.")  # TODO: This should be more informative
                    if r is not None:
                        # Build the ecosystem object and add it to the location.
                        if r.has_ecosystem(source="wte"):
                            ecosystems = r.get_ecosystems(source="wte")
                            # TODO Implement a uniquing function to handle the
                            #  envelope and polygon edge cases. The common pattern
                            #  is to do this as a subroutine of get_ecosystems()
                            #  but is temporarily being implemented here until
                            #  a good design pattern is found. Proposed design
                            #  patterns are:
                            #
                            ecosystems_in_envelope.append( # Differs from the point implementation
                                json.dumps(ecosystems[0]))
                        else:
                            # Add an explanatory comment if not resolved, to
                            # facilitate understanding and analysis.
                            ecosystems_in_envelope_comments.append(r.get_comments("wte")) # Differs from the point implementation
                ecosystems_in_envelope = list(set(ecosystems_in_envelope))  # Differs from the point implementation
                ecosystems_in_envelope = [json.loads(e) for e in ecosystems_in_envelope]  # Differs from the point implementation
                # FIXME This creates a list of comments in the response object.
                #  This should only be a string, however, more than one
                #  comment may result from multiple queries. What to do?
                ecosystems_in_envelope_comments = list(set(ecosystems_in_envelope_comments))  # Differs from the point implementation
                location.add_ecosystem(ecosystems_in_envelope)  # Differs from the point implementation
                location.add_comments(ecosystems_in_envelope_comments)  # Differs from the point implementation
                # TODO end of draft implementation for envelopes ----------------------------
            # if g.geom_type() == "polygon":
            #     location.add_comments("WTE: Was not queried because geometry is an unsupported type.")



            # Query the ECU map server
            location.add_comments("ECU: Was queried.")
            try:
                r = query(
                    geometry=g.to_esri_geometry(),
                    map_server="ecu"
                )
            except ConnectionError:
                r = None
                location.add_comments("ECU: Connection error. Please try again.")  # TODO: This should be more informative
            if r is not None:
                # Build the ecosystem object and add it to the location.
                if r.has_ecosystem(source="ecu"):
                    ecosystems = r.get_ecosystems(source="ecu")
                    location.add_ecosystem(ecosystems)
                else:
                    # Add an explanatory comment if not resolved, to
                    # facilitate understanding and analysis.
                    location.add_comments(r.get_comments("ecu"))

            # Query the EMU map server
            location.add_comments("EMU: Was queried.")
            try:
                r = query(
                    geometry=g.to_esri_geometry(),
                    map_server="emu"
                )
            except ConnectionError:
                r = None
                location.add_comments("EMU: Connection error. Please try again.")  # TODO: This should be more informative
            if r is not None:
                # Build the ecosystem object and add it to the location.
                if r.has_ecosystem(source="emu"):
                    ecosystems = r.get_ecosystems(source="emu")
                    location.add_ecosystem(ecosystems)
                else:
                    # Add an explanatory comment if not resolved, to
                    # facilitate understanding and analysis.
                    location.add_comments(r.get_comments("ecu"))


            # TODO Query the Freshwater map server

            # Add the location, and its ecosystems, to the base object.
            base.add_location(location)
        # Write the base object to a json file. Empty locations indicate no
        # ecosystems were found at the location. Empty ecosystems indicate the
        # location has no resolvable ecosystems.
        with open(output_file_path, "w", encoding='utf-8') as f:
            json.dump(base.data, f)



def json_to_df(json_dir, format="wide"):
    """Combine json files into a single long dataframe for analysis

    Parameters
    ----------
    json_dir : str
        Path to directory containing json files
    format : str
        Format of output dataframe. Options are "wide" and "long". Default is
        "wide".

    Returns
    -------
    df : pandas.DataFrame
        A dataframe of geographic coverages and corresponding ecosystems

    Notes
    -----
    The results of this function modify the native representation of ecosystems
    returned by map servers from grouped sets of attributes to grouped sets of
    unique attributes, and thus changes the semantics of how the map server
    authors intended the data to be interpreted. Specifically, areal geometries
    will include the unique attributes of all ecosystems within the area,
    whereas point geometries will only include the attributes of the ecosystem
    at the point.
    """
    files = glob.glob(json_dir + "*.json")
    if not files:
        raise FileNotFoundError("No json files found")
    res = []
    # Initialize the fields of the output dictionary from the
    # attributes of the ecosystem object. Constructing this dictionary
    # manually is probably less work and more understandable than
    # using a coded approach.
    boilerplate_output = {
        "dataset": None,
        "description": None,
        "geometry_type": None,
        "comments": None,
        "source": None,
        "Climate_Re": None,  # WTE attributes ...
        "Landcover": None,
        "Landforms": None,
        "Slope": None,  # ECU attributes ...
        "Sinuosity": None,
        "Erodibility": None,
        "Temperature and Moisture Regime": None,
        "River Discharge": None,
        "Wave Height": None,
        "Tidal Range": None,
        "Marine Physical Environment": None,
        "Turbidity": None,
        "Chlorophyll": None,
        "OceanName": None,  # EMU attributes ...
        "Depth": None,
        "Temperature": None,
        "Salinity": None,
        "Dissolved Oxygen": None,
        "Nitrate": None,
        "Phosphate": None,
        "Silicate": None
    }
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            # Load the results of the json file into a dictionary for parsing
            j = json.load(f)
            dataset = j.get("dataset")
            location = j.get("location")
            if len(location) == 0:
                output = dict(boilerplate_output)  # Create a copy of the boilerplate
                output["dataset"] = dataset
                res.append(output)
            else:
                for loc in location:
                    description = loc.get("description")
                    geometry_type = loc.get("geometry_type")
                    comments = loc.get("comments")
                    # Use list comprehension to convert None values to empty
                    #  strings to handle an unexpected edge case.
                    comments = ["" if c is None else c for c in comments]
                    comments = " ".join(comments)
                    ecosystem = loc.get("ecosystem")
                    if len(ecosystem) == 0:
                        output = dict(boilerplate_output)  # Create a copy of the boilerplate
                        output["dataset"] = dataset
                        output["description"] = description
                        output["geometry_type"] = geometry_type
                        output["comments"] = comments
                        res.append(output)
                    else:
                        for eco in ecosystem:
                            source = eco.get("source")
                            output = dict(boilerplate_output)  # Create a copy of the boilerplate
                            output["dataset"] = dataset
                            output["description"] = description
                            output["geometry_type"] = geometry_type
                            output["comments"] = comments
                            output["source"] = source
                            res.append(output)
                            attributes = eco.get("attributes")
                            # Iterate over the resolved ecosystem's attributes
                            # and add them to the output dictionary if they are
                            # present in the boilerplate dictionary.
                            for attribute in attributes:
                                if attribute in output.keys():
                                    output[attribute] = attributes[attribute]["label"]
                            res.append(output)
    # Convert to dataframe
    df = pd.DataFrame(res)
    # Sort for readability
    df[["scope", "identifier"]] = df["dataset"].str.split(".", n=1, expand=True)
    df["identifier"] = pd.to_numeric(df["identifier"])
    df = df.sort_values(by=["scope", "identifier"])
    df = df.drop(columns=["scope", "identifier"])
    # Rename columns for readability
    df = df.rename(
        columns={
            "dataset": "package_id",
            "description": "geographic_coverage_description",
            "source": "ecosystem_type"
        }
    )
    # Convert acronyms (of ecosystem types) to more descriptive names
    df["ecosystem_type"] = df["ecosystem_type"].replace(
        {
            "wte": "Terrestrial",
            "ecu": "Coastal",
            "emu": "Marine"
        }
    )
    if format == "wide":
        return df
    # Convert df to long format
    df = pd.melt(
        df,
        id_vars=[
            "package_id",
            "geographic_coverage_description",
            "geometry_type",
            "comments",
            "ecosystem_type"
        ],
        var_name="ecosystem_attribute",
        value_name="value"
    )
    # Remove all rows where the ecosystem is None
    # df = df.dropna(subset=["value"])
    # Drop duplicate rows and values of "n/a"
    df = df.drop_duplicates()
    df = df[df["value"] != "n/a"]
    # Sort by package_id and attribute
    df = df.sort_values(by=['package_id', 'geographic_coverage_description', 'geometry_type', 'comments',
       'ecosystem_type', 'ecosystem_attribute', 'value'])
    # Sort for readability. This is the same as the above sort but is done
    # again after a series of operations that may have changed the order.
    df[["scope", "identifier"]] = df["package_id"].str.split(".", n=1, expand=True)
    df["identifier"] = pd.to_numeric(df["identifier"])
    df = df.sort_values(by=["scope", "identifier"])
    df = df.drop(columns=["scope", "identifier"])
    return df



def get_number_of_unique_ecosystems(df_wide):
    """Get the number of unique ecosystems for each ecosystem type

    Parameters
    ----------
    df_wide : pandas.DataFrame
        A dataframe created by `json_to_df` in wide format

    Returns
    -------
    res : dict
        A dictionary of the number of unique ecosystems for each ecosystem type
    """
    # Drop the columns that are not ecosystem attributes except for ecosystem
    # type, which is needed to count the number of unique ecosystems for each
    # ecosystem type.
    df = df_wide.drop(columns=["package_id", "geographic_coverage_description", "geometry_type", "comments"])
    # Drop duplicate rows
    df = df.drop_duplicates()
    # Drop rows where the ecosystem type is None
    df = df.dropna(subset=["ecosystem_type"])
    # Get the total number of unique ecosystems and for each ecosystem type
    res = {}
    res["Total"] = df.shape[0]
    for eco_type in df["ecosystem_type"].unique():
        res[eco_type] = df[df["ecosystem_type"] == eco_type].shape[0]
    return res


def get_number_of_unique_geographic_coverages(df_wide):
    """Get the number of unique geographic coverages

    Parameters
    ----------
    df_wide : pandas.DataFrame
        A dataframe created by `json_to_df` in wide format

    Returns
    -------
    res : int
        The number of unique geographic coverages
    """
    # Create a new data frame with the columns package_id,
    # geographic_coverage_description, and geometry_type. These form a
    # composite key of unique ecosystems.
    df = df_wide[["package_id", "geographic_coverage_description", "geometry_type"]]
    # Drop duplicate rows
    df = df.drop_duplicates()
    # Get the number of unique geographic coverages
    res = df.shape[0]
    return res


def get_percent_of_geometries_with_no_ecosystem(df_wide):
    """Get the percent of geometries with no ecosystem

    Parameters
    ----------
    df_wide : pandas.DataFrame
        A dataframe created by `json_to_df` in wide format

    Returns
    -------
    res : float
        The percent of geometries with no ecosystem
    """
    # Drop the columns that are not ecosystem attributes or geometry identifiers
    # since we only want to count the number of geometries with no ecosystem.
    df = df_wide.drop(columns=['geometry_type', 'comments', 'ecosystem_type'])
    # Get number of rows where package_id and geographic_coverage_description
    # are the same.
    total_number_of_unique_geometries = df[df.duplicated(subset=['package_id', 'geographic_coverage_description'])].shape[0]
    # Remove rows from df where all ecosystem attribute columns do not have a
    # value of None. The remaining rows represent geometries that have no
    # ecosystem for some reason.
    ecosystem_attribute_columns = [
        'Climate_Re',
        'Landcover', 'Landforms', 'Slope', 'Sinuosity', 'Erodibility',
        'Temperature and Moisture Regime', 'River Discharge', 'Wave Height',
        'Tidal Range', 'Marine Physical Environment', 'Turbidity',
        'Chlorophyll', 'OceanName', 'Depth', 'Temperature', 'Salinity',
        'Dissolved Oxygen', 'Nitrate', 'Phosphate', 'Silicate'
    ]
    df = df[df[ecosystem_attribute_columns].isnull().all(axis=1)]
    # Drop duplicate rows
    df = df.drop_duplicates()
    # Get the number of rows in df, which is the number of geometries with no
    # ecosystem
    number_of_geometries_with_no_ecosystem = df.shape[0]
    # Get the percent of geometries with no ecosystem
    percent_of_geometries_with_no_ecosystem = number_of_geometries_with_no_ecosystem / total_number_of_unique_geometries * 100
    return percent_of_geometries_with_no_ecosystem


def plot_wide_data(df_wide):
    """Plot the proportion of ecosystem types across datasets

    Parameters
    ----------
    df_wide : pandas.DataFrame
        A dataframe created by `json_to_df` in wide format

    Returns
    -------
    None
    """

    # Count the number of unique ecosystem_type values for each unique
    # package_id.
    df = df_wide.groupby(['package_id', 'ecosystem_type']).size().reset_index(name='Count')
    # Create a histogram of the counts for each ecosystem_type
    df.hist(column='Count', by='ecosystem_type', bins=20, figsize=(10, 10))
    plt.show()
    return None


def plot_long_data(df_long):
    # Remove rows that contain None in any column to facilitate plotting.
    df = df_long.dropna()
    # Create a bar chart for Terrestrial ecosystem types, including ecosystem attribute
    # and value
    df_terrestrial = df[df['ecosystem_type'].isin(['Terrestrial'])]
    df_terrestrial = df_terrestrial.groupby(['ecosystem_attribute', 'value']).size().reset_index(name='Count')
    df_terrestrial.plot.bar(x='ecosystem_attribute', y='Count', rot=90, figsize=(10, 10))
    plt.show()
    return None


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


if __name__ == "__main__":

    print("42")

    # # Transform EML to ecosystems and write to json file
    # # For the spinneret package
    # res = eml_to_wte_json(
    #     eml_dir="/Users/csmith/Code/spinneret/src/spinneret/data/eml/",
    #     output_dir="/Users/csmith/Code/spinneret/src/spinneret/data/json/",
    #     overwrite=True
    # )
    # # For local testing
    # eml_to_wte_json(
    #     eml_dir="/Users/csmith/Data/edi/top_20_eml/",
    #     output_dir="/Users/csmith/Data/edi/top_20_json/",
    #     overwrite=False
    # )

    # Combine json files into a single dataframe
    df_long = json_to_df(json_dir="/Users/csmith/Data/edi/top_20_json/", format="long")
    df_wide = json_to_df(json_dir="/Users/csmith/Data/edi/top_20_json/", format="wide")

    # # Write df to tsv
    # import csv
    # output_dir = "/Users/csmith/Data/edi/"
    # df_long.to_csv(output_dir + "top_20_results.tsv", sep="\t", index=False, quoting=csv.QUOTE_ALL)

    # Summarize WTE results
    unique_ecosystems_by_type = get_number_of_unique_ecosystems(df_wide)
    no_ecosystem = get_percent_of_geometries_with_no_ecosystem(df_wide)
    number_of_unique_geographic_coverages = get_number_of_unique_geographic_coverages(df_wide)
    # PLot
    # plot_wide_data(df_wide)
    plot_long_data(df_long)
    print("42")
