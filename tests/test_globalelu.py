"""Test the globalelu module."""
from difflib import ndiff
import filecmp
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


def test_Location_init():
    assert False


def test_set_identifier():
    assert False


def test_set_description():
    assert False


def test_set_geometry_type():
    assert False


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
    location.add_ecosystem(ecosystem)
    assert isinstance(location.data['ecosystem'][0], dict)
    assert len(location.data['ecosystem']) == 1
    location.add_ecosystem(ecosystem)
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
    for source in ['wte', 'ecu']:
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
    # Query the WTE server with a geographic coverages known to resolve
    # to one or more WTEs.
    g = geocov[1]
    gtype = g.geom_type(schema="esri")
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        geometry_type=gtype,
        map_server="wte"
    )
    attributes = globalelu.Attributes('wte')
    attributes.set_wte_attributes(r)
    assert len(attributes.data) == 6
    assert isinstance(attributes.data, dict)
    assert attributes.data.keys() == globalelu.Attributes('wte').data.keys()
    for attribute in attributes.data:
        assert isinstance(attributes.data[attribute], dict)
        assert attributes.data[attribute].keys() == \
               globalelu.Attributes('wte').data[attribute].keys()
        assert attributes.data[attribute]['label'] is not None
        assert attributes.data[attribute]['annotation'] is not None


def test_set_ecu_attributes(geocov):
    """Test the set_ecu_attributes() function.

    The set_ecu_attributes() method should take the data from an ECU query
    response, parse the components, and set the corresponding values in the
    fields of an Attributes class instance data attribute. These attributes
    should have the expected value types for the label and annotation fields.
    A successful query should return a dictionary with the set of expected
    attributes. An unsuccessful query should return None, with the result of
    not modifying the data attribute of the associated Attributes class
    instance.
    """
    # Successful query
    g = geocov[9]
    gtype = g.geom_type(schema="esri")
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=gtype,
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
    gtype = g.geom_type(schema="esri")
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=gtype,
        map_server="ecu"
    )
    raw_ecosystems = r.get_unique_ecosystems(source='ecu')
    attributes = globalelu.Attributes('ecu')
    attributes.set_ecu_attributes(raw_ecosystems)
    assert attributes.data == globalelu.Attributes('ecu').data


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
        geocov[0],  # A point on land
        geocov[1]  # An envelope on land
    ]
    for g in geocov_success:
        gtype = g.geom_type(schema="esri")
        r = globalelu.identify(
            geometry=g.to_esri_geometry(),
            geometry_type=gtype,
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
        gtype = g.geom_type(schema="esri")
        r = globalelu.identify(
            geometry=g.to_esri_geometry(),
            geometry_type=gtype,
            map_server="wte",
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
    geocov_ecu = [geocov[8], geocov[9]]
    for g in geocov_ecu:
        gtype = g.geom_type(schema="esri")
        r = globalelu.query(
            geometry=g.to_esri_geometry(),
            geometry_type=gtype,
            map_server="ecu"
        )
        assert r is not None
        expected_attributes = "CSU_Descriptor"  # ECU has one attribute
        attributes = r.get_attributes([expected_attributes])[
            expected_attributes]
        assert isinstance(attributes[0], str)
        assert len(attributes[0]) > 0
    # Query the ECU server with a geographic coverage that is known to
    # not resolve to one or more ECUs.
    g = geocov[0]
    gtype = g.geom_type(schema="esri")
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=gtype,
        map_server="ecu"
    )
    assert r is not None
    assert r.has_ecosystem('ecu') is False


# def test_wte_json_to_df():
#     """Test the wte_json_to_df() function.
#
#     The wte_json_to_df() function should convert a directory of json
#     files to a pandas DataFrame. The DataFrame should have the expected
#     columns and should not contain any list values.
#     """
#     df = globalelu.wte_json_to_df(json_dir="src/spinneret/data/json/")
#     assert df is not None
#     assert len(df) > 0
#     assert "file" in df.columns
#     for col in ["Landforms", "Landcover", "Climate_Region"]:
#         assert col in df.columns
#         assert df[col].apply(lambda x: isinstance(x, list)).sum() == 0


# def test_summarize_wte_results():
#     """Test the summarize_wte_results() function.
#
#     The summarize_wte_results() function should return a dictionary of
#     summary statistics for the results. The dictionary should contain the
#     expected keys.
#     """
#     df = globalelu.wte_json_to_df(json_dir="src/spinneret/data/json/")
#     res = globalelu.summarize_wte_results(wte_df=df)
#     assert isinstance(res, dict)
#     expected_keys = {
#         "Successful matches (percent)",
#         "Terrestrial ecosystems (number)",
#         "Aquatic ecosystems (number)",
#         "Unsupported geometries (number)",
#         "Out of bounds geometries (number)",
#         "No geographic coverage (number)",
#         "Landforms",
#         "Landcover",
#         "Climate_Region",
#     }
#     assert set(res.keys()) == expected_keys


def test_get_attributes(geocov):
    """Test the get_attributes() function.

    The get_attributes() function should return a dictionary of attributes
    from the response object. The dictionary should contain the requested
    attributes and return an empty list for attributes that are not present.
    """
    r = globalelu.identify(
        geometry=geocov[0].to_esri_geometry(),
        geometry_type=geocov[0].geom_type(schema="esri"),
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
    as a JSON string. The envelope should contain the point and have a spatial
    reference of 4326.
    """
    point = geocov[8].to_esri_geometry()  # A point location
    res = globalelu.convert_point_to_envelope(point)
    assert isinstance(res, str)
    point = json.loads(point)  # Convert to dict for comparison
    res = json.loads(res)
    assert point["x"] > res["xmin"]
    assert point["x"] < res["xmax"]
    assert point["y"] > res["ymin"]
    assert point["y"] < res["ymax"]
    assert res["spatialReference"]["wkid"] == 4326


def test_has_ecosystem(geocov):
    """Test the has_ecosystem method.

    The has_ecosystem method should return True when the geometry is
    within the WTE area and False when the geometry is outside the WTE area.
    Similarly, the has_ecosystem method should return True when the geometry
    overlaps with an ECU vector and False when the geometry does not overlap
    with an ECU vector.
    """
    # Geometries over land areas have a WTE ecosystem
    g = geocov[1]
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        geometry_type=g.geom_type(schema="esri"),
        map_server="wte"
    )
    assert r.has_ecosystem('wte') is True
    # Geometries over water bodies, or outside the WTE area, don't have a WTE
    # ecosystem.
    geocov_ecu = [geocov[4], geocov[6]]
    for g in geocov_ecu:
        r = globalelu.identify(
            geometry=g.to_esri_geometry(),
            geometry_type=g.geom_type(schema="esri"),
            map_server="wte"
        )
        assert r.has_ecosystem('wte') is False
    # Geometries near the coast have a ECU ecosystem
    g = geocov[8]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=g.geom_type(schema="esri"),
        map_server="ecu"
    )
    assert r.has_ecosystem('ecu') is True
    # Geometries far from the coast don't have a ECU ecosystem
    g = geocov[0]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=g.geom_type(schema="esri"),
        map_server="ecu"
    )
    assert r.has_ecosystem('ecu') is False


def test_get_wte_ecosystems():
    """Test the get_wte_ecosystems method.

    A successful query should return a non-empty list of WTE ecosystems. An
    unsuccessful query should return an empty list.
    """
    # Successful query
    g = geocov[1]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=g.geom_type(schema="esri"),
        map_server="wte"
    )
    ecosystems = r.get_wte_ecosystems()
    assert isinstance(ecosystems, list)
    assert len(ecosystems) > 0
    # Unsuccessful query
    g = geocov[2]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=g.geom_type(schema="esri"),
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
    g = geocov[9]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=g.geom_type(schema="esri"),
        map_server="ecu"
    )
    ecosystems = r.get_ecu_ecosystems()
    assert isinstance(ecosystems, list)
    assert len(ecosystems) > 0
    # Unsuccessful query
    g = geocov[1]
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=g.geom_type(schema="esri"),
        map_server="ecu"
    )
    ecosystems = r.get_ecu_ecosystems()
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
    gtype = g.geom_type(schema="esri")
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        geometry_type=gtype,
        map_server="wte"
    )

    # TODO add the refactored code below to get the raw list of ecosystems
    full_list_of_ecosystems = []
    attributes = globalelu.Attributes(source="wte").data.keys()
    results = r.json.get("results")
    for result in results:
        res = dict()
        for attribute in attributes:
            res[attribute] = result['attributes'].get(attribute)
        res = json.dumps(res)
        full_list_of_ecosystems.append(res)

    unique_ecosystems = r.get_unique_ecosystems(source='wte')
    assert isinstance(unique_ecosystems, set)
    assert len(full_list_of_ecosystems) == 1
    assert len(unique_ecosystems) == 1
    assert unique_ecosystems == set(full_list_of_ecosystems)
    # Test an unsuccessful response from the wte server identify operation
    # (i.e. a response that contains no ecosystem).
    g = geocov[2]
    gtype = g.geom_type(schema="esri")
    r = globalelu.identify(
        geometry=g.to_esri_geometry(),
        geometry_type=gtype,
        map_server="wte"
    )
    # TODO add the refactored code below to get the raw list of ecosystems
    # full_list_of_ecosystems = []
    # attributes = globalelu.Attributes(source="wte").data.keys()
    # results = r.json.get("results")
    # for result in results:
    #     res = dict()
    #     for attribute in attributes:
    #         res[attribute] = result['attributes'].get(attribute)
    #     res = json.dumps(res)
    #     full_list_of_ecosystems.append(res)

    unique_ecosystems = r.get_unique_ecosystems(source='wte')  # FIXME the response here should be an empty set
    assert isinstance(unique_ecosystems, set)
    assert len(full_list_of_ecosystems) == 0
    assert len(unique_ecosystems) == 0
    assert unique_ecosystems == set(full_list_of_ecosystems)

    # Test a successful response from the ECU server query (i.e. a response
    # that contains one or more ecosystems).
    g = geocov[9]
    gtype = g.geom_type(schema="esri")
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=gtype,
        map_server="ecu"
    )
    full_list_of_ecosystems = r.get_attributes(["CSU_Descriptor"])[
        "CSU_Descriptor"]
    unique_ecosystems = r.get_unique_ecosystems(source='ecu')
    assert isinstance(unique_ecosystems, set)
    assert len(full_list_of_ecosystems) == 123
    assert len(unique_ecosystems) == 34
    assert unique_ecosystems == set(full_list_of_ecosystems)
    # Test an unsuccessful response from the ECU server query (i.e. a response
    # that contains no ecosystems).
    g = geocov[1]
    gtype = g.geom_type(schema="esri")
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=gtype,
        map_server="ecu"
    )
    full_list_of_ecosystems = r.get_attributes(["CSU_Descriptor"])[
        "CSU_Descriptor"]
    unique_ecosystems = r.get_unique_ecosystems(source='ecu')
    assert isinstance(unique_ecosystems, set)
    assert len(full_list_of_ecosystems) == 0
    assert len(unique_ecosystems) == 0
    assert unique_ecosystems == set(full_list_of_ecosystems)

def test_eml_to_wte_json():
    """Test the eml_to_wte_json() function.

    Each EML file in the src/spinneret/data/eml/ directory should be converted
    to a json file and saved to an output directory. When an EML file is
    missing a corresponding json file, the eml_to_wte_json() function
    should fill the gap by creating the json file. Additionally, existing json
    files should not be overwritten unless the overwrite flag is set to
    True. Furthermore, output files should have the same content as the
    fixtures in src/spinneret/data/json/. This content check verifies both the
    structural components of the response object and the logic of
    eml_to_wte_json() that populates the structure with data.
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
        # Furthermore, output files should have the same content as the
        # fixtures in src/spinneret/data/json/. This content check verifies
        # both the structural components of the response object and the logic
        # of eml_to_wte_json() that populates the structure with data.
        for f in fnames_in:
            filecmp.cmp(
                join(tmpdir, f + ".json"),
                join("src/spinneret/data/json/", f + ".json"),
                shallow=False,
            )
