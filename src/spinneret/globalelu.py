"""Get ENVO Classifications from Global Ecological Land Units Lookup"""

import json
import importlib.resources
import requests
import pandas as pd
from spinneret.utilities import user_agent, _json_extract, \
    convert_point_to_envelope, _get_geometry_type, _is_point_location


# pylint: disable=too-many-lines


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
        # Note, geometry_type (below) is the actual geometry type (e.g. point)
        # rather than the ESRI representation (e.g. envelope with same lat
        # min/max and lon min/max), because this is used for diagnostic
        # purposes and understanding if the underlying sampling space is a
        # point or envelope.
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
                "Raster.Temp_Class": {"label": None, "annotation": None},
                "Raster.Moisture_C": {"label": None, "annotation": None},
                "Raster.LC_ClassNa": {"label": None, "annotation": None},
                "Raster.LF_ClassNa": {"label": None, "annotation": None},
                "Raster.Temp_Moist": {"label": None, "annotation": None},
                "Raster.ClassName": {"label": None, "annotation": None},
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
                "CSU_Descriptor": {"label": None, "annotation": None},
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
                "EMU_Descriptor": {"label": None, "annotation": None},
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
                self.data[attribute] = {"label": label, "annotation": annotation}
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
                self.data[attribute] = {"label": label, "annotation": annotation}
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
        """Set attributes for ECU.

        Parameters
        ----------
        unique_ecosystem_attributes : str
            Dictionary of unique ecosystem attributes.

        Notes
        -----
        The expected attribute keys are not returned in the API response, but
        are defined in https://doi.org/10.5670/oceanog.2021.219. We use the
        paper to define the expected attributes here, and set them in the order
        that is consistently returned in the API response.
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
        # TODO Fix issue where an attribute from the initialized list returned
        #  by  Attributes() was missing for some reason and thus an annotation
        #  couldn't  be found for it. If arbitrary joining of empties to the
        #  annotation string is done, then the annotation may be wrong. Best to
        #  just leave it out.
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
            "annotation": CSU_Descriptor_annotation,
        }
        # Append to results
        self.data = self.data

    def set_emu_attributes(self, unique_ecosystem_attributes):
        """
        Notes
        -----
        The expected attribute keys are not returned in the API response, but
        are defined in https://doi.org/10.5670/oceanog.2017.116. We use the
        paper to define the expected attributes here, and set them in the order
        that is consistently returned in the API response.
        """
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
        # Add ocean name to front of descriptors list in preparation for the
        # zipping operation below
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
                "annotation": self.get_annotation(label, source="emu"),
            }
        # Add composite EMU_Description class and annotation.
        # Get ecosystems values and join with commas
        # TODO Fix issue where an attribute from the initialized list returned
        #  by  Attributes() was missing for some reason and thus an annotation
        #  couldn't  be found for it. If arbitrary joining of empties to the
        #  annotation string  is done, then the annotation may be wrong. Best
        #  to just leave it out.
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
        #  issue by running on geographic coverage in the file
        #  knb-lter-sbc.100.11.xml
        if None in EMU_Descriptor_annotation:
            EMU_Descriptor_annotation = [
                "Placeholder" if f is None else f for f in EMU_Descriptor_annotation
            ]

        EMU_Descriptor_annotation = "|".join(EMU_Descriptor_annotation)
        self.data["EMU_Descriptor"] = {
            "label": EMU_Descriptor,
            "annotation": EMU_Descriptor_annotation,
        }
        # Append to results
        self.data = self.data

    @staticmethod
    def get_annotation(label, source):
        if source == "wte":
            sssom_path = importlib.resources.files("spinneret.data.sssom").joinpath("wte-envo.sssom.tsv")
            with open(
                sssom_path,
                mode="r",
                encoding="utf-8",
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
            res = _json_extract(self.json, "UniqueValue.Pixel Value")
            if len(res) == 0:
                return False
            if len(res) > 0 and res[0] == "NoData":
                return False
            return True
        elif source == "ecu" or source == "emu":
            # FIXME: This produces an error when running the geographic
            #  coverage in the file knb-lter-ntl.420.2.
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
        if source == "wte":
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
                    res[attribute] = result["attributes"].get(attribute)
                res = json.dumps(res)
                descriptors.append(res)
            descriptors = set(descriptors)
            descriptors = [json.loads(d) for d in descriptors]
            return descriptors
        elif source == "ecu":
            if not self.has_ecosystem(source="ecu"):
                return list()
            attribute = "CSU_Descriptor"
            descriptors = self.get_attributes([attribute])[attribute]
            descriptors = set(descriptors)
            descriptors = list(descriptors)
            return descriptors
        elif source == "emu":
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

            # FIXME? This pattern differs from WTE and ECU implementations.
            #  Change? See implementation notes.
            self.convert_codes_to_values(source="emu")

            # FIXME? This pattern differs from WTE and ECU implementations.
            #  Change? See implementation notes.
            descriptors = self.get_ecosystems_for_geometry_z_values(source="emu")
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
            attributes.set_attributes(
                unique_ecosystem_attributes=unique_wte_ecosystem, source="wte"
            )
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
            attributes.set_attributes(
                unique_ecosystem_attributes=unique_ecu_ecosystem, source="ecu"
            )
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
            attributes.set_attributes(
                unique_ecosystem_attributes=unique_emu_ecosystem, source="emu"
            )
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
            # - Get the z values from the geometry attribute of the response
            # object
            geometry = json.loads(self.geometry)
            zmin = geometry.get("zmin")
            zmax = geometry.get("zmax")
            res = []
            if zmin is None or zmax is None:  # Case with no z values
                for item in self.json["features"]:
                    parsed = {
                        "attributes": {
                            "OceanName": item["attributes"]["OceanName"],
                            "Name_2018": item["attributes"]["Name_2018"],
                        }
                    }
                    res.append(json.dumps(parsed))
            else:  # Case when z values are present
                for item in self.json["features"]:
                    top = item["attributes"]["UnitTop"]
                    bottom = item["attributes"]["UnitBottom"]
                    # Case where zmin and zmax are equal
                    if (zmax <= top and zmax >= bottom) and (
                        zmin <= top and zmin >= bottom
                    ):
                        parsed = {
                            "attributes": {
                                "OceanName": item["attributes"]["OceanName"],
                                "Name_2018": item["attributes"]["Name_2018"],
                            }
                        }
                        res.append(json.dumps(parsed))
                    # Case where zmin and zmax are not equal (a depth interval)
                    if (zmax <= top and zmax >= bottom) or (
                        zmin <= top and zmin >= bottom
                    ):
                        parsed = {
                            "attributes": {
                                "OceanName": item["attributes"]["OceanName"],
                                "Name_2018": item["attributes"]["Name_2018"],
                            }
                        }
                        res.append(json.dumps(parsed))
            # Get the unique set of ecosystems (don't want duplicates) and
            # convert back to a list as preferred by subsequent operations
            res = set(res)
            res = list(res)
            return res


def identify(geometry=str, map_server=str):
    """Run an identify operation on a USGS map service resource and return the
    requested attributes

    For more see: https://rmgsc.cr.usgs.gov/arcgis/sdk/rest/index.html#/
        Identify_Map_Service/02ss000000m7000000/

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
        "imageDisplay": "600,550,96",
    }
    r = requests.get(base, params=payload, timeout=10, headers=user_agent())
    return Response(json=r.json(), geometry=geometry)


def query(geometry=str, map_server=str):
    """Run a query operation on a USGS map service resource and return the
    requested attributes

    For more see: https://rmgsc.cr.usgs.gov/arcgis/sdk/rest/index.html#//
        02ss0000000r000000

    Parameters
    ----------
    geometry : str
        An ESRI geometry in JSON format. If a geometry contains Z values, they
        must be in units of meters to meet downstream processing assumptions.
        The coordinate reference system of the input should be EPSG:4326.
        Not doing so may result in spurious results.
    map_server : str
        The map server to query. Options are `ecu`, `emu`.

    Returns
    -------
    Response

    Notes
    -----
    Point locations should be represented as envelopes, i.e. where xmin=xmax,
    xmin=xmax, and zmin=zmax. Z can be null. The results will be the same.
    Usage of `esriGeometryEnvelope`/`envelope` is used in place of
    esriGeometryPoint because it behaves the same and it allows for the
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

            # TODO Rename to add_buffer? Doing so may keep from confounding the
            #  fact that the input geometry may either represent a true point
            #  or an envelope
            geometry = convert_point_to_envelope(geometry, buffer=0.5)
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
            "returnExtentOnly": "false",
        }
        base = (
            "https://rmgsc.cr.usgs.gov/arcgis/rest/services/"
            + map_server
            + "/MapServer/"
            + layer
            + "/query"
        )
    elif map_server == "emu":
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
            "returnExtentOnly": "false",
        }
        base = (
            "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/"
            + map_server
            + "/FeatureServer/"
            + layer
            + "/query"
        )
    r = requests.get(base, params=payload, timeout=10, headers=user_agent())
    return Response(json=r.json(), geometry=geometry)
