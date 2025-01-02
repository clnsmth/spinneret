"""The insights module."""
import glob
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patheffects import withStroke


def json_to_df(json_dir, format="wide"):
    """Combine json files into a single dataframe

    Parameters
    ----------
    json_dir : str
        Path to directory containing json files
    format : str
        Format of output dataframe. Options are "wide" and "long". Default is
        "wide".

    Returns
    -------
    df : pandas.DataFrame
        A dataframe of geographic coverages and select ecosystem attributes.

    Notes
    -----
    The results of this function modify the native representation of ecosystems
    returned by map servers from grouped sets of attributes to grouped sets of
    unique attributes, and thus changes the semantics of how the map server
    authors intended the data to be interpreted. Specifically, areal
    geometries, returned by this function, include the unique attributes of all
    ecosystems within the area, whereas point geometries will only include the
    attributes of the ecosystem at the point.
    """
    files = glob.glob(json_dir + "*.json")
    if not files:
        raise FileNotFoundError("No json files found")
    res = []
    # Initialize the fields of the output dictionary from the
    # attributes of the ecosystem object. Constructing this dictionary
    # manually is probably less work and more understandable than
    # using a coded approach.
    boilerplate_output = {
        "dataset": None,
        "description": None,
        "geometry_type": None,
        "comments": None,
        "source": None,
        "Climate_Re": None,  # WTE attributes ...
        "Landcover": None,
        "Landforms": None,
        "Slope": None,  # ECU attributes ...
        "Sinuosity": None,
        "Erodibility": None,
        "Temperature and Moisture Regime": None,
        "River Discharge": None,
        "Wave Height": None,
        "Tidal Range": None,
        "Marine Physical Environment": None,
        "Turbidity": None,
        "Chlorophyll": None,
        "OceanName": None,  # EMU attributes ...
        "Depth": None,
        "Temperature": None,
        "Salinity": None,
        "Dissolved Oxygen": None,
        "Nitrate": None,
        "Phosphate": None,
        "Silicate": None,
    }
    # Iterate over the json files, parse the contents into a dictionary, and
    # append the results to the res list for later conversion to a dataframe.
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            j = json.load(f)
            dataset = j.get("dataset")
            location = j.get("location")
            # No locations were found. Append and continue.
            if len(location) == 0:
                output = dict(
                    boilerplate_output
                )  # Create a copy of the boilerplate and begin populating it
                # Note, in this function, values for the output dictionary are
                # stored as variables, which are added to the dictionary right
                # before it is appended to the res list. This is done to ensure
                # that the results are not the most recent iteration of the
                # loop.
                output["dataset"] = dataset
                res.append(output)
            else:
                # At least one location was found, and is possible that an
                # ecosystem was resolved.# At least one location was found,
                # and is possible that an ecosystem was resolved.
                for loc in location:
                    description = loc.get("description")
                    geometry_type = loc.get("geometry_type")
                    comments = loc.get("comments")
                    # FIXME: This is an edge case, the origins of which are not
                    #  yet known. Convert None values to empty strings to
                    #  handle this for the time being.
                    comments = ["" if c is None else c for c in comments]
                    comments = " ".join(comments)
                    ecosystem = loc.get("ecosystem")
                    if (
                        len(ecosystem) == 0
                    ):  # No ecosystems were resolved. Append and continue.
                        output = dict(boilerplate_output)
                        output["dataset"] = dataset
                        output["description"] = description
                        output["geometry_type"] = geometry_type
                        output["comments"] = comments
                        res.append(output)
                    else:
                        # At least one ecosystem was resolved. Parse the
                        # attributes and append.
                        for eco in ecosystem:
                            source = eco.get("source")
                            output = dict(boilerplate_output)
                            output["dataset"] = dataset
                            output["description"] = description
                            output["geometry_type"] = geometry_type
                            output["comments"] = comments
                            output["source"] = source
                            attributes = eco.get("attributes")
                            # Iterate over the resolved ecosystem's attributes
                            # and add them to the output dictionary if they are
                            # present in the boilerplate dictionary.
                            for attribute in attributes:
                                if attribute in output.keys():
                                    output[attribute] = attributes[attribute]["label"]
                            res.append(output)
    # Convert the dictionary to a dataframe in wide format. This is the default
    # format, and is easily facilitated because the output dictionary is
    # flat (i.e. not nested).
    df = pd.DataFrame(res)
    # Sort for readability
    df[["scope", "identifier"]] = df["dataset"].str.split(".", n=1, expand=True)
    df["identifier"] = pd.to_numeric(df["identifier"])
    df = df.sort_values(by=["scope", "identifier"])
    df = df.drop(columns=["scope", "identifier"])
    # Rename columns for readability
    df = df.rename(
        columns={
            "dataset": "package_id",
            "description": "geographic_coverage_description",
            "source": "ecosystem_type",
        }
    )
    # Convert acronyms (of ecosystem types) to more descriptive names for
    # readability
    df["ecosystem_type"] = df["ecosystem_type"].replace(
        {"wte": "Terrestrial", "ecu": "Coastal", "emu": "Marine"}
    )
    if format == "wide":
        return df
    # Convert df to long format if specified in the function call. Attribute
    # value pairs are the ecosystem attributes and their values.
    df = pd.melt(
        df,
        id_vars=[
            "package_id",
            "geographic_coverage_description",
            "geometry_type",
            "comments",
            "ecosystem_type",
        ],
        var_name="ecosystem_attribute",
        value_name="value",
    )

    # Remove rows where ecosystem_type and ecosystem_attribute should not be
    # listed together (e.g. "Terrestrial" and "Depth"). This is a result of
    # melting the wide data frame to a long data frame. Not doing would
    # result in a dataframe with rows that have no meaning and that cause the
    # user confusion. We do this by creating long dataframes for each of the
    # ecosystem types (and their associated attributes), and then concatenating
    # them together.

    # Subset the dataframe where the ecosystem_type is "Terrestrial".
    df_terrestrial = df[df["ecosystem_type"] == "Terrestrial"]
    df_terrestrial = df_terrestrial[
        df_terrestrial["ecosystem_attribute"].isin(
            ["Climate_Re", "Landcover", "Landforms"]
        )
    ]
    # Subset the dataframe where the ecosystem_type is "Coastal".
    df_coastal = df[df["ecosystem_type"] == "Coastal"]
    df_coastal = df_coastal[
        df_coastal["ecosystem_attribute"].isin(
            [
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
            ]
        )
    ]
    # Subset the dataframe where the ecosystem_type is "Marine".
    df_marine = df[df["ecosystem_type"] == "Marine"]
    df_marine = df_marine[
        df_marine["ecosystem_attribute"].isin(
            [
                "OceanName",
                "Depth",
                "Temperature",
                "Salinity",
                "Dissolved Oxygen",
                "Nitrate",
                "Phosphate",
                "Silicate",
            ]
        )
    ]
    # Concatenate the three dataframes together.
    df = pd.concat([df_terrestrial, df_coastal, df_marine])

    # FIXME: Drop duplicate rows and values of "n/a". This represents an edge
    #  case that should be handled upstream. Not sure why this is happening.
    df = df.drop_duplicates()
    df = df[df["value"] != "n/a"]

    # Sort by package_id and attribute for readability
    df = df.sort_values(
        by=[
            "package_id",
            "geographic_coverage_description",
            "geometry_type",
            "comments",
            "ecosystem_type",
            "ecosystem_attribute",
            "value",
        ]
    )
    # Sort for readability. This is the same as the above sort but is done
    # again after a series of operations that may have changed the order.
    df[["scope", "identifier"]] = df["package_id"].str.split(".", n=1, expand=True)
    df["identifier"] = pd.to_numeric(df["identifier"])
    df = df.sort_values(by=["scope", "identifier"])
    df = df.drop(columns=["scope", "identifier"])
    return df


def get_number_of_unique_ecosystems(df_wide):
    """Get the number of unique ecosystems for each ecosystem type

    Parameters
    ----------
    df_wide : pandas.DataFrame
        A dataframe created by `json_to_df` in wide format

    Returns
    -------
    res : dict
        A dictionary of the number of unique ecosystems for each ecosystem
        type, i.e. "Terrestrial", "Coastal", "Marine"
    """
    # Drop the columns that are not ecosystem attributes except for ecosystem
    # type, which is needed to count the number of unique ecosystems for each
    # ecosystem type.
    df = df_wide.drop(
        columns=[
            "package_id",
            "geographic_coverage_description",
            "geometry_type",
            "comments",
        ]
    )
    # Drop duplicate rows so that each row represents a unique ecosystem
    df = df.drop_duplicates()
    # Drop rows where the ecosystem type is None, these should not be counted.
    df = df.dropna(subset=["ecosystem_type"])
    # Get the total number of unique ecosystems and for each ecosystem type and
    # return the result as a dictionary.
    res = {}
    res["Total"] = df.shape[0]
    for eco_type in df["ecosystem_type"].unique():
        res[eco_type] = df[df["ecosystem_type"] == eco_type].shape[0]
    return res


def get_number_of_unique_geographic_coverages(df_wide):
    """Get the number of unique geographic coverages

    Parameters
    ----------
    df_wide : pandas.DataFrame
        A dataframe created by `json_to_df` in wide format

    Returns
    -------
    res : int
        The number of unique geographic coverages (locations) across all
        datasets.
    """
    # Create a new data frame with the columns package_id,
    # geographic_coverage_description, and geometry_type. These form a
    # composite key of unique ecosystems.
    df = df_wide[["package_id", "geographic_coverage_description", "geometry_type"]]
    # Drop duplicate rows so that each row represents a unique ecosystem
    df = df.drop_duplicates()
    # Get the number of unique geographic coverages and return the result.
    res = df.shape[0]
    return res


def get_percent_of_geometries_with_no_ecosystem(df_wide):
    """Get the percent of geometries with no ecosystem

    Parameters
    ----------
    df_wide : pandas.DataFrame
        A dataframe created by `json_to_df` in wide format

    Returns
    -------
    res : float
        The percent of geometries with no ecosystem.

    Notes
    -----
    This doesn't mean that the correct ecosystem (or all possible ecosystems
    in actuality) for the geometry was resolved, rather that the geometry
    resolves to ecosystem in the supported set of map servers.
    """
    # Drop the columns that are not ecosystem attributes or geometry
    # identifiers since we only want to count the number of geometries with no
    # ecosystem.
    df = df_wide.drop(columns=["geometry_type", "comments", "ecosystem_type"])
    # Get number of rows where package_id and geographic_coverage_description
    # are the same.
    total_number_of_unique_geometries = df[
        df.duplicated(subset=["package_id", "geographic_coverage_description"])
    ].shape[0]
    # Remove rows from df where all ecosystem attribute columns do not have a
    # value of None. The remaining rows represent geometries that have no
    # ecosystem for some reason.
    ecosystem_attribute_columns = [
        "Climate_Re",
        "Landcover",
        "Landforms",
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
        "OceanName",
        "Depth",
        "Temperature",
        "Salinity",
        "Dissolved Oxygen",
        "Nitrate",
        "Phosphate",
        "Silicate",
    ]
    df = df[df[ecosystem_attribute_columns].isnull().all(axis=1)]
    # Drop duplicate rows so that each row represents a unique geometry with no
    # ecosystem
    df = df.drop_duplicates()
    # Get the number of rows in df, which is the number of geometries with no
    # ecosystem
    number_of_geometries_with_no_ecosystem = df.shape[0]
    # Return as the percent of geometries with no ecosystem out of the total
    # number of unique geometries.
    percent_of_geometries_with_no_ecosystem = (
        number_of_geometries_with_no_ecosystem / total_number_of_unique_geometries * 100
    )
    return percent_of_geometries_with_no_ecosystem


def plot_wide_data(df_wide):
    """Plot the proportion of ecosystem types across datasets

    Parameters
    ----------
    df_wide : pandas.DataFrame
        A dataframe created by `json_to_df` in wide format

    Returns
    -------
    None
    """
    # FIXME: This function should be renamed to something more descriptive.
    # Count the number of unique ecosystem_type values for each unique
    # package_id.
    df = (
        df_wide.groupby(["package_id", "ecosystem_type"])
        .size()
        .reset_index(name="Count")
    )
    # Create a histogram of the counts for each ecosystem_type
    df.hist(column="Count", by="ecosystem_type", bins=20, figsize=(10, 10))
    plt.show()
    return None


def plot_long_data(df_long, output_dir):
    # FIXME: This function should be renamed to something more descriptive.
    # Remove rows that contain None in any column to facilitate plotting.
    df = df_long.dropna()
    # Drop geographic_coverage_description, comments, and geometry_type
    # columns since they are not used in this analysis.
    df = df.drop(
        columns=["geographic_coverage_description", "comments", "geometry_type"]
    )
    # Drop duplicate rows
    df = df.drop_duplicates()
    # Group by ecosystem_type, ecosystem_attribute, and value and count the
    # number of unique package_id values for each unique combination of
    # ecosystem_type, ecosystem_attribute, and value. This creates the data
    # frame that will be used to create the plots.
    df = (
        df.groupby(["ecosystem_type", "ecosystem_attribute", "value"])
        .size()
        .reset_index(name="Count")
    )

    # Create a series of horizontal bar plots for each ecosystem type,
    # where each plot is grouped by the ecosystem_attribute column. Individual
    # plots are necessary, rather than a single plot with subplots, because
    # the number of plots generated for the marine and coastal ecosystem types
    # is on the order of 10s, which is too many to display in a single plot.
    for ecosystem_type in df["ecosystem_type"].unique():
        # Subset the data frame to only include rows that contain the current
        # ecosystem_type (i.e. Terrestrial, Marine, or Coastal).
        df_subset = df[df["ecosystem_type"] == ecosystem_type]
        for ecosystem_attribute in df_subset["ecosystem_attribute"].unique():
            # Subset the data frame to only include rows that contain the
            # current ecosystem_attribute values.
            df_subset2 = df_subset[
                df_subset["ecosystem_attribute"] == ecosystem_attribute
            ]
            # Sort the rows by the value column in descending order for
            # readability.
            df_subset2 = df_subset2.sort_values(by=["Count"], ascending=True)

            # Start building the bar chart.
            counts = df_subset2["Count"].values.tolist()
            names = df_subset2["value"].values.tolist()
            BLUE = "#076fa2"
            # Set the positions for the bars. This allows us to determine
            # the bar locations.
            y = [i * 0.9 for i in range(len(names))]
            # Create the basic bar chart
            fig, ax = plt.subplots(figsize=(12, 7))
            ax.barh(y, counts, height=0.55, align="edge", color=BLUE)
            # Customize the layout of the bar chart
            if max(counts) >= 200:
                x_tick_interval = 20
            else:
                x_tick_interval = 10
            ax.xaxis.set_ticks([i for i in range(0, max(counts), x_tick_interval)])
            ax.xaxis.set_ticklabels(
                [i for i in range(0, max(counts), x_tick_interval)],
                size=16,
                fontweight=100,
            )
            ax.xaxis.set_tick_params(labelbottom=False, labeltop=True, length=0)
            ax.set_xlim((0, max(counts) + 10))
            ax.set_ylim((0, len(names) * 0.9 - 0.2))
            # Set whether axis ticks and gridlines are above or below most
            # axes.
            ax.set_axisbelow(True)
            ax.grid(axis="x", color="#A8BAC4", lw=1.2)
            ax.spines["right"].set_visible(False)
            ax.spines["top"].set_visible(False)
            ax.spines["bottom"].set_visible(False)
            ax.spines["left"].set_lw(1.5)
            # This capstyle determines the lines don't go beyond the limit we
            # specified see: https://matplotlib.org/stable/api/_enums_api.html
            # ?highlight=capstyle#matplotlib._enums.CapStyle
            ax.spines["left"].set_capstyle("butt")
            # Hide y labels
            ax.yaxis.set_visible(False)
            fig
            # Add the labels
            PAD = 0.3
            for name, count, y_pos in zip(names, counts, y):
                x = 0
                color = "lightgrey"
                path_effects = None
                # Determine if the bar label should be inside or outside the
                # bar by comparing the x value of the bar to the x value of
                # the text label. To do this we first plot both with
                # "invisible ink", get the max x position of each, and then
                # compare them.
                ax.text(
                    x + PAD,
                    y_pos + 0.5 / 2,
                    name,
                    color="none",
                    fontsize=18,
                    va="center",
                    path_effects=path_effects,
                )
                x_text_end = ax.texts[-1].get_window_extent().x1
                ax.plot(count, y_pos, ".", color="none", markersize=18)
                x_point = ax.lines[-1].get_window_extent().x1
                position_label_to_right_of_bar = x_text_end > x_point
                # Add the text label to the appropriate position
                if position_label_to_right_of_bar:
                    x = count
                    color = BLUE
                    path_effects = [withStroke(linewidth=6, foreground="white")]
                ax.text(
                    x + PAD,
                    y_pos + 0.5 / 2,
                    name,
                    color=color,
                    fontsize=18,
                    va="center",
                    path_effects=path_effects,
                )
            fig
            # Add annotations and final tweaks
            # Make room on top and bottom
            # Note there's no room on the left and right sides
            fig.subplots_adjust(left=0.05, right=1, top=0.8, bottom=0.1)
            # Add x label
            ax.set_xlabel("Number of Datasets", size=18, fontweight=100)
            ax.xaxis.set_label_coords(0.5, 1.14)
            # Add title
            ttl = "{} - {}".format(ecosystem_type, ecosystem_attribute)
            fig.text(
                # 0, 0.925, ttl,
                0.05,
                0.925,
                ttl,
                fontsize=22,
                fontweight="bold",
            )
            # Set facecolor, useful when saving as .png
            fig.set_facecolor("white")
            fig
            fig.savefig(output_dir + ttl + ".png", dpi=300)
    return None


def summarize_results(wte_df):
    """Summarize results

    Parameters
    ----------
    wte_df : pandas.DataFrame
        A dataframe of the ecosystems created by `json_to_df`

    Returns
    -------
    res : dict
        A dictionary of the results
    """
    # TODO: This function is outdated, but could remain useful if updated to
    #  work with the new data summarizing functions.
    res = {}
    cols = wte_df.columns.tolist()
    cols_eco = ["Landforms", "Landcover", "Climate_Re"]
    # Match success rate of the identify operation
    df = wte_df[cols].dropna(subset=cols_eco)
    res["Successful matches (percent)"] = (df.shape[0] / wte_df.shape[0]) * 100
    other_metrics = {
        "Terrestrial ecosystems (number)": "Is a terrestrial ecosystem.",
        "Aquatic ecosystems (number)": "Is an aquatic ecosystem.",
        "Unsupported geometries (number)": "Envelopes and polygons are not supported",
        "Out of bounds geometries (number)": "Is unknown ecosystem (outside the WTE area).",
        "No geographic coverage (number)": "No geographic coverage found",
    }
    for key, value in other_metrics.items():
        i = wte_df["comments"] == value
        res[key] = wte_df[i].shape[0]
    for col in cols_eco:
        df["count"] = 1
        df_grouped = df.groupby(col).count().reset_index()
        df_grouped = df_grouped.sort_values(by="count", ascending=False)
        res[col] = df_grouped.set_index(col).to_dict()["count"]
    return res