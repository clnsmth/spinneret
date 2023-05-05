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


def test_identify(geocov):
    """Test the identify() function.

    The identify function queries a map service and returns a response object.
    The response object's attributes differ based on the geometry type and the
    specific map service that was queried. This test checks that the response
    object is not None and that the attributes are of the correct type.
    """
    # Look for expected WTE response attributes
    for g in geocov:
        gtype = g.geom_type(schema="esri")
        r = globalelu.identify(
            geometry=g.to_esri_geometry(),
            geometry_type=gtype,
            map_server="wte",
        )
        if gtype == "esriGeometryPoint":
            assert r is not None
            # FIXME This logic does not garuntee the following assertions are
            #  ever run. It could be that WTE never has a positive ecosystem
            #  response. Better is prescribe the set of geographic coverages
            #  that are expected to resolve to WTE. See test_query() for a
            #  working example.
            if r.has_ecosystem(source="wte"):
                # TODO assert points return one ecosystem
                expected_attributes = globalelu.Attributes(
                    source="wte").data.keys()
                for attr in expected_attributes:
                    assert attr in r.get_attributes([attr]).keys()
                    assert len(r.get_attributes([attr])[attr][0]) > 0

        # elif gtype == "esriGeometryEnvelope":
        #     # TODO Large envelopes contain > 1 ecosystem
        #     assert type(res.get_attributes(["Landforms"])) is list
        # elif gtype == "esriGeometryPolygon":
        #     # TODO Large polygons contain > 1 ecosystem
        #     assert type(res.get_attributes(["Landforms"])) is list


def test_query(geocov):
    """Test the query() function.

    The query function queries a map service and returns a response object.
    The response object's attributes differ based on the specific map service
    that was queried. This test checks that the response object is not None
    and that the attributes are of the correct type.
    """
    # Query the ECU server with a set of geographic coverages known to resolve
    # to one or more ECUs.
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
        assert len(
            r.get_attributes([expected_attributes])[expected_attributes][
                0]) > 0
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


def test_set_ecu_attributes(geocov):
    # Query the ECU server with a set of geographic coverages known to resolve
    # to one or more ECUs.
    g = geocov[9]
    gtype = g.geom_type(schema="esri")
    r = globalelu.query(
        geometry=g.to_esri_geometry(),
        geometry_type=gtype,
        map_server="ecu"
    )
    # FIXME Note, these are a prototype of the innerworkings of a set_ecosystems() function.
    #  This is for temporary testing/dev purposes.
    unique_ecosystem_attributes = r.get_unique_ecosystems(source='ecu')  # Get unique ecosystems listed in the response
    one_attribute_set = next(iter(unique_ecosystem_attributes))  # Iteration begins
    attributes = globalelu.Attributes('ecu')
    attributes.set_ecu_attributes(one_attribute_set)

    assert len(r.json.get("features")) > 0
    features = r.get_attributes(["CSU_Descriptor"])["CSU_Descriptor"]
    assert len(features) > 0
    assert len(set(features)) == 2  # Testing unique features


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

    assert False
