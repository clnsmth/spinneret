"""Utilities for the geoenvo module"""
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon


def user_agent():
    """Define the spinneret user agent in HTTP requests

    For use with the `header` parameter of the requests library.

    Returns
    -------
    dict
        User agent
    """
    header = {"user-agent": "spinneret Python package"}
    return header


def _json_extract(obj, key):
    """Recursively fetch values from nested JSON.

    Parameters
    ----------
    obj : dict
        A JSON object
    key : str
        The key to search for

    Returns
    -------
    arr : list
        A list of values for the given key
    """
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    values = extract(obj, arr, key)
    return values


def convert_point_to_envelope(geometry, buffer=None):
    """Convert an esriGeometryPoint to an esriGeometryEnvelope

    Parameters
    ----------
    geometry : dict
        An esriGeometryEnvelope representing a point
    buffer : float
        The distance in kilometers to buffer the point. The buffer is a radius
        around the point. The default is 0.5.

    Returns
    -------
    str : ESRI JSON envelope geometry

    Notes
    -----
    This function assumes the coordinate reference system of the input
    geometry is EPSG:4326.
    """
    if not _is_point_location(geometry) or buffer is None:
        return geometry
    geometry = json.loads(geometry)
    df = pd.DataFrame([{"longitude": geometry["xmin"], "latitude": geometry["ymin"]}])
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326"
    )
    # TODO Verify the consequences of projecting to an arbitrary CRS
    #  for sake of buffering.
    gdf = gdf.to_crs("EPSG:32634")  # A CRS in units of meters
    gdf.geometry = gdf.geometry.buffer(buffer * 1000)  # Convert to meters
    gdf = gdf.to_crs("EPSG:4326")  # Convert back to EPSG:4326
    bounds = gdf.bounds
    # TODO Update values of geometry object
    geometry["xmin"] = bounds.minx[0]
    geometry["ymin"] = bounds.miny[0]
    geometry["xmax"] = bounds.maxx[0]
    geometry["ymax"] = bounds.maxy[0]
    return json.dumps(geometry)


def _get_geometry_type(geometry):
    """Get the geometry type from the response object's geometry attribute

    Parameters
    ----------
    geometry : str
        The ESRI geometry object

    Returns
    -------
    str : The geometry type

    Notes
    -----
    This function determines the geometry type by looking for distinguishing
    properties of the ESRI geometry object.
    """
    geometry = json.loads(geometry)
    if geometry.get("x") is not None:
        return "esriGeometryPoint"
    elif geometry.get("xmin") is not None:
        return "esriGeometryEnvelope"
    elif geometry.get("rings") is not None:
        return "esriGeometryPolygon"
    else:
        return None


def _is_point_location(geometry):
    """Is a geometry a point location? Points are represented as envelopes, but
    it is useful to know if the geometry is a point location for some internal
    processes

    Parameters
    ----------
    geometry : str
        The ESRI geometry object

    Returns
    -------
    bool : True if the geometry is a point location, False otherwise
    """
    if _get_geometry_type(geometry) != "esriGeometryEnvelope":
        return False
    geometry = json.loads(geometry)
    if geometry.get("xmin") == geometry.get("xmax") and geometry.get(
        "ymin"
    ) == geometry.get("ymax"):
        return True
    return False


def _polygon_or_envelope_to_points(geometry):
    """Convert a polygon or envelope to a list of points

    Parameters
    ----------
    geometry : str
        The ESRI geometry object

    Returns
    -------
    list : A list of ESRI envelope geometries (as str) representing point
    locations (i.e. xmin == xmax and ymin == ymax). Note, this is a design
    decision.

    Notes
    -----
    For improving the results from the WTE identify responses. Currently, the
    identify operation returns the midpoint of the envelope. This function
    returns the vertices of a polygon or envelope in addition to the centroid.
    This function could likely be improved.

    Currently, this only operates on the outer ring of a polygon. Inner rings
    are not considered. A warning is thrown if inner rings are present, because
    the centroid will be incorrect.
    """
    geometry_type = _get_geometry_type(geometry)
    geometry = json.loads(geometry)
    # TODO-merge: Create xy series based on whether the geometry is a polygon
    #  or a envelope.
    if geometry_type == "esriGeometryPolygon":
        # Create a GeoSeries with the vertices of the polygon
        bounds = []
        for xy_pair in geometry.get("rings")[0]:
            x, y = xy_pair
            bounds.append((x, y))
        # Bump off the last one since it is the same as the first
        bounds.pop()
        # TODO Throw a warning when inner ring is present, because the centriod
        #  will be incorrect.
    elif geometry_type == "esriGeometryEnvelope":
        # Create a GeoSeries with the four corners of the envelope
        bounds = [
            (geometry.get("xmin"), geometry.get("ymin")),
            (geometry.get("xmax"), geometry.get("ymin")),
            (geometry.get("xmax"), geometry.get("ymax")),
            (geometry.get("xmin"), geometry.get("ymax")),
        ]
    # Construct point geometries from the envelope corners
    res = []
    for corner in bounds:
        res.append(
            json.dumps(
                {
                    "xmin": corner[0],
                    "ymin": corner[1],
                    "xmax": corner[0],
                    "ymax": corner[1],
                    "zmin": geometry.get("zmin"),
                    "zmax": geometry.get("zmax"),
                    "spatialReference": geometry.get("spatialReference"),
                }
            )
        )
    # Get the centroid of the geometry
    shape = gpd.GeoSeries(Polygon(bounds))
    centroid = shape.centroid
    # TODO Use one single consistent approach to transferring values to the
    #  result for simplicity.
    res.append(
        json.dumps(
            {
                "xmin": centroid.x[0],
                "ymin": centroid.y[0],
                "xmax": centroid.x[0],
                "ymax": centroid.y[0],
                "zmin": geometry.get("zmin"),
                "zmax": geometry.get("zmax"),
                "spatialReference": geometry.get("spatialReference"),
            }
        )
    )
    return res