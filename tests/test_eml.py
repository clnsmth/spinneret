"""Tests for the eml module."""
import pytest
from spinneret import eml


@pytest.fixture
def geocov():
    """A list of GeographicCoverage instances from the test EML file."""
    res = eml.get_geographic_coverage(eml="../src/spinneret/data/eml/edi.1.1.xml")
    return res


def test_get_geographic_coverage():
    """Test get_geographic_coverage function."""
    res = eml.get_geographic_coverage(eml="../src/spinneret/data/eml/edi.1.1.xml")
    assert type(res) == list
    for item in res:
        assert type(item) == eml.GeographicCoverage


def test_geom_type(geocov):
    """Test geographicCoverage _geom_type method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert geocov[0]._geom_type() == "envelope"
    assert geocov[1]._geom_type() == "point"
    assert geocov[2]._geom_type() == "polygon"


def test_to_esri_geometry(geocov):
    """Test geographicCoverage to_esri_geometry method

    This is a fixture based on the contents of edi.1.1.xml. This fixture
    should be updated whenever that files geographicCoverage changes.
    """
    assert geocov[0].to_esri_geometry() == {
        "xmin": -72.22,
        "ymin": 42.47,
        "xmax": -72.21,
        "ymax": 42.48,
        "spatialReference": {"wkid": 4326},
    }
    assert geocov[1].to_esri_geometry() == {
        "x": -72.22,
        "y": 42.48,
        "spatialReference": {"wkid": 4326},
    }
    assert geocov[2].to_esri_geometry() == {
        "rings": [
            [[-119.453, 35.0], [-125.0, 37.5555], [-122.0, 40.0], [-119.453, 35.0]],
            [[-120.453, 36.0], [-124.0, 37.5555], [-122.0, 39.0], [-120.453, 36.0]],
        ],
        "spatialReference": {"wkid": 4326},
    }
