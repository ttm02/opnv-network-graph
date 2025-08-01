from matplotlib import pyplot as plt
import matplotlib.cm as cm
import matplotlib
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from network import Network
from utils import *
import pandas as pd

import warnings

import argparse


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--network_file', default='network.db', required=False)
    parser.add_argument('--stations_file', default='stops.csv', required=False)
    parser.add_argument('--time_limit', default=30, type=int, help='time limit in minutes', required=False)
    parser.add_argument('--start_time', default='09:00', type=str, help='start time in HH:MM', required=False)
    parser.add_argument('--station', default='Frankfurt Hauptbahnhof', type=str, required=False)
    parser.add_argument('--output', default='map.png', required=False)

    return parser.parse_args()


def main():
    args = parse_arguments()

    network = Network(args.network_file)
    print("Read Station Positions")
    stops_data = pd.read_csv(args.stations_file, index_col="DHID")
    stops_data.dropna(inplace=True)

    print("Find Start station")
    start_station = find_closest_station_id_by_name(args.station, stops_data)
    time_limit = args.time_limit
    start_time = time_to_minutes(args.start_time)

    map_box = (49.8388, 8.560719, 49.931479, 8.750582)  # area around Darmstadt
    # select stops in that area
    in_area = stops_data[(stops_data["Latitude"] > map_box[0]) &
                         (stops_data["Latitude"] < map_box[2]) &
                         (stops_data["Longitude"] > map_box[1]) &
                         (stops_data["Longitude"] < map_box[3])].copy()

    get_departures_plot(network, in_area, map_box)

def get_departures_plot(network, in_area, map_box):
    # get the data
    def get_depatures(stop_id):
        result = []
        for stop_id, timetable in network.stops[stop_id].items():
            timetable.sort()
            for connection in timetable:
                result.append(connection.departure)
        return result

    def count_daytime_departures(stop_id):
        departures = get_depatures(stop_id)
        return sum(9 <= (t // 60) < 18 for t in departures)  # counts hours 9–17

    # collect number of departures
    in_area["daytime_departures"] = in_area.index.map(count_daytime_departures)
    # in_area["daytime_departures"] = in_area["daytime_departures"] / 8 # per hour
    # remove stations only used at night (or not at all)
    in_area_with_depatures = in_area[
        in_area["daytime_departures"] > 0].copy()

    cmap, norm = add_color_col(in_area_with_depatures, "daytime_departures")
    get_point_plot(in_area_with_depatures, "color", map_box, norm, cmap,
                   "Number of Departures from 9 to 17:00", "departures")


def add_color_col(df, values_col, colormap="plasma", color_col="color"):
    norm = mcolors.LogNorm(
        vmin=df[values_col].min(),
        vmax=df[values_col].max()
    )
    cmap = matplotlib.colormaps[colormap]  # or "plasma", "virdis", etc.
    colors = cmap(norm(df[values_col].to_numpy()))
    # colors is now a 2D array, as ech color has a distinct values for rgba, need to combine them for the pandas dataframe, alternatively, we could use mcolors.to_hex
    df[color_col] = [tuple(c) for c in colors]
    return cmap, norm


def draw_map(map_box, title):
    map = get_map(map_box)

    ax = map.show_mpl(figsize=(12, 12))

    ax.annotate(
        title,
        xy=(0.5, 1.02),  # Position relative to axes (centered above the map)
        xycoords="axes fraction",
        fontsize=24,
        ha="center",  # Center horizontally
        va="bottom",  # Position below the top edge
    )
    return map, ax


def draw_data_points(map, ax, df, color_col):
    # plot data points
    for _, row in df.iterrows():
        lat, lon = row["Latitude"], row["Longitude"]
        x, y = map.to_pixels(lat, lon)

        color = row[color_col]
        ax.plot(x, y, 'o', color=color, ms=10, mew=0.5, alpha=.5)


def add_colorbar(ax, norm, cmap):
    cax = inset_axes(ax,
                     width="5%",  # width of colorbar relative to parent axes
                     height="50%",  # height of colorbar relative to parent axes
                     loc='upper right',
                     borderpad=2)
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    plt.colorbar(sm, cax=cax)


def save_plot(filename):
    # write to file
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        # ignore the warning about tight layout as the result looks satisfactory
        # inset_axes will plate the colorbar inside the map, so no real problem with a tight_layout
        plt.tight_layout()
    plt.savefig(f"{filename}.png")


def get_point_plot(df, color_col, map_box, norm, cmap, title, outname):
    map, ax = draw_map(map_box, title)
    draw_data_points(map, ax, df, color_col)
    add_colorbar(ax, norm, cmap)
    save_plot(outname)


if __name__ == '__main__':
    main()
