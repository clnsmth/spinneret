"""Tests for conftest.py"""

from json import dumps
from unittest.mock import patch


def test_geom_type(test_geometry):
    """Test the geom_type method of the GeographicCoverage class"""
    assert test_geometry[0].geom_type() == "envelope"
    assert test_geometry[1].geom_type() == "point"
    assert test_geometry[2].geom_type() == "polygon"
    assert test_geometry[0].geom_type(schema="esri") == "esriGeometryEnvelope"
    assert test_geometry[1].geom_type(schema="esri") == "esriGeometryPoint"
    assert test_geometry[2].geom_type(schema="esri") == "esriGeometryPolygon"
    
    
def test_to_esri_geometry(test_geometry):
    """Test to_esri_geometry method of the GeographicCoverage class.

    Envelopes are converted to esriGeometryEnvelope, points to
    esriGeometryEnvelope, and polygons to esriGeometryPolygon.
    """
    # Envelope to envelope
    g = test_geometry[0]  # An envelope without units
    assert g.to_esri_geometry() == dumps(
        {
            "xmin": -123.552,
            "ymin": 39.804,
            "xmax": -120.83,
            "ymax": 40.441,
            "zmin": None,
            "zmax": None,
            "spatialReference": {"wkid": 4326},
        }
    )

    # Point to envelope
    g = test_geometry[1]  # A point without units
    assert g.to_esri_geometry() == dumps(
        {
            "xmin": -72.22,
            "ymin": 42.48,
            "xmax": -72.22,
            "ymax": 42.48,
            "zmin": None,
            "zmax": None,
            "spatialReference": {"wkid": 4326},
        }
    )

    # Point to envelope
    g = test_geometry[11]  # A point with units
    assert g.to_esri_geometry() == dumps(
        {
            "xmin": -157.875,
            "ymin": 21.125,
            "xmax": -157.875,
            "ymax": 21.125,
            "zmin": -15.0,
            "zmax": 0.0,
            "spatialReference": {"wkid": 4326},
        }
    )

    # Polygon to polygon
    g = test_geometry[2]
    assert g.to_esri_geometry() == dumps(
        {
            "rings": [
                [
                    [-123.7976226, 39.3085666],
                    [-123.8222818, 39.3141049],
                    [-123.8166231, 39.2943269],
                    [-123.7976226, 39.3085666],
                ],
                [
                    [-123.8078563, 39.3068951],
                    [-123.8163387, 39.3086898],
                    [-123.813222, 39.3022756],
                    [-123.8078177, 39.3068354],
                    [-123.8078563, 39.3068951],
                ],
            ],
            "spatialReference": {"wkid": 4326},
        }
    )


def test_description(test_geometry):
    """Test description method of the GeographicCoverage class"""
    assert isinstance(test_geometry[0].description(), str)
    test_geometry[0].gc.remove(test_geometry[0].gc.find(".//geographicDescription"))
    assert test_geometry[0].description() is None


def test_west(test_geometry):
    """Test the west method of the GeographicCoverage class"""
    assert isinstance(test_geometry[0].west(), float)
    test_geometry[0].gc.remove(test_geometry[0].gc.find(".//westBoundingCoordinate").getparent())
    assert test_geometry[0].west() is None


def test_east(test_geometry):
    """Test east method of the GeographicCoverage class"""
    assert isinstance(test_geometry[0].east(), float)
    test_geometry[0].gc.remove(test_geometry[0].gc.find(".//eastBoundingCoordinate").getparent())
    assert test_geometry[0].east() is None


def test_north(test_geometry):
    """Test north_bounding_coordinate method of the GeographicCoverage class"""
    assert isinstance(test_geometry[0].north(), float)
    test_geometry[0].gc.remove(test_geometry[0].gc.find(".//northBoundingCoordinate").getparent())
    assert test_geometry[0].north() is None


def test_south(test_geometry):
    """Test the south_bounding_coordinate method of the GeographicCoverage
    class"""
    assert isinstance(test_geometry[0].south(), float)
    test_geometry[0].gc.remove(test_geometry[0].gc.find(".//southBoundingCoordinate").getparent())
    assert test_geometry[0].south() is None


def test_outer_gring(test_geometry):
    """Test the outer_gring method of the GeographicCoverage class"""
    assert isinstance(test_geometry[2].outer_gring(), str)
    test_geometry[2].gc.remove(test_geometry[2].gc.find(".//datasetGPolygonOuterGRing").getparent())
    assert test_geometry[2].outer_gring() is None


def test_exclusion_gring(test_geometry):
    """Test the exclusion_gring method of the GeographicCoverage class"""
    assert isinstance(test_geometry[2].exclusion_gring(), str)
    test_geometry[2].gc.remove(
        test_geometry[2].gc.find(".//datasetGPolygonExclusionGRing").getparent()
    )
    assert test_geometry[2].exclusion_gring() is None


def test_altitude_minimum(test_geometry):
    """Test the altitude_minimum method of the GeographicCoverage class"""
    g = test_geometry[11]  # A geographic coverage with altitudes in meters
    assert isinstance(g.altitude_minimum(), float)
    assert g.altitude_minimum() == -15
    # The _convert_to_meters method should be called when the to_meters
    # argument is True.
    with patch(
        "tests.conftest.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_minimum(to_meters=True)
        mock__convert_to_meters.assert_called_once()
    # The _convert_to_meters method should not be called when the to_meters
    # argument is False.
    with patch(
        "tests.conftest.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_minimum(to_meters=False)
        mock__convert_to_meters.assert_not_called()
    # Returns None when no altitudeMinimum element is present.
    g.gc.remove(g.gc.find(".//altitudeMinimum").getparent())
    assert g.altitude_minimum() is None


def test_altitude_maximum(test_geometry):
    """Test the altitude_maximum method of the GeographicCoverage class"""
    g = test_geometry[11]  # A geographic coverage with altitudes in meters
    assert isinstance(g.altitude_maximum(), float)
    assert g.altitude_maximum() == 0

    # The _convert_to_meters method should be called when the to_meters
    # argument is True.
    with patch(
        "tests.conftest.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_maximum(to_meters=True)
        mock__convert_to_meters.assert_called_once()

    # The _convert_to_meters method should not be called when the to_meters
    # argument is False.
    with patch(
        "tests.conftest.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_maximum(to_meters=False)
        mock__convert_to_meters.assert_not_called()

    # Returns None when no altitudeMinimum element is present.
    g.gc.remove(g.gc.find(".//altitudeMaximum").getparent())
    assert g.altitude_maximum() is None


def test_altitude_units(test_geometry):
    """Test the altitude_units method of the GeographicCoverage class"""
    g = test_geometry[11]  # A geographic coverage with altitude in units of feet
    assert isinstance(g.altitude_units(), str)
    assert g.altitude_units() == "meter"
    g.gc.remove(g.gc.find(".//altitudeUnits").getparent())
    assert g.altitude_units() is None


def test__convert_to_meters(test_geometry):
    """Test geographicCoverage _convert_to_meters method

    This method should convert the altitude values to meters if they are not
    already in meters. If the altitude units are not specified, the method
    should return None, which is the default value returned by the
    altitude_minimum and altitude_maximum methods. Because this is a method
    of the geographicCoverage class, it is not possible to test it directly
    so we use an instance of geographicCoverage to access the method for
    testing.
    """
    g = test_geometry[0]
    # Case when no altitude or units are specified in the geographicCoverage
    assert g._convert_to_meters(x=None, from_units=None) is None
    # Case when altitude is specified but no units are specified. Should return value as is.
    assert g._convert_to_meters(x=10, from_units=None) == 10
    # Case when altitude is not specified but units are.
    assert g._convert_to_meters(x=None, from_units="meters") is None
    # Case when altitude is specified and units are specified. Should convert to meters.
    assert g._convert_to_meters(x=10, from_units="foot") == 3.048