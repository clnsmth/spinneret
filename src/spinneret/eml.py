"""EML metadata related operations"""

import glob
import json
import os
from math import isnan
from lxml import etree
from spinneret.globalelu import Base, Location, identify, \
    query
from spinneret.utilities import _polygon_or_envelope_to_points


def get_geographic_coverage(eml):
    """Get geographicCoverage elements from EML metadata

    Parameters
    ----------
    eml : str
        Path to EML metadata file

    Returns
    -------
    list : GeographicCoverage
        List of GeographicCoverage instances

    Examples
    --------
    >>> from spinneret import eml
    >>>
    >>> res = eml.get_geographic_coverage(
    ...     eml="src/spinneret/data/eml/edi.1.1.xml"
    ... )
    """
    xml = etree.parse(eml)
    gc = xml.xpath(".//geographicCoverage")
    if len(gc) == 0:
        return None
    res = []
    for item in gc:
        res.append(GeographicCoverage(item))
    return res


class GeographicCoverage:
    """geographicCoverage related operations"""

    def __init__(self, gc):
        self.gc = gc

    def description(self):
        """Get geographicDescription element from geographicCoverage

        Returns
        -------
        str : description
            geographicDescription element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].description()
        """
        try:
            return self.gc.findtext(".//geographicDescription")
        except TypeError:
            return None

    def west(self):
        """Get westBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : west
            westBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].westBoundingCoordinate()
        """
        try:
            return float(self.gc.findtext(".//westBoundingCoordinate"))
        except TypeError:
            return None

    def east(self):
        """Get eastBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : east
            eastBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].east()
        """
        try:
            return float(self.gc.findtext(".//eastBoundingCoordinate"))
        except TypeError:
            return None

    def north(self):
        """Get northBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : north
            northBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].north()
        """
        try:
            return float(self.gc.findtext(".//northBoundingCoordinate"))
        except TypeError:
            return None

    def south(self):
        """Get southBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : south
            southBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].south()
        """
        try:
            return float(self.gc.findtext(".//southBoundingCoordinate"))
        except TypeError:
            return None

    def altitude_minimum(self, to_meters=False):
        """Get altitudeMinimum element from geographicCoverage

        Parameters
        ----------
        to_meters : bool
            Convert to meters?

        Returns
        -------
        float : altitude_minimum
            altitudeMinimum element

        Notes
        -----
        A conversion to meters is based on the value retrieved from the
        altitudeUnits element of the geographic coverage, and a conversion
        table from the EML specification. If the altitudeUnits element is
        not present, and the to_meters parameter is True, then the altitude
        value is returned as-is and a warning issued.
        """
        try:
            res = float(self.gc.findtext(".//altitudeMinimum"))
        except TypeError:
            res = None
        if to_meters is True:
            res = self._convert_to_meters(x=res, from_units=self.altitude_units())
        return res

    def altitude_maximum(self, to_meters=False):
        """Get altitudeMaximum element from geographicCoverage

        Parameters
        ----------
        to_meters : bool
            Convert to meters?

        Returns
        -------
        float : altitude_maximum
            altitudeMaximum element

        Notes
        -----
        A conversion to meters is based on the value retrieved from the
        altitudeUnits element of the geographic coverage, and a conversion
        table from the EML specification. If the altitudeUnits element is
        not present, and the to_meters parameter is True, then the altitude
        value is returned as-is and a warning issued.
        """
        try:
            res = float(self.gc.findtext(".//altitudeMaximum"))
        except TypeError:
            res = None
        if to_meters is True:
            res = self._convert_to_meters(x=res, from_units=self.altitude_units())
        return res

    def altitude_units(self):
        try:
            return self.gc.findtext(".//altitudeUnits")
        except TypeError:
            return None

    def outer_gring(self):
        """Get datasetGPolygonOuterGRing/gRing element from geographicCoverage

        Returns
        -------
        str : outer_gring
            datasetGPolygonOuterGRing/gRing element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].outer_gring()
        """
        try:
            return self.gc.findtext(".//datasetGPolygonOuterGRing/gRing")
        except TypeError:
            return None

    def exclusion_gring(self):
        """Get datasetGPolygonExclusionGRing/gRing element from
        geographicCoverage

        Returns
        -------
        str : exclusion_gring
            datasetGPolygonExclusionGRing/gRing element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].exclusion_gring()
        """
        try:
            return self.gc.findtext(".//datasetGPolygonExclusionGRing/gRing")
        except TypeError:
            return None

    def geom_type(self, schema="eml"):
        """Get geometry type from geographicCoverage

        Parameters
        ----------
        schema : str
            Schema dialect to use when returning values, either "eml" or "esri"

        Returns
        -------
        str : geometry type
            geometry type as "polygon", "point", or "envelope" for
            `schema="eml"`, or "esriGeometryPolygon", "esriGeometryPoint", or
            "esriGeometryEnvelope" for `schema="esri"`
        """
        if self.gc.find(".//datasetGPolygon") is not None:
            if schema == "eml":
                return "polygon"
            return "esriGeometryPolygon"
        if self.gc.find(".//boundingCoordinates") is not None:
            if self.west() == self.east() and self.north() == self.south():
                if schema == "eml":
                    res = "point"
                else:
                    res = "esriGeometryPoint"
                return res
            if schema == "eml":
                res = "envelope"
            else:
                res = "esriGeometryEnvelope"
            return res
        return None

    def to_esri_geometry(self):
        """Convert geographicCoverage to ESRI JSON geometry

        Returns
        -------
        str : ESRI JSON geometry
            ESRI JSON geometry type as "polygon", "point", or "envelope"

        Notes
        -----
        The logic here presumes that if a polygon is listed, it is the true
        feature of interest, rather than the associated boundingCoordinates,
        which are required to be listed by the EML spec alongside all polygon
        listings.

        Geographic coverage latitude and longitude are assumed to be in the
        spatial reference system of WKID 4326 and are inserted into the ESRI
        geometry as x and y values. Geographic coverages with altitudes and
        associated units are converted to units of meters and added to the ESRI
        geometry as z values.

        Geographic coverages that are point locations, as indicated by their
        bounding box latitude min and max values and longitude min and max
        values being equivalent, are converted to ESRI envelopes rather than
        ESRI points, because the envelope geometry type is more expressive and
        handles more usecases than the point geometry alone. Furthermore, point
        locations represented as envelope geometries produce the same results
        as if the point of location was represented as a point geometry.

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].to_esri_geometry()
        >>> res[1].to_esri_geometry()
        >>> res[2].to_esri_geometry()
        """
        if self.geom_type() == "polygon":
            return self._to_esri_polygon()
        if self.geom_type() == "point":
            return (
                self._to_esri_envelope()
            )  # Envelopes are more expressive and behave the same as point geometries, so us envelopes
        if self.geom_type() == "envelope":
            return self._to_esri_envelope()
        return None

    def _to_esri_envelope(self):
        """Convert boundingCoordinates to ESRI JSON envelope geometry

        Returns
        -------
        str : ESRI JSON envelope geometry
            ESRI JSON envelope geometry

        Notes
        -----
        Defaulting to WGS84 because the EML spec does not specify a CRS and
        notes the coordinates are meant to convey general information.
        """
        altitude_minimum = self.altitude_minimum(to_meters=True)
        altitude_maximum = self.altitude_maximum(to_meters=True)
        res = {
            "xmin": self.west(),
            "ymin": self.south(),
            "xmax": self.east(),
            "ymax": self.north(),
            "zmin": altitude_minimum,
            "zmax": altitude_maximum,
            "spatialReference": {"wkid": 4326},
        }
        return json.dumps(res)

    def _to_esri_polygon(self):
        """Convert datasetGPolygon to ESRI JSON polygon geometry

        Returns
        -------
        str : ESRI JSON polygon geometry
            ESRI JSON polygon geometry

        Notes
        -----
        Defaulting to WGS84 because the EML spec does not specify a CRS and
        notes the coordinates are meant to convey general information.
        """

        def _format_ring(gring):
            # Reformat the string of coordinates into a list of lists
            ring = []
            for item in gring.split():
                x = item.split(",")
                # Try to convert the coordinates to floats. The EML spec does
                # not enforce strictly numeric values.
                try:
                    ring.append([float(x[0]), float(x[1])])
                except TypeError:
                    ring.append([x[0], x[1]])
            # Ensure that the first and last points are the same
            if ring[0] != ring[-1]:
                ring.append(ring[0])
            # TODO Ensure that the outer ring is oriented clockwise and the
            #  inner ring is oriented counter-clockwise
            return ring

        if self.outer_gring() is not None:
            ring = _format_ring(self.outer_gring())
            res = {"rings": [ring], "spatialReference": {"wkid": 4326}}
            if self.exclusion_gring() is not None:
                ring = _format_ring(self.exclusion_gring())
                res["rings"].append(ring)
            return json.dumps(res)
        return None

    @staticmethod
    def _convert_to_meters(x, from_units):
        """Convert an elevation from a given unit of measurement to meters.

        Parameters
        ----------
        x : float
            Value to convert.
        from_units : str
            Units to convert from. This must be one of: meter, decimeter,
            dekameter, hectometer, kilometer, megameter, Foot_US, foot,
            Foot_Gold_Coast, fathom, nauticalMile, yard, Yard_Indian,
            Link_Clarke, Yard_Sears, mile.

        Returns
        -------
        float : in units of meters
        """
        # TODO Warn if x is a non-nan float and the units are empty. This indicates that
        #  the value has no units and results derived from subsequent use of the value
        #  may be incorrect.
        if x is None:
            x = float("NaN")
        conversion_factors = _load_conversion_factors()
        conversion_factor = conversion_factors.get(from_units, float("NaN"))
        if not isnan(
            conversion_factor
        ):  # Apply the conversion factor if from_units is a valid unit of measurement otherwise return the length value as is
            x = x * conversion_factors.get(from_units, float("NaN"))
        if isnan(
            x
        ):  # Convert back to None, which is the NULL type returned by altitude_minimum and altitude_maximum
            x = None
        return x


def _load_conversion_factors():
    """Load conversion factors

    Returns
    -------
    dict : conversion factors
        Dictionary of conversion factors for converting from common units of
        length to meters.
    """
    conversion_factors = {
        "meter": 1,
        "decimeter": 1e-1,
        "dekameter": 1e1,
        "hectometer": 1e2,
        "kilometer": 1e3,
        "megameter": 1e6,
        "Foot_US": 0.3048006,
        "foot": 0.3048,
        "Foot_Gold_Coast": 0.3047997,
        "fathom": 1.8288,
        "nauticalMile": 1852,
        "yard": 0.9144,
        "Yard_Indian": 0.914398530744440774,
        "Link_Clarke": 0.2011661949,
        "Yard_Sears": 0.91439841461602867,
        "mile": 1609.344,
    }
    return conversion_factors


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
            with open(output_file_path, "w", encoding="utf-8") as f:
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
                    r = identify(geometry=g.to_esri_geometry(), map_server="wte")
                except ConnectionError:
                    r = None
                    location.add_comments(
                        "WTE: Connection error. Please try again."
                    )  # TODO: This should be more informative
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
            #  The current implmentation uses iteration over the point
            #  geometries representing the envelope, collecting the results in
            #  a list, then finally appending to the location object.
            #  A POTENTIAL SOLUTION here is to:
            #  - allow envelope and polygon geometries into the identify
            #  operation
            #  - convert the envelope to a polygon geometries into points
            #  - perform iteration on the geometries
            #  - construct an r.json response object that incorporates the
            #  results and which mimicks the natural server response (but with
            #  a list of ecosystem attributes, one from each identify)
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
                points = _polygon_or_envelope_to_points(
                    g.to_esri_geometry()
                )  # Differs from the point implementation
                # Differs from point implementation
                ecosystems_in_envelope = []
                ecosystems_in_envelope_comments = (
                    []
                )  # Differs from the point implementation
                for point in points:  # Differs from the point implementation
                    try:
                        r = identify(geometry=point, map_server="wte")
                    except ConnectionError:
                        r = None
                        location.add_comments(
                            "WTE: Connection error. Please try again."
                        )  # TODO: This should be more informative
                    if r is not None:
                        # Build the ecosystem object and add it to the
                        # location.
                        if r.has_ecosystem(source="wte"):
                            ecosystems = r.get_ecosystems(source="wte")
                            # TODO Implement a uniquing function to handle the
                            #  envelope and polygon edge cases. The common
                            #  pattern is to do this as a subroutine of
                            #  get_ecosystems() but is temporarily being
                            #  implemented here until a good design pattern is
                            #  found. Proposed design patterns are:
                            #
                            # Differs from the point implementation
                            ecosystems_in_envelope.append(json.dumps(ecosystems[0]))
                        else:
                            # Add an explanatory comment if not resolved, to
                            # facilitate understanding and analysis.
                            ecosystems_in_envelope_comments.append(
                                r.get_comments("wte")
                            )  # Differs from the point implementation
                ecosystems_in_envelope = list(
                    set(ecosystems_in_envelope)
                )  # Differs from the point implementation
                ecosystems_in_envelope = [
                    json.loads(e) for e in ecosystems_in_envelope
                ]  # Differs from the point implementation
                # FIXME This creates a list of comments in the response object.
                #  This should only be a string, however, more than one
                #  comment may result from multiple queries. What to do?
                ecosystems_in_envelope_comments = list(
                    set(ecosystems_in_envelope_comments)
                )  # Differs from the point implementation
                location.add_ecosystem(
                    ecosystems_in_envelope
                )  # Differs from the point implementation
                location.add_comments(
                    ecosystems_in_envelope_comments
                )  # Differs from the point implementation
                # TODO end of draft implementation for envelopes --------------
            # if g.geom_type() == "polygon":
            #     location.add_comments("WTE: Was not queried because geometry
            #     is an unsupported type.")

            # Query the ECU map server
            location.add_comments("ECU: Was queried.")
            try:
                r = query(geometry=g.to_esri_geometry(), map_server="ecu")
            except ConnectionError:
                r = None
                location.add_comments(
                    "ECU: Connection error. Please try again."
                )  # TODO: This should be more informative
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
                r = query(geometry=g.to_esri_geometry(), map_server="emu")
            except ConnectionError:
                r = None
                location.add_comments(
                    "EMU: Connection error. Please try again."
                )  # TODO: This should be more informative
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
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(base.data, f)


if __name__ == "__main__":
    geocov = get_geographic_coverage(eml="data/eml/edi.1.1.xml")
    for item in geocov:
        print(item.to_esri_geometry())
