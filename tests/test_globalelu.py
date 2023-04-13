"""Test the globalelu module."""
import pytest
import tempfile
import os
import glob
import spinneret.globalelu as globalelu
import spinneret.eml as eml


@pytest.fixture
def geocov():
    """A list of GeographicCoverage instances from the test EML file."""
    res = eml.get_geographic_coverage(eml="src/spinneret/data/eml/edi.1.1.xml")
    return res


def test_eml_to_wte_pkl():
    """Test the eml_to_wte_pkl() function.

    Each EML file in the src/spinneret/data/eml/ directory should be converted
    to a WTE pickle file and saved to an output directory.
    """
    fpaths_in = glob.glob("src/spinneret/data/eml/" + "*.xml")
    fnames_in = [os.path.splitext(os.path.basename(f))[0] for f in fpaths_in]
    with tempfile.TemporaryDirectory() as tmpdir:
        globalelu.eml_to_wte_pkl(
            eml_dir="src/spinneret/data/eml/",
            output_dir=tmpdir
        )
        fpaths_out = os.listdir(tmpdir)
        for f in fnames_in:
            assert f + ".pkl" in fpaths_out
            assert os.path.getsize(os.path.join(tmpdir, f + ".pkl")) > 0

def test_identify(geocov):
    """Test the identify() function.

    # The identify function queries the WTE map service and returns a response
    # object. The response object's attributes differ based on the geometry
    # type. This test checks that the response object is not None and that the
    # attributes are of the correct type.
    """
    for g in geocov:
        gtype = g.geom_type(schema="esri")
        r = globalelu.identify(
            geometry=g.to_esri_geometry(),
            geometry_type=gtype,
            map_server="wte",
        )
        # TODO remove the type constraint in the following code block once
        #  support is added for all geometry types
        if gtype == "esriGeometryPoint":
            assert r is not None
            if r.get_attributes(["Pixel Value"])["Pixel Value"][0] != 'NoData':
                assert len(r.get_attributes(["Landforms"])["Landforms"]) > 0
                assert len(r.get_attributes(["Landcover"])["Landcover"]) > 0
                assert len(r.get_attributes(["Climate_Re"])["Climate_Re"]) > 0
        # if gtype == "esriGeometryPoint":
        #     # TODO Points return one ecosystem
        # elif gtype == "esriGeometryEnvelope":
        #     # TODO Large envelopes contain > 1 ecosystem
        #     assert type(res.get_attributes(["Landforms"])) is list
        # elif gtype == "esriGeometryPolygon":
        #     # TODO Large polygons contain > 1 ecosystem
        #     assert type(res.get_attributes(["Landforms"])) is list


def test_wte_pkl_to_df():
    """Test the wte_pkl_to_df() function.

    The wte_pkl_to_df() function should convert a directory of WTE pickle
    files to a pandas DataFrame. The DataFrame should have the expected
    columns and should not contain any list values.
    """
    df = globalelu.wte_pkl_to_df(pkl_dir="src/spinneret/data/pkl/")
    assert df is not None
    assert len(df) > 0
    assert "file" in df.columns
    for col in ["Landforms", "Landcover", "Climate_Region"]:
        assert col in df.columns
        assert df[col].apply(lambda x: type(x) is list).sum() == 0



def test_summarize_wte_results():
    df = globalelu.wte_pkl_to_df(pkl_dir="src/spinneret/data/pkl/")
    res = globalelu.summarize_wte_results(wte_df=df)
    assert type(res) is dict
    expected = set(["Landforms", "Landcover", "Climate_Region", "percent_success"])
    assert set(res.keys()) == expected
