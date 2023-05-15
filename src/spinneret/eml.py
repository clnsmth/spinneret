"""EML metadata related operations"""
import json
from lxml import etree


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

    def altitude_minimum(self, units=None):
        # TODO implement
        # Negative values are assumed to be below sea
        # level but are in fact with respect to a reference that
        #  is described in free text so it is impossible to parse.
        return None

    def altitude_maximum(self, units=None):
        # TODO implement
        # Negative values are assumed to be below sea
        # level but are in fact with respect to a reference that
        #  is described in free text so it is impossible to parse.
        return None

    def altitude_units(self):
        # TODO implement
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
        # TODO Add a source parameter to enable custom handling of geometry parsing.
        #  E.g. In the case of EMU points should be passed as Ezri envelopes, to
        #  enable query by a range of Z values rather than a set
        #  of discrete values. Points are represented as envelopes
        #  by replicating the X&Y values across the min and max
        #  fields for each of these parameters.
        if self.geom_type() == "polygon":
            return self._to_esri_polygon()
        if self.geom_type() == "point":
            return self._to_esri_point()
        if self.geom_type() == "envelope":
            return self._to_esri_envelope()
        return None

    def _to_esri_point(self):
        """Convert boundingCoordinates to ESRI JSON point geometry

        Returns
        -------
        str : ESRI JSON point geometry
            ESRI JSON point geometry

        Notes
        -----
        Defaulting coordinate reference system to WGS84 because the EML spec
        does not specify a CRS and notes the coordinates are meant to convey
        general information. Additionally, point locations in EML can also be
        represented as a GRingPointType, but is not being implemented here
        until needed.
        """
        res = {
            "x": self.west(),
            "y": self.north(),
            "spatialReference": {"wkid": 4326},
        }
        return json.dumps(res)

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
        res = {
            "xmin": self.west(),
            "ymin": self.south(),
            "xmax": self.east(),
            "ymax": self.north(),
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


if __name__ == "__main__":
    geocov = get_geographic_coverage(eml="data/eml/edi.1.1.xml")
    for item in geocov:
        print(item.to_esri_geometry())
