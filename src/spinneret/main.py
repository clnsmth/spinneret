"""The Main module for Spinneret."""

from spinneret.eml import eml_to_wte_json
from spinneret.insights import (json_to_df, get_number_of_unique_ecosystems,
                                get_percent_of_geometries_with_no_ecosystem,
                                get_number_of_unique_geographic_coverages,
                                plot_long_data, plot_wide_data)


if __name__ == "__main__":

    # Transform EML to ecosystems and write to json file

    eml_to_wte_json(
        eml_dir="/Users/csmith/Data/globalelu/eml/",
        output_dir="/Users/csmith/Data/globalelu/results/",
        overwrite=True
    )

    # Insights

    # Combine json files into a single dataframe
    df_long = json_to_df(json_dir="/Users/csmith/Data/edi/top_20_json/", format="long")
    df_wide = json_to_df(json_dir="/Users/csmith/Data/edi/top_20_json/", format="wide")

    # Write df to tsv
    import csv
    output_dir = "/Users/csmith/Data/edi/"
    df_long.to_csv(output_dir + "top_20_results.tsv", sep="\t",
                   index=False,
                   quoting=csv.QUOTE_ALL)

    # Summarize results
    unique_ecosystems_by_type = get_number_of_unique_ecosystems(df_wide)
    no_ecosystem = get_percent_of_geometries_with_no_ecosystem(df_wide)
    number_of_unique_geographic_coverages = get_number_of_unique_geographic_coverages(df_wide)

    # PLot results
    # plot_wide_data(df_wide)
    plot_long_data(df_long, output_dir="/Users/csmith/Data/edi/top_20_plots/")

    print("42")
