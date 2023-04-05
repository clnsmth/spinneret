"""EML metadata related operations"""
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
    >>> res = eml.get_geographic_coverage(
    ...     eml="../src/spinneret/data/eml/edi.1.1.xml"
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

    def geographicDescription(self):
        """Get geographicDescription element from geographicCoverage

        Returns
        -------
        str : geographicDescription
            geographicDescription element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="../src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].geographicDescription()
        """
        return self.gc.findtext(".//geographicDescription")

    def westBoundingCoordinate(self):
        """Get westBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : westBoundingCoordinate
            westBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="../src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].westBoundingCoordinate()
        """
        try:
            return float(self.gc.findtext(".//westBoundingCoordinate"))
        except TypeError:
            return None

    def eastBoundingCoordinate(self):
        """Get eastBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : eastBoundingCoordinate
            eastBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="../src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].eastBoundingCoordinate()
        """
        try:
            return float(self.gc.findtext(".//eastBoundingCoordinate"))
        except TypeError:
            return None

    def northBoundingCoordinate(self):
        """Get northBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : northBoundingCoordinate
            northBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="../src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].northBoundingCoordinate()
        """
        try:
            return float(self.gc.findtext(".//northBoundingCoordinate"))
        except TypeError:
            return None

    def southBoundingCoordinate(self):
        """Get southBoundingCoordinate element from geographicCoverage

        Returns
        -------
        float : southBoundingCoordinate
            southBoundingCoordinate element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="../src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].southBoundingCoordinate()
        """
        try:
            return float(self.gc.findtext(".//southBoundingCoordinate"))
        except TypeError:
            return None

    def datasetGPolygonOuterGRing(self):
        """Get datasetGPolygonOuterGRing/gRing element from geographicCoverage

        Returns
        -------
        str : datasetGPolygonOuterGRing/gRing
            datasetGPolygonOuterGRing/gRing element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="../src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].datasetGPolygonOuterGRing()
        """
        try:
            return self.gc.findtext(".//datasetGPolygonOuterGRing/gRing")
        except TypeError:
            return None

    def datasetGPolygonExclusionGRing(self):
        """Get datasetGPolygonExclusionGRing/gRing element from
        geographicCoverage

        Returns
        -------
        str : datasetGPolygonExclusionGRing/gRing
            datasetGPolygonExclusionGRing/gRing element

        Examples
        --------
        >>> from spinneret import eml
        >>> res = eml.get_geographic_coverage(
        ...     eml="../src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].datasetGPolygonExclusionGRing()
        """
        try:
            return self.gc.findtext(".//datasetGPolygonExclusionGRing/gRing")
        except TypeError:
            return None

    def _geom_type(self):
        """Get geometry type from geographicCoverage

        Returns
        -------
        str : geometry type
            geometry type as "polygon", "point", or "envelope"
        """
        if self.gc.find(".//datasetGPolygon") is not None:
            return "polygon"
        if self.gc.find(".//boundingCoordinates") is not None:
            if (
                self.westBoundingCoordinate() == self.eastBoundingCoordinate()
                and self.northBoundingCoordinate() == self.southBoundingCoordinate()
            ):
                return "point"
            return "envelope"
        return None

    def to_esri_geometry(self):
        """Convert geographicCoverage to ESRI JSON geometry

        Returns
        -------
        dict : ESRI JSON geometry
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
        ...     eml="../src/spinneret/data/eml/edi.1.1.xml"
        ... )
        >>> res[0].to_esri_geometry()
        >>> res[1].to_esri_geometry()
        >>> res[2].to_esri_geometry()
        """
        if self._geom_type() == "polygon":
            return self._to_esri_polygon()
        if self._geom_type() == "point":
            return self._to_esri_point()
        if self._geom_type() == "envelope":
            return self._to_esri_envelope()
        return None

    def _to_esri_point(self):
        """Convert boundingCoordinates to ESRI JSON point geometry

        Returns
        -------
        dict : ESRI JSON point geometry
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
            "x": self.westBoundingCoordinate(),
            "y": self.northBoundingCoordinate(),
            "spatialReference": {"wkid": 4326},
        }
        return res

    def _to_esri_envelope(self):
        """Convert boundingCoordinates to ESRI JSON envelope geometry

        Returns
        -------
        dict : ESRI JSON envelope geometry
            ESRI JSON envelope geometry

        Notes
        -----
        Defaulting to WGS84 because the EML spec does not specify a CRS and
        notes the coordinates are meant to convey general information.
        """
        res = {
            "xmin": self.westBoundingCoordinate(),
            "ymin": self.southBoundingCoordinate(),
            "xmax": self.eastBoundingCoordinate(),
            "ymax": self.northBoundingCoordinate(),
            "spatialReference": {"wkid": 4326},
        }
        return res

    def _to_esri_polygon(self):
        """Convert datasetGPolygon to ESRI JSON polygon geometry

        Returns
        -------
        dict : ESRI JSON polygon geometry
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

        if self.datasetGPolygonOuterGRing() is not None:
            ring = _format_ring(self.datasetGPolygonOuterGRing())
            res = {"rings": [ring], "spatialReference": {"wkid": 4326}}
            if self.datasetGPolygonExclusionGRing() is not None:
                ring = _format_ring(self.datasetGPolygonExclusionGRing())
                res["rings"].append(ring)
            return res
        return None


if __name__ == "__main__":
    geocov = get_geographic_coverage(eml="data/eml/edi.1.1.xml")
    for item in geocov:
        print(item.to_esri_geometry())
