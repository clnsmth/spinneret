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

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert geocov[0].to_esri_geometry() == dumps(
        {
            "xmin": -123.552,
            "ymin": 39.804,
            "xmax": -120.83,
            "ymax": 40.441,
            "spatialReference": {"wkid": 4326},
        }
    )
    assert geocov[1].to_esri_geometry() == dumps(
        {
            "x": -72.22,
            "y": 42.48,
            "spatialReference": {"wkid": 4326},
        }
    )
    assert geocov[2].to_esri_geometry() == dumps(
        {
            "rings": [
                [[-123.7976226, 39.3085666], [-123.8222818, 39.3141049], [-123.8166231, 39.2943269], [-123.7976226, 39.3085666]],
                [[-123.8078563, 39.3068951], [-123.8163387, 39.3086898], [-123.813222, 39.3022756], [-123.8078177, 39.3068354], [-123.8078563, 39.3068951]]
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
    geocov[0].gc.remove(geocov[0].gc.find(".//westBoundingCoordinate").getparent())
    assert geocov[0].west() is None


def test_east(geocov):
    """Test geographicCoverage east method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].east(), float)
    geocov[0].gc.remove(geocov[0].gc.find(".//eastBoundingCoordinate").getparent())
    assert geocov[0].east() is None


def test_north(geocov):
    """Test geographicCoverage north_bounding_coordinate method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].north(), float)
    geocov[0].gc.remove(geocov[0].gc.find(".//northBoundingCoordinate").getparent())
    assert geocov[0].north() is None


def test_south(geocov):
    """Test geographicCoverage south_bounding_coordinate method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[0].south(), float)
    geocov[0].gc.remove(geocov[0].gc.find(".//southBoundingCoordinate").getparent())
    assert geocov[0].south() is None


def test_outer_gring(geocov):
    """Test geographicCoverage outer_gring method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert isinstance(geocov[2].outer_gring(), str)
    geocov[2].gc.remove(geocov[2].gc.find(".//datasetGPolygonOuterGRing").getparent())
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
