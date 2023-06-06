"""Test the globalelu module."""
import tempfile
import os
import json
from os.path import join, splitext, getsize, getmtime, basename, exists
import glob
import pytest
from spinneret import globalelu
from spinneret import eml


@pytest.fixture
def geocov():
    """A list of GeographicCoverage instances from the test EML file.

    The test EML file is src/spinneret/data/eml/edi.1.1.xml, which contains
    a representative set of user inputs for the identify() function."""
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
                "spatialReference": {
                    "<spatialReference>": "<value>"
                }
            }
        ),
        "esriGeometryPolygon": json.dumps(
            {
                "hasZ": "<true | false>",
                "hasM": "<true | false>",
                "rings": [
                    [
                        ["<x11>", "<y11>", "<z11>", "<m11>"],
                        ["<x1N>", "<y1N>", "<z1N>", "<m1N>"]
                    ],
                    [
                        ["<xk1>", "<yk1>", "<zk1>", "<mk1>"],
                        ["<xkM>", "<ykM>", "<zkM>", "<mkM>"]
                    ]
                ],
                "spatialReference": {"<spatialReference>": "<value>"}
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
                "spatialReference": {
                    "<spatialReference>": "<value>"
                }
            }
        ),
        "unsupported": json.dumps(
            {
                "unsupported": "<unsupported>"
            }
        )
    }
    return geometries


def test_Response_init():
    r = globalelu.Response(json="<json>", geometry="<geometry>")
    assert r.json == "<json>"
    assert r.geometry == "<geometry>"


def test_Location_init():
    # TODO implement test
    assert True


def test_set_identifier():
    # TODO implement test
    assert True


def test_set_description():
    # TODO implement test
    assert True


def test_set_geometry_type():
    # TODO implement test
    assert True


def test_add_comments_location():
    """Test the add_comments method.

    The add_comments method should append a comment to the comments attribute
    of the Location class instance."""
    location = globalelu.Location()
    assert location.data['comments'] == []
    location.add_comments('This is a comment.')
    assert location.data['comments'] == ['This is a comment.']
    location.add_comments('This is another comment.')
    assert location.data['comments'] == ['This is a comment.',
                                         'This is another comment.']


def test_add_ecosystem():
    """Test the add_ecosystem method.

    The add_ecosystem method should append an Ecosystem instance to a location
    class instance's data attribute."""
    location = globalelu.Location()
    ecosystem = globalelu.Ecosystem()
    assert isinstance(location.data['ecosystem'], list)
    assert len(location.data['ecosystem']) == 0
    location.add_ecosystem([ecosystem.data])
    assert isinstance(location.data['ecosystem'][0], dict)
    assert len(location.data['ecosystem']) == 1
    location.add_ecosystem([ecosystem.data])
    assert isinstance(location.data['ecosystem'][1], dict)
    assert len(location.data['ecosystem']) == 2


def test_Ecosystem_init():
    """Test the Ecosystem class __init__ method.

    The Ecosystem class should be initialized with a data attribute containing
    a dictionary with a set of expected names and values for the ecosystem
    component of the data model."""
    ecosystem = globalelu.Ecosystem()
    expected_attributes = ['source', 'version', 'comments', 'attributes']
    assert isinstance(ecosystem.data, dict)
    for attribute in expected_attributes:
        assert attribute in ecosystem.data.keys()
        if attribute == 'comments':
            assert isinstance(ecosystem.data[attribute], list)
        else:
            assert isinstance(ecosystem.data[attribute], None.__class__)


def test_set_source():
    """Test the Ecosystem class set_source method.

    The set_source method should set the source attribute of the Ecosystem
    class instance."""
    ecosystem = globalelu.Ecosystem()
    assert ecosystem.data['source'] is None
    ecosystem.set_source('ecu')
    assert ecosystem.data['source'] == 'ecu'


def test_set_version():
    """Test the Ecosystem class set_version method.

    The set_version method should set the version attribute of the Ecosystem
    class instance."""
    ecosystem = globalelu.Ecosystem()
    assert ecosystem.data['version'] is None
    ecosystem.set_version('1.0')
    assert ecosystem.data['version'] == '1.0'


def test_add_comments_ecosystem():
    """Test the Ecosystem class add_comments method.

    The add_comments method should append a comment to the comments
    attribute of the Ecosystem class instance."""
    ecosystem = globalelu.Ecosystem()
    assert ecosystem.data['comments'] == []
    ecosystem.add_comments('This is a comment.')
    assert ecosystem.data['comments'] == ['This is a comment.']
    ecosystem.add_comments('This is another comment.')
    assert ecosystem.data['comments'] == ['This is a comment.',
                                          'This is another comment.']


def test_Attributes_init():
    """Test the Attributes class __init__ method.

    The Attributes class should be initialized with a data attribute containing
    a dictionary configured with a set of source specific attributes. Each
    attribute should have a corresponding dictionary with label and annotation
    fields."""
    for source in ['wte', 'ecu', 'emu']:
        if source == 'wte':
            attributes = globalelu.Attributes(source='wte')
            expected_attributes = [
                "Temperatur",
                "Moisture",
                "Landcover",
                "Landforms",
                "Climate_Re",
                "ClassName"
            ]
        elif source == 'ecu':
            attributes = globalelu.Attributes(source='ecu')
            expected_attributes = [
                "Slope",
                "Sinuosity",
                "Erodibility",
                "Temperature and Moisture Regime",
                "River Discharge",
                "Wave Height",
                "Tidal Range",
                "Marine Physical Environment",
                "Turbidity",
                "Chlorophyll",
                "CSU_Descriptor"
            ]
        elif source == 'emu':
            attributes = globalelu.Attributes(source='emu')
            expected_attributes = [
                "OceanName",
                "Depth",
                "Temperature",
                "Salinity",
                "Dissolved Oxygen",
                "Nitrate",
                "Phosphate",
                "Silicate",
                "EMU_Descriptor"
            ]
        assert isinstance(attributes.data, dict)
        for attribute in expected_attributes:
            assert attribute in attributes.data.keys()
            assert isinstance(attributes.data[attribute], dict)
            assert 'label' in attributes.data[attribute].keys()
            assert 'annotation' in attributes.data[attribute].keys()
            assert isinstance(attributes.data[attribute]['label'],
                              None.__class__)
            assert isinstance(attributes.data[attribute]['annotation'],
                              None.__class__)


def test_set_wte_attributes(geocov):
    """Test the set_wte_attributes method.

    The set_wte_attributes method should take the data from a WTE identify
    response, parse the components, and set the corresponding values in the
    fields of an Attributes class instance data attribute. These attributes
    should have the expected value types for the label and annotation fields.
    A successful query should return a dictionary with the set of expected
    attributes. An unsuccessful query should return None, with the result of
    not modifying the data attribute of the associated Attributes class
    instance.
    """
    # Successful query
    g = geocov[1]
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        map_server="wte"
    )
    raw_ecosystems = r.get_unique_ecosystems(source='wte')
    for raw_ecosystem in raw_ecosystems:
        attributes = globalelu.Attributes('wte')
        attributes.set_wte_attributes(raw_ecosystem)
        assert len(attributes.data) == 6
        assert isinstance(attributes.data, dict)
        assert attributes.data.keys() == globalelu.Attributes(
            'wte').data.keys()
        for attribute in attributes.data:
            assert isinstance(attributes.data[attribute], dict)
            assert attributes.data[attribute].keys() == \
                   globalelu.Attributes('wte').data[attribute].keys()
            assert attributes.data[attribute]['label'] is not None
            assert attributes.data[attribute]['annotation'] is not None
    # Unsuccessful query
    g = geocov[2]
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        map_server="wte"
    )
    raw_ecosystems = r.get_unique_ecosystems(source='wte')
    attributes = globalelu.Attributes('wte')
    attributes.set_wte_attributes(raw_ecosystems)
    assert attributes.data == globalelu.Attributes('wte').data


def test_set_ecu_attributes(geocov):
    """Test the set_ecu_attributes method.

    The set_ecu_attributes method should take the data from an ECU query
    response, parse the components, and set the corresponding values in the
    fields of an Attributes class instance data attribute. These attributes
    should have the expected value types for the label and annotation fields.
    A successful query should return a dictionary with the set of expected
    attributes. An unsuccessful query should return None, with the result of
    not modifying the data attribute of the associated Attributes class
    instance.
    """
    # Successful query
    g = geocov[8]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="ecu"
    )
    raw_ecosystems = r.get_unique_ecosystems(source='ecu')
    for raw_ecosystem in raw_ecosystems:
        attributes = globalelu.Attributes('ecu')
        attributes.set_ecu_attributes(raw_ecosystem)
        assert isinstance(attributes.data, dict)
        assert len(attributes.data) == 11
        assert attributes.data.keys() == globalelu.Attributes(
            'ecu').data.keys()
        for attribute in attributes.data:
            assert isinstance(attributes.data[attribute], dict)
            assert attributes.data[attribute].keys() == \
                   globalelu.Attributes('ecu').data[attribute].keys()
            assert attributes.data[attribute]['label'] is not None
            assert attributes.data[attribute]['annotation'] is not None
    # Unsuccessful query
    g = geocov[1]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="ecu"
    )
    raw_ecosystems = r.get_unique_ecosystems(source='ecu')
    attributes = globalelu.Attributes('ecu')
    attributes.set_ecu_attributes(raw_ecosystems)
    assert attributes.data == globalelu.Attributes('ecu').data


def test_set_emu_attributes(geocov):
    """Test the set_emu_attributes method.

    The set_emu_attributes method should take the data from an EMU query
    response, parse the components, and set the corresponding values in the
    fields of an Attributes class instance data attribute. These attributes
    should have the expected value types for the label and annotation fields.
    A successful query should return a dictionary with the set of expected
    attributes. An unsuccessful query should return None, with the result of
    not modifying the data attribute of the associated Attributes class
    instance.
    """
    # Successful query
    g = geocov[11]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    raw_ecosystems = r.get_unique_ecosystems(source='emu')
    for raw_ecosystem in raw_ecosystems:
        attributes = globalelu.Attributes('emu')
        attributes.set_emu_attributes(raw_ecosystem)
        assert isinstance(attributes.data, dict)
        assert len(attributes.data) == 9
        assert attributes.data.keys() == globalelu.Attributes(
            'emu').data.keys()
        for attribute in attributes.data:
            assert isinstance(attributes.data[attribute], dict)
            assert attributes.data[attribute].keys() == \
                   globalelu.Attributes('emu').data[attribute].keys()
            assert attributes.data[attribute]['label'] is not None
            assert attributes.data[attribute]['annotation'] is not None
    # Unsuccessful query
    g = geocov[0]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    raw_ecosystems = r.get_unique_ecosystems(source='emu')
    attributes = globalelu.Attributes('emu')
    attributes.set_emu_attributes(raw_ecosystems)
    assert attributes.data == globalelu.Attributes('emu').data


def test_add_attributes():
    """Test the Ecosystem class add_attributes method.

    The add_attributes method should add a dictionary of attributes to the
    data attribute of the Ecosystem class instance, regardless if the
    Attributes class instance is the default or whether it is set with
    attributes from an set_attributes method."""
    ecosystem = globalelu.Ecosystem()
    assert isinstance(ecosystem.data['attributes'], None.__class__)
    attributes = globalelu.Attributes('ecu')
    ecosystem.add_attributes(attributes)
    assert isinstance(ecosystem.data['attributes'], dict)


def test_identify(geocov):
    """Test the identify() function.

    The identify function queries a map service and returns a response object.
    The response object's attributes differ based on the specific map service
    that was queried. This test checks that the response object has an
    ecosystem when queried with a geographic coverage that is known to resolve
    to an ecosystem. This test also checks that the response object has no
    ecosystem when queried with a geographic coverage that is known to not
    resolve to an ecosystem. This test also checks for known edge cases, such
    as when a geographic coverage is outside the extent of the map service.
    """
    # Run an identify operation on the WTE server with a set of geographic
    # coverages known to resolve to a WTE ecosystem.
    geocov_success = [
        geocov[0],  # An envelope on land
        geocov[1]  # A point on land
    ]
    for g in geocov_success:
        r = globalelu.identify(
            geometry=g.to_esri_geometry(),
            map_server="wte",
        )
        assert r is not None
        assert isinstance(r, globalelu.Response)
        assert r.has_ecosystem(source="wte")
    # Run an identify operation on the WTE server with a geographic coverage
    # known to not resolve to a WTE ecosystem, because it is either: a location
    # over the ocean or a freshwater body, an unsupported geometry type (i.e.
    # envelope or polygon), or a location outside the extent of the map
    # service.
    geocov_fail = [
        geocov[2],  # A polygon
        geocov[4],  # A point over the ocean
        geocov[5],  # A point over a freshwater body
        geocov[6]  # A point outside the WTE map service extent
    ]
    for g in geocov_fail:
        r = globalelu.identify(
            geometry=g.to_esri_geometry(),
            map_server="wte"
        )
        assert r is not None
        assert isinstance(r, globalelu.Response)
        assert r.has_ecosystem(source="wte") is False


def test_query(geocov):
    """Test the query() function.

    The query function queries a map service and returns a response object.
    The response object's attributes differ based on the specific map service
    that was queried. This test checks that the response object has a set of
    ecosystems when queried with a geographic coverage that is known to resolve
    to one or more ecosystems. This test also checks that the response object
    has no ecosystems when queried with a geographic coverage that is known to
    not resolve to one or more ecosystems.
    """
    # Query the ECU server with a geographic coverage known to resolve to one
    # or more ECUs.
    geocov_success = [
        geocov[3],  # Polygon
        geocov[7],  # Point
        geocov[8]  # Envelope
    ]
    for g in geocov_success:
        r = globalelu.query(
            geometry=g.to_esri_geometry(),
            map_server="ecu"
        )
        assert r is not None
        expected_attributes = "CSU_Descriptor"  # ECU has one attribute
        attributes = r.get_attributes([expected_attributes])[
            expected_attributes]
        assert isinstance(attributes, list)
        assert isinstance(attributes[0], str)
        assert len(attributes[0]) > 0
    # Query the ECU server with a geographic coverage that is known to
    # not resolve to one or more ECUs.
    g = geocov[0]  # Envelope on land
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="ecu"
    )
    assert r is not None
    assert r.has_ecosystem('ecu') is False

    # Query the EMU server with a geographic coverage known to resolve to one
    # or more EMUs.
    # TODO This test can be combined with the one above, in a for loop, because
    #  the test structures are identical.
    geocov_success = [
        geocov[4],  # Point
        geocov[9],  # Envelope
        geocov[10]  # Polygon
    ]
    for g in geocov_success:
        r = globalelu.query(
            geometry=g.to_esri_geometry(),
            map_server="emu"
        )
        assert r is not None
        r.convert_codes_to_values(source="emu")
        for expected_attribute in ["Name_2018", "OceanName"]:
            attributes = r.get_attributes([expected_attribute])[
                expected_attribute]
            assert isinstance(attributes, list)
            assert isinstance(attributes[0], str)
            assert len(attributes[0]) > 0
    # Query the EMU server with a geographic coverage that is known to
    # not resolve to one or more ECUs.
    g = geocov[0]  # Envelope on land
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    assert r is not None
    assert r.has_ecosystem('emu') is False


def test_get_attributes(geocov):
    """Test the get_attributes() function.

    The get_attributes() function should return a dictionary of attributes
    from the response object. The dictionary should contain the requested
    attributes and return an empty list for attributes that are not present.
    """
    r = globalelu.identify(
        geometry=geocov[0].to_esri_geometry(),
        map_server="wte",
    )
    attributes = ["Landforms", "Landcover", "Climate_Re"]
    res = r.get_attributes(attributes)
    assert isinstance(res, dict)
    for a in attributes:
        assert a in res
        assert len(res[a]) > 0
    res = r.get_attributes(["Not a valid attribute"])
    assert "Not a valid attribute" in res
    assert len(res["Not a valid attribute"]) == 0


# def test_initialize_data_model():
#     """Test the initialize_data_model() function.
#
#     The initialize_data_model() function should return a dictionary with
#     the expected keys. When the with_attributes flag is None, the dictionary
#     should not contain any attributes. When the with_attributes flag is one of
#     the supported types, the dictionary should contain the expected attributes.
#     """
#     # The empty dictionary should contain the expected keys.
#
#     res = globalelu.initialize_data_model()
#     assert isinstance(res, dict)
#     assert set(res.keys()) == {"dataset", "location"}
#     assert res["dataset"] is None
#     assert isinstance(res["location"], list)
#     assert isinstance(res["location"][0], dict)
#     assert res["location"][0]["identifier"] is None
#     assert res["location"][0]["description"] is None
#     assert res["location"][0]["geometry"] is None
#     assert isinstance(res["location"][0]["ecosystem"], list)
#     assert isinstance(res["location"][0]["ecosystem"][0], dict)
#     assert isinstance(res["location"][0]["ecosystem"][0]["comments"], list)
#     assert isinstance(res["location"][0]["ecosystem"][0]["attributes"], dict)
#     # The WTE attributes should be present when the with_attributes flag is
#     # set to "WTE".
#     res = globalelu.initialize_data_model(with_attributes="WTE")
#     attrs = res["location"][0]["ecosystem"][0]["attributes"]
#     assert isinstance(attrs, dict)
#     assert isinstance(attrs["WTE"], dict)
#     assert set(attrs["WTE"].keys()) == {
#         "source_version",
#         "Temperatur",
#         "Moisture",
#         "Landcover",
#         "Landforms",
#         "Climate_Re",
#         "ClassName"
#     }
#     for a in set(attrs["WTE"].keys()):
#         if a is not "source_version":
#             assert isinstance(attrs["WTE"][a], dict)
#             assert set(attrs["WTE"][a].keys()) == {"label", "annotation"}
#             assert attrs["WTE"][a]["label"] is None
#             assert attrs["WTE"][a]["annotation"] is None


def test_convert_point_to_envelope(geocov):
    """Test the convert_point_to_envelope() function.

    The convert_point_to_envelope() function should return an ESRI envelope
    as a JSON string and have a spatial reference of 4326. If a buffer argument
    is not passed, the resulting envelope bounds should equal the point. If a
    buffer argument is passed, the resulting envelope should enclose the point
    within its bounds.
    """
    # Without a buffer
    point = geocov[7].to_esri_geometry()  # A point location
    res = globalelu.convert_point_to_envelope(point)
    assert isinstance(res, str)
    assert point == res

    # With a buffer
    point = geocov[7].to_esri_geometry()  # A point location
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
    polygon = geocov[2].to_esri_geometry()  # Polygon
    res = globalelu.convert_point_to_envelope(polygon)
    assert isinstance(res, str)
    assert polygon == res


def test_has_ecosystem(geocov):
    """Test the has_ecosystem method.

    The has_ecosystem method should return True when the geometry is
    within the WTE area and False when the geometry is outside the WTE area.
    Similarly, the has_ecosystem method should return True when the geometry
    overlaps with an ECU vector and False when the geometry does not overlap
    with an ECU vector. Similarly for EMU.
    """
    # Geometries over land areas have a WTE ecosystem
    g = geocov[1]
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        map_server="wte"
    )
    assert r.has_ecosystem('wte') is True
    # Geometries over water bodies, or outside the WTE area, don't have a WTE
    # ecosystem.
    geocov_ecu = [geocov[4], geocov[6]]
    for g in geocov_ecu:
        r = globalelu.identify(
            geometry=g.to_esri_geometry(),
            map_server="wte"
        )
        assert r.has_ecosystem('wte') is False

    # Geometries near the coast have a ECU ecosystem
    g = geocov[7]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="ecu"
    )
    assert r.has_ecosystem('ecu') is True
    # Geometries far from the coast don't have a ECU ecosystem
    g = geocov[0]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="ecu"
    )
    assert r.has_ecosystem('ecu') is False

    # Geometries on the ocean have an EMU ecosystem
    g = geocov[4]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    assert r.has_ecosystem('emu') is True
    # Geometries on land don't have an EMU ecosystem
    g = geocov[0]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    assert r.has_ecosystem('emu') is False


def test_get_wte_ecosystems(geocov):
    """Test the get_wte_ecosystems method.

    A successful query should return a non-empty list of WTE ecosystems. An
    unsuccessful query should return an empty list.
    """
    # Successful query
    g = geocov[1]
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        map_server="wte"
    )
    ecosystems = r.get_wte_ecosystems()
    assert isinstance(ecosystems, list)
    assert len(ecosystems) > 0
    # Unsuccessful query
    g = geocov[2]
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        map_server="wte"
    )
    ecosystems = r.get_wte_ecosystems()
    assert isinstance(ecosystems, list)
    assert len(ecosystems) == 0


def test_get_ecu_ecosystems(geocov):
    """Test the get_ecu_ecosystems() function

    A successful query should return a non-empty list of ECU ecosystems. An
    unsuccessful query should return an empty list.
    """
    # Successful query
    g = geocov[8]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="ecu"
    )
    ecosystems = r.get_ecu_ecosystems()
    assert isinstance(ecosystems, list)
    assert len(ecosystems) > 0
    # Unsuccessful query
    g = geocov[1]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="ecu"
    )
    ecosystems = r.get_ecu_ecosystems()
    assert isinstance(ecosystems, list)
    assert len(ecosystems) == 0


def test_get_emu_ecosystems(geocov):
    """Test the get_emu_ecosystems() method

    A successful query should return a non-empty list of EMU ecosystems. An
    unsuccessful query should return an empty list.
    """
    # A series of successful queries
    g = geocov[11]  # Point
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    ecosystems = r.get_emu_ecosystems()
    assert isinstance(ecosystems, list)
    assert len(ecosystems) == 1
    g = geocov[9]  # Envelope
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    ecosystems = r.get_emu_ecosystems()
    assert isinstance(ecosystems, list)
    assert len(ecosystems) == 4
    g = geocov[10]  # Polygon
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    ecosystems = r.get_emu_ecosystems()
    assert isinstance(ecosystems, list)
    assert len(ecosystems) == 7

    # Unsuccessful query
    g = geocov[1]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    ecosystems = r.get_emu_ecosystems()
    assert isinstance(ecosystems, list)
    assert len(ecosystems) == 0


def test_get_unique_ecosystems(geocov):
    """Test the get_unique_ecosystems method.

    The get_unique_ecosystems method should return a set of unique ecosystems
    contained in a given server response object. The way ecosystems are
    expressed by each server (in JSON format) differs, so the function should
    be capable of recognizing the format and parsing it accordingly. The set
    object returned by the get_unique_ecosystems method enables iterative
    parsing of the contents by the builder routine of the get_wte_ecosystems
    and get_ecu_ecosystems methods of the Response object. Note, currently,
    the identify operation used to query the WTE server does not return more
    than one ecosystem per query.
    """
    # Test a successful response from the WTE server identify operation (i.e.
    # a response an ecosystem).
    g = geocov[1]
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        map_server="wte"
    )
    unique_ecosystems = r.get_unique_ecosystems(source='wte')
    assert isinstance(unique_ecosystems, list)
    assert len(unique_ecosystems) == len(r.json.get("results"))
    assert len(unique_ecosystems) == 1
    # Test an unsuccessful response from the wte server identify operation
    # (i.e. a response that contains no ecosystem).
    g = geocov[2]
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        map_server="wte"
    )
    unique_ecosystems = r.get_unique_ecosystems(source='wte')
    assert isinstance(unique_ecosystems, list)
    assert len(unique_ecosystems) == 0

    # Test a successful response from the ECU server query (i.e. a response
    # that contains one or more ecosystems).
    g = geocov[8]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="ecu"
    )
    full_list_of_ecosystems = r.get_attributes(["CSU_Descriptor"])[
        "CSU_Descriptor"]
    unique_ecosystems = r.get_unique_ecosystems(source='ecu')
    assert isinstance(unique_ecosystems, list)
    assert len(full_list_of_ecosystems) == 123
    assert len(unique_ecosystems) == 34
    assert unique_ecosystems == list(set(full_list_of_ecosystems))
    # Test an unsuccessful response from the ECU server query (i.e. a response
    # that contains no ecosystems).
    g = geocov[1]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="ecu"
    )
    full_list_of_ecosystems = r.get_attributes(["CSU_Descriptor"])[
        "CSU_Descriptor"]
    unique_ecosystems = r.get_unique_ecosystems(source='ecu')
    assert isinstance(unique_ecosystems, list)
    assert len(full_list_of_ecosystems) == 0
    assert len(unique_ecosystems) == 0
    assert unique_ecosystems == list(set(full_list_of_ecosystems))

    # Test a successful response from the EMU server query (i.e. a response
    # that contains one or more ecosystems).
    g = geocov[11]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    # FIXME? This test differs from those for WTE and ECU because the get
    #  unique ecosystems operation is wrapped in two. See implementation for
    #  details.
    # full_list_of_ecosystems = r.json.get("features")
    unique_ecosystems = r.get_unique_ecosystems(source='emu')
    assert isinstance(unique_ecosystems, list)
    # assert len(full_list_of_ecosystems) == 1
    assert len(unique_ecosystems) == 1
    # assert unique_ecosystems == list(set(full_list_of_ecosystems))
    # Test an unsuccessful response from the EMU server query (i.e. a response
    # that contains no ecosystems).
    g = geocov[0]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    # full_list_of_ecosystems = r.get_attributes(["CSU_Descriptor"])[
    #     "CSU_Descriptor"]
    unique_ecosystems = r.get_unique_ecosystems(source='emu')
    assert isinstance(unique_ecosystems, list)
    # assert len(full_list_of_ecosystems) == 0
    assert len(unique_ecosystems) == 0
    # assert unique_ecosystems == list(set(full_list_of_ecosystems))


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
        globalelu.eml_to_wte_json(eml_dir="src/spinneret/data/eml/",
                                  output_dir=tmpdir)
        fpaths_out = os.listdir(tmpdir)
        for f in fnames_in:
            assert f + ".json" in fpaths_out
            assert getsize(join(tmpdir, f + ".json")) > 0

        # When an EML file is missing a corresponding json file, the
        # eml_to_wte_json() function should fill the gap by creating the json
        # file.
        os.remove(join(tmpdir, fnames_in[0] + ".json"))
        assert exists(join(tmpdir, fnames_in[0] + ".json")) is False
        globalelu.eml_to_wte_json(eml_dir="src/spinneret/data/eml/",
                                  output_dir=tmpdir)
        assert exists(join(tmpdir, fnames_in[0] + ".json")) is True

        # Additionally, existing json files should not be overwritten
        # unless the overwrite flag is set to True.
        # Get date and time of existing json files
        dates = {}
        for f in fnames_in:
            dates[f] = getmtime(join(tmpdir, f + ".json"))
        # Run the function again without overwriting existing json files
        globalelu.eml_to_wte_json(eml_dir="src/spinneret/data/eml/",
                                  output_dir=tmpdir)
        for f in fnames_in:
            assert getmtime(join(tmpdir, f + ".json")) == dates[f]
        # Run the function again with overwriting existing json files
        globalelu.eml_to_wte_json(
            eml_dir="src/spinneret/data/eml/", output_dir=tmpdir,
            overwrite=True
        )
        for f in fnames_in:
            assert getmtime(join(tmpdir, f + ".json")) != dates[f]


def test_eml_to_wte_json_wte_envelope(geocov):
    """Test the eml_to_wte_json() function with a WTE envelope."""

    # FIXME: This test is a temporary approach to testing how envelopes are
    #  handled by the ecosystem lookup on the WTE server. It is essentially a
    #  manual integration test, and will be removed in the future.
    g = geocov[0]  # Envelope encompassing multiple ecosystems
    geometry = g.to_esri_geometry()
    ecosystems_in_envelope = []
    points = globalelu._polygon_or_envelope_to_points(geometry)
    for point in points:
        try:
            r = globalelu.identify(
                geometry=point,
                map_server="wte"
            )
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

    g = geocov[3]  # Polygon encompassing multiple ecosystems
    geometry = g.to_esri_geometry()
    ecosystems_in_envelope = []
    points = globalelu._polygon_or_envelope_to_points(geometry)
    for point in points:
        try:
            r = globalelu.identify(
                geometry=point,
                map_server="wte"
            )
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


def test_convert_codes_to_values(geocov):
    """Test the convert_codes_to_values method.

    Codes listed in the response object should be converted to their string
    value equivalents."""
    # Test a successful response from the EMU server query operation.
    g = geocov[4]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    # Codes are numeric values in the response object initially.
    for feature in r.json.get("features"):
        assert isinstance(feature.get("attributes").get("Name_2018"), int)
        assert isinstance(feature.get("attributes").get("OceanName"), int)
    # Codes are string values in the response object after conversion.
    r.convert_codes_to_values(source="emu")
    for feature in r.json.get("features"):
        assert isinstance(feature.get("attributes").get("Name_2018"), str)
        assert isinstance(feature.get("attributes").get("OceanName"), str)

    # Test an unsuccessful response from the EMU server query operation.
    g = geocov[0]  # Location on land
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )
    # The response object's features list is empty and therefore a no-op.
    assert isinstance(r.json.get("features"), list)
    assert len(r.json.get("features")) == 0


def test_get_ecosystems_for_geometry_z_values(geocov):
    """Test the get_ecosystems_for_geometry method.

    When a geometry has a single z value (i.e. discrete depth) the
    get_ecosystems_for_geometry_z_values method should return any EMUs
    intersecting with the z value, including both bounding EMUs when the z
    value equals the boundary between the 2 EMUs. When a geometry has 2 z
    values (i.e. range of depths) the method should return any EMUs
    intersecting with the range, including both bounding EMUs when the z value
    equals the boundary between the 2 EMUs. When a geometry has no z values
    (i.e. no depth) the method should return all EMUs.

    Rather than using a set of geographic coverage fixtures, each exemplifying
    the scenarios, we reduce the number of API calls to the EMU server by
    modifying the z values of the response objects geometry attribute.

    The results of the assertions were determined by visual inspection of the
    EMU server map service interface at the geographic coverage represented in
    the test fixture. Or rather the test fixture was set based on a specific
    data point in the EMU server map service interface.
    """
    # A set of tests on a point location with z values
    g = geocov[11]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        map_server="emu"
    )

    # Single z value within EMU returns one EMU
    geometry = json.loads(r.geometry)
    geometry["zmin"] = -15
    geometry["zmax"] = -15
    r.geometry = json.dumps(geometry)
    ecosystems = r.get_ecosystems_for_geometry_z_values(source="emu")
    expected_ecosystems = {18}
    assert isinstance(ecosystems, list)
    for ecosystem in ecosystems:
        assert isinstance(ecosystem, str)
        assert json.loads(ecosystem)['attributes'][
                   'Name_2018'] in expected_ecosystems
    assert len(ecosystems) == 1

    # Single z value on the bounder between two EMUs returns two EMUs
    geometry = json.loads(r.geometry)
    geometry["zmin"] = -30
    geometry["zmax"] = -30
    r.geometry = json.dumps(geometry)
    ecosystems = r.get_ecosystems_for_geometry_z_values(source="emu")
    expected_ecosystems = {18, 24}
    assert isinstance(ecosystems, list)
    for ecosystem in ecosystems:
        assert isinstance(ecosystem, str)
        assert json.loads(ecosystem)['attributes'][
                   'Name_2018'] in expected_ecosystems
    assert len(ecosystems) == 2

    # Range of z values each intersecting with the midpoints of two
    #  adjacent EMUs returns two EMUs
    geometry = json.loads(r.geometry)
    geometry["zmin"] = -90
    geometry["zmax"] = -15
    r.geometry = json.dumps(geometry)
    ecosystems = r.get_ecosystems_for_geometry_z_values(source="emu")
    expected_ecosystems = {18, 24}
    assert isinstance(ecosystems, list)
    for ecosystem in ecosystems:
        assert isinstance(ecosystem, str)
        assert json.loads(ecosystem)['attributes'][
                   'Name_2018'] in expected_ecosystems
    assert len(ecosystems) == 2

    # Range of z values on boundaries of two adjacent EMUs returns 3 EMUs
    geometry = json.loads(r.geometry)
    geometry["zmin"] = -150
    geometry["zmax"] = -30
    r.geometry = json.dumps(geometry)
    ecosystems = r.get_ecosystems_for_geometry_z_values(source="emu")
    expected_ecosystems = {18, 24, 11}
    assert isinstance(ecosystems, list)
    for ecosystem in ecosystems:
        assert isinstance(ecosystem, str)
        assert json.loads(ecosystem)['attributes'][
                   'Name_2018'] in expected_ecosystems
    assert len(ecosystems) == 3

    # No z values returns all EMUs.
    # z = None
    geometry = json.loads(r.geometry)
    geometry["zmin"] = None
    geometry["zmax"] = None
    r.geometry = json.dumps(geometry)
    ecosystems = r.get_ecosystems_for_geometry_z_values(source="emu")
    expected_ecosystems = {18, 24, 11, 26, 8, 19}
    assert isinstance(ecosystems, list)
    for ecosystem in ecosystems:
        assert isinstance(ecosystem, str)
        assert json.loads(ecosystem)['attributes'][
                   'Name_2018'] in expected_ecosystems
    assert len(ecosystems) == 6


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
            "spatialReference": {
                "<spatialReference>": "<value>"
            }
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
            "spatialReference": {
                "<spatialReference>": "<value>"
            }
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
                    ["<x1N>", "<y1N>", "<z1N>", "<m1N>"]
                ],
                [
                    ["<xk1>", "<yk1>", "<zk1>", "<mk1>"],
                    ["<xkM>", "<ykM>", "<zkM>", "<mkM>"]
                ]
            ],
            "spatialReference": {"<spatialReference>": "<value>"}
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
    g = geocov[0]
    geometry = g.to_esri_geometry()
    points = globalelu._polygon_or_envelope_to_points(geometry)
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
            geometry_dict["ymax"]
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
    g = geocov[3]
    geometry = g.to_esri_geometry()
    points = globalelu._polygon_or_envelope_to_points(geometry)
    # The method returns a list of 4 points
    assert isinstance(points, list)
    assert len(points) == 4
    # First 3 points equal the vertices of the polygon
    geometry_dict = json.loads(geometry)
    geometry_corners = set([item for sublist in geometry_dict["rings"][0] for item in sublist])
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

