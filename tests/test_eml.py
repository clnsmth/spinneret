"""Tests for the eml module."""
import json
import tempfile
import os
from os.path import join, splitext, getsize, getmtime, basename, exists
import glob
from json import dumps
import pytest
from unittest.mock import patch
from spinneret import eml, geoenv, utilities



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
    g = geocov[0]  # An envelope without units
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
    g = geocov[1]  # A point without units
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
    g = geocov[11]  # A point with units
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
    g = geocov[2]
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


def test_altitude_minimum(geocov):
    g = geocov[11]  # A geographic coverage with altitudes in meters
    assert isinstance(g.altitude_minimum(), float)
    assert g.altitude_minimum() == -15
    # The _convert_to_meters method should be called when the to_meters
    # argument is True.
    with patch(
        "spinneret.eml.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_minimum(to_meters=True)
        mock__convert_to_meters.assert_called_once()
    # The _convert_to_meters method should not be called when the to_meters
    # argument is False.
    with patch(
        "spinneret.eml.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_minimum(to_meters=False)
        mock__convert_to_meters.assert_not_called()
    # Returns None when no altitudeMinimum element is present.
    g.gc.remove(g.gc.find(".//altitudeMinimum").getparent())
    assert g.altitude_minimum() is None


def test_altitude_maximum(geocov):
    g = geocov[11]  # A geographic coverage with altitudes in meters
    assert isinstance(g.altitude_maximum(), float)
    assert g.altitude_maximum() == 0
    # The _convert_to_meters method should be called when the to_meters
    # argument is True.
    with patch(
        "spinneret.eml.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_maximum(to_meters=True)
        mock__convert_to_meters.assert_called_once()
    # The _convert_to_meters method should not be called when the to_meters
    # argument is False.
    with patch(
        "spinneret.eml.GeographicCoverage._convert_to_meters"
    ) as mock__convert_to_meters:
        g.altitude_maximum(to_meters=False)
        mock__convert_to_meters.assert_not_called()
    # Returns None when no altitudeMinimum element is present.
    g.gc.remove(g.gc.find(".//altitudeMaximum").getparent())
    assert g.altitude_maximum() is None


def test_altitude_units(geocov):
    g = geocov[11]  # A geographic coverage with altitude in units of feet
    assert isinstance(g.altitude_units(), str)
    assert g.altitude_units() == "meter"
    g.gc.remove(g.gc.find(".//altitudeUnits").getparent())
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


def test_eml_to_wte_json():
    """Test the eml_to_wte_json() function.

    Each EML file in the src/spinneret/data/eml/ directory should be converted
    to a json file and saved to an output directory. When an EML file is
    missing, the eml_to_wte_json() function should fill the gap by creating
    the json file. Additionally, existing json files should not be overwritten
    unless the overwrite flag is set to True.

    Note, fixtures of the json files cannot be used to test against because
    set operations are frequently used in the eml_to_wte_json() subroutines,
    which do not preserve order, and hence the fixture always be
    different from the output of the eml_to_wte_json() function, except by
    random chance.
    """
    fpaths_in = glob.glob("src/spinneret/data/eml/" + "*.xml")
    fnames_in = [splitext(basename(f))[0] for f in fpaths_in]
    with tempfile.TemporaryDirectory() as tmpdir:
        # Each EML file in the src/spinneret/data/eml/ directory should be
        # converted to a json file and saved to an output directory.
        eml.eml_to_wte_json(eml_dir="src/spinneret/data/eml/", output_dir=tmpdir)
        fpaths_out = os.listdir(tmpdir)
        for f in fnames_in:
            assert f + ".json" in fpaths_out
            assert getsize(join(tmpdir, f + ".json")) > 0

        # When an EML file is missing a corresponding json file, the
        # eml_to_wte_json() function should fill the gap by creating the json
        # file.
        os.remove(join(tmpdir, fnames_in[0] + ".json"))
        assert exists(join(tmpdir, fnames_in[0] + ".json")) is False
        eml.eml_to_wte_json(eml_dir="src/spinneret/data/eml/", output_dir=tmpdir)
        assert exists(join(tmpdir, fnames_in[0] + ".json")) is True

        # Additionally, existing json files should not be overwritten
        # unless the overwrite flag is set to True.
        # Get date and time of existing json files
        dates = {}
        for f in fnames_in:
            dates[f] = getmtime(join(tmpdir, f + ".json"))
        # Run the function again without overwriting existing json files
        eml.eml_to_wte_json(eml_dir="src/spinneret/data/eml/", output_dir=tmpdir)
        for f in fnames_in:
            assert getmtime(join(tmpdir, f + ".json")) == dates[f]
        # Run the function again with overwriting existing json files
        eml.eml_to_wte_json(
            eml_dir="src/spinneret/data/eml/", output_dir=tmpdir, overwrite=True
        )
        for f in fnames_in:
            assert getmtime(join(tmpdir, f + ".json")) != dates[f]


def test_eml_to_wte_json_wte_envelope(geocov):
    """Test the eml_to_wte_json() function with a WTE envelope."""

    # FIXME: This test is a temporary approach to testing how envelopes are
    #  handled by the ecosystem lookup on the WTE server. It is essentially a
    #  manual integration test, and will be removed in the future.
    g = geocov[0]  # Envelope encompassing multiple ecosystems  # TODO convert to esri geometry fixture, because we don't want EML related operations in the package
    geometry = g.to_esri_geometry()
    ecosystems_in_envelope = []
    points = utilities._polygon_or_envelope_to_points(geometry)
    for point in points:
        try:
            r = geoenv.identify(geometry=point, map_server="wte")
        except ConnectionError:
            r = None
        if r is not None:
            # Build the ecosystem object and add it to the location.
            if r.has_ecosystem(source="wte"):
                ecosystems = r.get_ecosystems(source="wte")
                # TODO Implement a uniquing function to handle this edge case
                #  after geometry type passing is finalized, which may negate
                #  the need for this edge case handling.
                ecosystems_in_envelope.append(json.dumps(ecosystems[0]))
    ecosystems_in_envelope = list(set(ecosystems_in_envelope))
    ecosystems_in_envelope = [json.loads(e) for e in ecosystems_in_envelope]
    # TODO (end TODO) -----------------------------------------------
    assert len(ecosystems_in_envelope) == 4
    for item in ecosystems_in_envelope:
        assert isinstance(item, dict)

    # TODO refactor this test according to any changes made above. This is a
    #  copy.

    g = geocov[3]  # Polygon encompassing multiple ecosystems  # TODO convert to esri geometry fixture, because we don't want EML related operations in the package
    geometry = g.to_esri_geometry()
    ecosystems_in_envelope = []
    points = utilities._polygon_or_envelope_to_points(geometry)
    for point in points:
        try:
            r = geoenv.identify(geometry=point, map_server="wte")
        except ConnectionError:
            r = None
        if r is not None:
            # Build the ecosystem object and add it to the location.
            if r.has_ecosystem(source="wte"):
                ecosystems = r.get_ecosystems(source="wte")
                # TODO Implement a uniquing function to handle this edge case
                #  after geometry type passing is finalized, which may negate
                #  the need for this edge case handling.
                ecosystems_in_envelope.append(json.dumps(ecosystems[0]))
    ecosystems_in_envelope = list(set(ecosystems_in_envelope))
    ecosystems_in_envelope = [json.loads(e) for e in ecosystems_in_envelope]
    # TODO (end TODO) -----------------------------------------------
    assert len(ecosystems_in_envelope) == 1
    for item in ecosystems_in_envelope:
        assert isinstance(item, dict)