"""Tests for the eml module."""
from json import dumps
import pytest
from spinneret import eml


@pytest.fixture
def geocov():
    """A list of GeographicCoverage instances from the test EML file."""
    res = eml.get_geographic_coverage(eml="src/spinneret/data/eml/edi.1.1.xml")
    return res


def test_get_geographic_coverage():
    """Test get_geographic_coverage function."""
    res = eml.get_geographic_coverage(eml="src/spinneret/data/eml/edi.1.1.xml")
    assert isinstance(res, list)
    for item in res:
        assert isinstance(item, eml.GeographicCoverage)


def test_geom_type(geocov):
    """Test geographicCoverage geom_type method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert geocov[0].geom_type() == "envelope"
    assert geocov[1].geom_type() == "point"
    assert geocov[2].geom_type() == "polygon"
    assert geocov[0].geom_type(schema="esri") == "esriGeometryEnvelope"
    assert geocov[1].geom_type(schema="esri") == "esriGeometryPoint"
    assert geocov[2].geom_type(schema="esri") == "esriGeometryPolygon"


def test_to_esri_geometry(geocov):
    """Test geographicCoverage to_esri_geometry method

    Envelopes are converted to esriGeometryEnvelope, points to
    esriGeometryEnvelope, and polygons to esriGeometryPolygon.
    """
    # Envelope to envelope
    g = geocov[0]
    assert g.to_esri_geometry() == dumps(
        {
            "xmin": -123.552,
            "ymin": 39.804,
            "xmax": -120.83,
            "ymax": 40.441,
            "zmin": None,
            "zmax": None,
            "spatialReference": {"wkid": 4326}
        }
    )

    # Point to envelope (we do this because envelopes produce same results as
    # points but are more expressive).
    g = geocov[1]
    assert g.to_esri_geometry() == dumps(
        {
            "xmin": -72.22,
            "ymin": 42.48,
            "xmax": -72.22,
            "ymax": 42.48,
            "zmin": None,
            "zmax": None,
            "spatialReference": {"wkid": 4326}
        }
    )

    # Polygon to polygon
    g = geocov[2]
    assert g.to_esri_geometry() == dumps(
        {
            "rings": [
                [[-123.7976226, 39.3085666], [-123.8222818, 39.3141049],
                 [-123.8166231, 39.2943269], [-123.7976226, 39.3085666]],
                [[-123.8078563, 39.3068951], [-123.8163387, 39.3086898],
                 [-123.813222, 39.3022756], [-123.8078177, 39.3068354],
                 [-123.8078563, 39.3068951]]
            ], "spatialReference": {"wkid": 4326}}
    )


def test_description(geocov):
    """Test geographicCoverage description method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].description(), str)
    geocov[0].gc.remove(geocov[0].gc.find(".//geographicDescription"))
    assert geocov[0].description() is None


def test_west(geocov):
    """Test geographicCoverage west method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].west(), float)
    geocov[0].gc.remove(
        geocov[0].gc.find(".//westBoundingCoordinate").getparent())
    assert geocov[0].west() is None


def test_east(geocov):
    """Test geographicCoverage east method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].east(), float)
    geocov[0].gc.remove(
        geocov[0].gc.find(".//eastBoundingCoordinate").getparent())
    assert geocov[0].east() is None


def test_north(geocov):
    """Test geographicCoverage north_bounding_coordinate method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].north(), float)
    geocov[0].gc.remove(
        geocov[0].gc.find(".//northBoundingCoordinate").getparent())
    assert geocov[0].north() is None


def test_south(geocov):
    """Test geographicCoverage south_bounding_coordinate method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].south(), float)
    geocov[0].gc.remove(
        geocov[0].gc.find(".//southBoundingCoordinate").getparent())
    assert geocov[0].south() is None


def test_outer_gring(geocov):
    """Test geographicCoverage outer_gring method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[2].outer_gring(), str)
    geocov[2].gc.remove(
        geocov[2].gc.find(".//datasetGPolygonOuterGRing").getparent())
    assert geocov[2].outer_gring() is None


def test_exclusion_gring(geocov):
    """Test geographicCoverage exclusion_gring method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[2].exclusion_gring(), str)
    geocov[2].gc.remove(
        geocov[2].gc.find(".//datasetGPolygonExclusionGRing").getparent()
    )
    assert geocov[2].exclusion_gring() is None


def test_altitude_minimum(geocov):
    g = geocov[11]  # A geographic coverage with altitude in units of feet
    assert isinstance(g.altitude_minimum(), float)
    assert g.altitude_minimum() == -49.2126
    assert g.altitude_minimum(to_meters=True) == -15.00000048
    g.gc.remove(
        g.gc.find(".//altitudeMinimum").getparent()
    )
    assert g.altitude_minimum() is None


def test_altitude_maximum(geocov):
    g = geocov[11]  # A geographic coverage with altitude in units of feet
    assert isinstance(g.altitude_maximum(), float)
    assert g.altitude_maximum() == 0
    assert g.altitude_maximum(to_meters=True) == 0
    g.gc.remove(
        g.gc.find(".//altitudeMaximum").getparent()
    )
    assert g.altitude_minimum() is None


def test_altitude_units(geocov):
    g = geocov[11]  # A geographic coverage with altitude in units of feet
    assert isinstance(g.altitude_units(), str)
    assert g.altitude_units() == 'foot'
    g.gc.remove(
        g.gc.find(".//altitudeUnits").getparent()
    )
    assert g.altitude_units() is None


def test__convert_to_meters(geocov):
    """Test geographicCoverage _convert_to_meters method

    This method should convert the altitude values to meters if they are not
    already in meters. If the altitude units are not specified, the method
    should return None, which is the default value returned by the
    altitude_minimum and altitude_maximum methods. Because this is a method
    of the geographicCoverage class, it is not possible to test it directly
    so we use an instance of geographicCoverage to access the method for
    testing.
    """
    g = geocov[0]
    # Case when no altitude or units are specified in the geographicCoverage
    assert g._convert_to_meters(x=None, from_units=None) is None
    # Case when altitude is specified but no units are specified. Should return value as is.
    assert g._convert_to_meters(x=10, from_units=None) == 10
    # Case when altitude is not specified but units are.
    assert g._convert_to_meters(x=None, from_units="meters") is None
    # Case when altitude is specified and units are specified. Should convert to meters.
    assert g._convert_to_meters(x=10, from_units="foot") == 3.048
