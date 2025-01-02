"""Tests for the utilities module."""
import json
import pytest
from spinneret import globalelu
from spinneret import eml
from spinneret.utilities import _polygon_or_envelope_to_points


@pytest.fixture
def geocov():
    """A list of GeographicCoverage instances from the test EML file."""
    res = eml.get_geographic_coverage(eml="src/spinneret/data/eml/edi.1.1.xml")
    return res


@pytest.fixture
def geometry_shapes():
    """A list of ESRI geometries."""
    geometries = {
        "esriGeometryPoint": json.dumps(
            {
                "x": "<x>",
                "y": "<y>",
                "z": "<z>",
                "m": "<m>",
                "spatialReference": {"<spatialReference>": "<value>"},
            }
        ),
        "esriGeometryPolygon": json.dumps(
            {
                "hasZ": "<true | false>",
                "hasM": "<true | false>",
                "rings": [
                    [
                        ["<x11>", "<y11>", "<z11>", "<m11>"],
                        ["<x1N>", "<y1N>", "<z1N>", "<m1N>"],
                    ],
                    [
                        ["<xk1>", "<yk1>", "<zk1>", "<mk1>"],
                        ["<xkM>", "<ykM>", "<zkM>", "<mkM>"],
                    ],
                ],
                "spatialReference": {"<spatialReference>": "<value>"},
            }
        ),
        "esriGeometryEnvelope": json.dumps(
            {
                "xmin": "<xmin>",
                "ymin": "<ymin>",
                "xmax": "<xmax>",
                "ymax": "<ymax>",
                "zmin": "<zmin>",
                "zmax": "<zmax>",
                "mmin": "<mmin>",
                "mmax": "<mmax>",
                "spatialReference": {"<spatialReference>": "<value>"},
            }
        ),
        "unsupported": json.dumps({"unsupported": "<unsupported>"}),
    }
    return geometries


def test_convert_point_to_envelope(geocov):
    """Test the convert_point_to_envelope() function.

    The convert_point_to_envelope() function should return an ESRI envelope
    as a JSON string and have a spatial reference of 4326. If a buffer argument
    is not passed, the resulting envelope bounds should equal the point. If a
    buffer argument is passed, the resulting envelope should enclose the point
    within its bounds.
    """
    # Without a buffer
    point = geocov[7].to_esri_geometry()  # A point location  # TODO convert to esri geometry fixture, because we don't want EML related operations in the package
    res = globalelu.convert_point_to_envelope(point)
    assert isinstance(res, str)
    assert point == res

    # With a buffer
    point = geocov[7].to_esri_geometry()  # A point location  # TODO convert to esri geometry fixture, because we don't want EML related operations in the package
    res = globalelu.convert_point_to_envelope(point, buffer=0.5)
    assert isinstance(res, str)
    assert point != res
    point = json.loads(point)  # Convert to dict for comparison
    res = json.loads(res)
    assert point["xmin"] > res["xmin"]
    assert point["xmax"] < res["xmax"]
    assert point["ymin"] > res["ymin"]
    assert point["ymax"] < res["ymax"]
    assert res["spatialReference"]["wkid"] == 4326

    # Other geometries are unchanged
    polygon = geocov[2].to_esri_geometry()  # Polygon  # TODO convert to esri geometry fixture, because we don't want EML related operations in the package
    res = globalelu.convert_point_to_envelope(polygon)
    assert isinstance(res, str)
    assert polygon == res


def test__get_geometry_type(geometry_shapes):
    """Test the _get_geometry_type method.

    The _get_geometry_type method should return the ESRI geometry type if it is
    supported, otherwise it should return None.
    """
    # Point
    geom = geometry_shapes["esriGeometryPoint"]
    assert globalelu._get_geometry_type(geom) == "esriGeometryPoint"
    # Polygon
    geom = geometry_shapes["esriGeometryPolygon"]
    assert globalelu._get_geometry_type(geom) == "esriGeometryPolygon"
    # Envelope
    geom = geometry_shapes["esriGeometryEnvelope"]
    assert globalelu._get_geometry_type(geom) == "esriGeometryEnvelope"
    # Unsupported
    geom = geometry_shapes["unsupported"]
    assert globalelu._get_geometry_type(geom) is None


def test__is_point_location():
    """Test the _is_point_location method.

    The _is_point_location method should return True if the geometry is a
    point, otherwise it should return False.
    """
    # Envelope is actually a point
    point = json.dumps(
        {
            "xmin": -72.22,
            "ymin": 42.48,
            "xmax": -72.22,
            "ymax": 42.48,
            "spatialReference": {"<spatialReference>": "<value>"},
        }
    )
    assert globalelu._is_point_location(point) is True

    # Envelope is an envelope
    envelope = json.dumps(
        {
            "xmin": -123.552,
            "ymin": 39.804,
            "xmax": -120.830,
            "ymax": 40.441,
            "spatialReference": {"<spatialReference>": "<value>"},
        }
    )
    assert globalelu._is_point_location(envelope) is False

    # Other geometry types are not analyzed and return False
    polygon = json.dumps(
        {
            "hasZ": "<true | false>",
            "hasM": "<true | false>",
            "rings": [
                [
                    ["<x11>", "<y11>", "<z11>", "<m11>"],
                    ["<x1N>", "<y1N>", "<z1N>", "<m1N>"],
                ],
                [
                    ["<xk1>", "<yk1>", "<zk1>", "<mk1>"],
                    ["<xkM>", "<ykM>", "<zkM>", "<mkM>"],
                ],
            ],
            "spatialReference": {"<spatialReference>": "<value>"},
        }
    )
    assert globalelu._is_point_location(polygon) is False


def test__polygon_or_envelope_to_points(geocov):
    """Test the _polygon_or_envelope_to_points method.

    The _polygon_or_envelope_to_points method should return a list of points
    that represent the vertices of the polygon or envelope in addition to the
    centroid.
    """
    # Test an envelope
    g = geocov[0]  # TODO convert to esri geometry fixture, because we don't want EML related operations in the package
    geometry = g.to_esri_geometry()
    points = _polygon_or_envelope_to_points(geometry)
    # The method returns a list of 5 points
    assert isinstance(points, list)
    assert len(points) == 5
    # First 4 points equal the corners of the envelope
    geometry_dict = json.loads(geometry)
    geometry_corners = set(
        [
            geometry_dict["xmin"],
            geometry_dict["ymin"],
            geometry_dict["xmax"],
            geometry_dict["ymax"],
        ]
    )
    for i in [0, 1, 2, 3]:
        assert isinstance(points[i], str)
        point = json.loads(points[i])
        # Min and max values are equal for points
        assert point["xmin"] == point["xmax"]
        assert point["ymin"] == point["ymax"]
        # The point is a corner of the envelope
        assert point["xmin"] in geometry_corners
        assert point["ymin"] in geometry_corners
        # Spatial reference and z values are not modified by this method
        assert point["spatialReference"] == geometry_dict["spatialReference"]
        assert point["zmin"] == geometry_dict["zmin"]
        assert point["zmax"] == geometry_dict["zmax"]
    # The last point is the centriod of the envelope and passes the same tests
    # as the first 4 points. Note, this equivalence testing against the prior
    # 4 points is needed because the method handling the 5 is different and
    # we want to ensure that the same tests are applied.
    assert isinstance(points[4], str)
    point = json.loads(points[4])
    # Min and max values are equal for points
    assert point["xmin"] == point["xmax"]
    assert point["ymin"] == point["ymax"]
    # The point is the midpoint of the envelope (centroid)
    assert point["xmin"] == (geometry_dict["xmin"] + geometry_dict["xmax"]) / 2
    assert point["ymin"] == (geometry_dict["ymin"] + geometry_dict["ymax"]) / 2
    # Spatial reference and z values are not modified by this method
    assert point["spatialReference"] == geometry_dict["spatialReference"]
    assert point["zmin"] == geometry_dict["zmin"]
    assert point["zmax"] == geometry_dict["zmax"]

    # Test a polygon
    g = geocov[3]  # TODO convert to esri geometry fixture, because we don't want EML related operations in the package
    geometry = g.to_esri_geometry()
    points = _polygon_or_envelope_to_points(geometry)
    # The method returns a list of 4 points
    assert isinstance(points, list)
    assert len(points) == 4
    # First 3 points equal the vertices of the polygon
    geometry_dict = json.loads(geometry)
    geometry_corners = set(
        [item for sublist in geometry_dict["rings"][0] for item in sublist]
    )
    for i in [0, 1, 2]:
        assert isinstance(points[i], str)
        point = json.loads(points[i])
        # Min and max values are equal for points
        assert point["xmin"] == point["xmax"]
        assert point["ymin"] == point["ymax"]
        # The point is a vertice of the polygon
        assert point["xmin"] in geometry_corners
        assert point["ymin"] in geometry_corners
        # Spatial reference is not modified by this method
        assert point["spatialReference"] == geometry_dict["spatialReference"]
    # The last point is the centriod of the polygon and passes the same tests
    # as the first 3 points. Note, this equivalence testing against the prior
    # 3 points is needed because the method handling the 4 is different and
    # we want to ensure that the same tests are applied.
    assert isinstance(points[3], str)
    point = json.loads(points[3])
    # Min and max values are equal for points
    assert point["xmin"] == point["xmax"]
    assert point["ymin"] == point["ymax"]
    # The centroid point is somewhere between the x and y bounds of the polygon
    xbounds = [item[0] for item in geometry_dict["rings"][0]]
    ybounds = [item[1] for item in geometry_dict["rings"][0]]
    assert point["xmin"] > min(xbounds) and point["xmin"] < max(xbounds)
    assert point["ymin"] > min(ybounds) and point["ymin"] < max(ybounds)
    # Spatial reference and z values are not modified by this method
    assert point["spatialReference"] == geometry_dict["spatialReference"]
