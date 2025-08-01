from matplotlib import pyplot as plt
import matplotlib.cm as cm
import matplotlib
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from network import Network
from utils import *
import pandas as pd
from tqdm import tqdm

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
    stops_data = pd.read_csv(args.stations_file, index_col="DHID")
    stops_data.dropna(inplace=True)

    map_box = (49.8388, 8.560719, 49.931479, 8.750582)  # area around Darmstadt
    # select stops in that area
    in_area = stops_data[(stops_data["Latitude"] > map_box[0]) &
                         (stops_data["Latitude"] < map_box[2]) &
                         (stops_data["Longitude"] > map_box[1]) &
                         (stops_data["Longitude"] < map_box[3])].copy()

    get_early_departure_plot(network, in_area, map_box)
    get_num_departures_plot(network, in_area, map_box)
    get_num_connections_plot(network, in_area, map_box)
    get_reacable_in_plot(network, in_area, map_box, "Darmstadt Schloss")

    get_num_vehicles_plot(network, in_area, map_box)
    get_fastest_route_plot(network, stops_data, [9 * 60 + 0, 9 * 60 + 15, 9 * 60 + 30, 9 * 60 + 45],
                           "Darmstadt Schloss", "Dieburg Bahnhof")


def get_num_departures_plot(network, in_area, map_box):
    # get the data
    def get_num_depatures(stop_id):
        result = []
        for stop_id, timetable in network.stops[stop_id].items():
            timetable.sort()
            for connection in timetable:
                result.append(connection.departure)
        return result

    def count_daytime_departures(stop_id):
        departures = get_num_depatures(stop_id)
        return sum(9 <= (t // 60) < 18 for t in departures)  # counts hours 9–17

    # collect number of departures
    in_area["daytime_departures"] = in_area.index.map(count_daytime_departures)
    # in_area["daytime_departures"] = in_area["daytime_departures"] / 8 # per hour
    # remove stations only used at night (or not at all)
    in_area_with_depatures = in_area[
        in_area["daytime_departures"] > 0].copy()

    get_plot_colorbar(in_area_with_depatures, "daytime_departures", map_box,
                      kind="points", title="Number of Departures from 9 to 17:00", outname="num_departures")


def get_early_departure_plot(network, in_area, map_box):
    end_of_day = 2 * 60 + 50  # 02:50

    # a bus leaving at 0:30 is part of the old day, that is your ticket from the previous day is still valid

    def get_early(stop_id):
        earliest_depature = 25 * 60  # next day
        for stop_id, timetable in network.stops[stop_id].items():
            timetable.sort()
            idx = 0
            while idx < len(timetable) and timetable[idx].departure < end_of_day:
                idx += 1
            # found the next departure
            if idx < len(timetable):
                earliest_depature = min(timetable[idx].departure, earliest_depature)
        return earliest_depature

    # to_series as, as the stop_id is the index
    in_area["first_departure"] = in_area.index.to_series().apply(get_early)
    in_area["first_departure_hour"] = in_area["first_departure"] // 60  # only the hour

    get_plot_legend(in_area[in_area["first_departure_hour"] != 25],
                    # remove departures in hour 25 as this is tha value if no earlier one was found. e.g.night busses that run before 2:50 in the night
                    "first_departure_hour", map_box, kind="points", title="Earliest Depature (after 02:50)",
                    legend_title="First Departure Hour", unit_name=":00", outname="earliest_departures")


def get_num_connections_plot(network, in_area, map_box):
    def get_num_connected_nodes(stop_id):
        # for iid , _ in network.stops[stop_id].items():
        #    print(stops_data.loc[iid]["Name"])
        return len(network.stops[stop_id].items())

    in_area["num_connections"] = in_area.index.to_series().apply(get_num_connected_nodes)
    with_connections = in_area[in_area["num_connections"] > 0]
    get_plot_colorbar(with_connections, "num_connections", map_box, kind="points",
                      title="Number of connected nodes\n(also counting stations outside of shown area)",
                      outname="num_connections")


def get_fastest_route_plot(network, stops_data, start_times, start_station_name, stop_station_name):
    start = find_closest_station_id_by_name(start_station_name, stops_data)
    stop = find_closest_station_id_by_name(stop_station_name, stops_data)
    map_box = (49.8488, 8.560719, 49.931479, 8.90061)  # area around Darmstadt including Dieburg
    rows = []

    for t in start_times:
        route = network.get_fastest_route(start, t, stop)
        # trace back the route to draw it on the map
        current_stop = stop
        while current_stop != start:
            previous_stop = route[current_stop][1]  # element 0 is arrival time
            # append to dataframe
            rows.append([stops_data.loc[previous_stop, "Latitude"], stops_data.loc[previous_stop, "Longitude"],
                         stops_data.loc[current_stop, "Latitude"], stops_data.loc[current_stop, "Longitude"],
                         minutes_to_time(t)])
            current_stop = previous_stop

    # to pandas dataframe
    route_data = pd.DataFrame(rows,
                              columns=["Latitude_start", "Longitude_start", "Latitude_stop", "Longitude_stop",
                                       "start_time"])
    get_plot_legend(route_data, "start_time", map_box, kind="lines",
                    title=f"Fastest Route from {stops_data.loc[start, 'Name']} to {stops_data.loc[stop, 'Name']}",
                    legend_title="Start Time",
                    outname="fastest_route")


def get_num_vehicles_plot(network, in_area, map_box):
    # number of vehicles on this network section per day
    network_frequencies = {}
    for stop_id, row in in_area.iterrows():
        for connected_stop, timetable in network.stops[stop_id].items():
            if connected_stop in in_area.index:  # only connections inside the area
                if (stop_id, connected_stop) in network_frequencies:
                    network_frequencies[(stop_id, connected_stop)] += len(timetable)
                elif (connected_stop, stop_id) in network_frequencies:
                    network_frequencies[(connected_stop, stop_id)] += len(timetable)
                else:
                    # add new entry
                    network_frequencies[(connected_stop, stop_id)] = len(timetable)
    # get coordinates of start and end
    rows = []
    for (stop1, stop2), num_vehicles in network_frequencies.items():
        if num_vehicles > 2:
            # cleaner visualization as some single or twice a day trips look wired on the map (this happens mostly in the night)
            rows.append([in_area.loc[stop1, "Latitude"], in_area.loc[stop1, "Longitude"],
                         in_area.loc[stop2, "Latitude"], in_area.loc[stop2, "Longitude"],
                         num_vehicles])

    # to pandas dataframe
    route_data = pd.DataFrame(rows,
                              columns=["Latitude_start", "Longitude_start", "Latitude_stop", "Longitude_stop",
                                       "num_vehicles"])
    get_plot_colorbar(route_data, "num_vehicles", map_box, kind="lines",
                      title=f"Number of Vehicles on route Per day",
                      outname="vehicles_per_day")


def get_reacable_in_plot(network, in_area, map_box, start_station_name):
    time_limit = 180
    start = find_closest_station_id_by_name(start_station_name, in_area)
    start_time = 9 * 60

    reachable_info = network.get_reachable_stations_in_time(start, start_time, time_limit)

    in_area["reachable_in"] = in_area.apply(
        # row.name is the station id
        lambda row: reachable_info[row.name][0] - start_time if row.name in reachable_info else pd.NA, axis=1)

    in_area.loc[start, "reachable_in"] = 1  # cannot visualize 0
    get_plot_colorbar(in_area.dropna(inplace=False),  # remove stations unreachable in time
                      # dont picture stations reachable too late
                      "reachable_in", map_box, kind="points",
                      title=f"Reachable form {in_area.loc[start, 'Name']} (starting {minutes_to_time(start_time)})",
                      legend_title="Reachable in minutes", outname="reachable_in")


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


def draw_data_points(map, ax, df, values_col, cmap=None, norm=None, colordict=None):
    for _, row in tqdm(df.iterrows(), total=len(df)):
        lat, lon = row["Latitude"], row["Longitude"]
        x, y = map.to_pixels(lat, lon)

        value = row[values_col]
        if colordict is None:
            assert norm is not None
            assert cmap is not None
            color = cmap(norm(value))
        else:
            assert norm is None
            assert cmap is None
            color = colordict[value]
        ax.plot(x, y, 'o', color=color, ms=10, mew=0.5, alpha=.5)


def draw_data_lines(map, ax, df, values_col, cmap=None, norm=None, colordict=None):
    for _, row in tqdm(df.iterrows(), total=len(df)):
        lat1, lon1 = row["Latitude_start"], row["Longitude_start"]
        x1, y1 = map.to_pixels(lat1, lon1)
        lat2, lon2 = row["Latitude_stop"], row["Longitude_stop"]
        x2, y2 = map.to_pixels(lat2, lon2)

        value = row[values_col]
        if colordict is None:
            assert norm is not None
            assert cmap is not None
            color = cmap(norm(value))
        else:
            assert norm is None
            assert cmap is None
            color = colordict[value]
        ax.plot([x1, x2], [y1, y2], '-', color=color, linewidth=2, alpha=.75)


def add_colorbar(ax, norm, cmap, legend_title):
    cax = inset_axes(ax,
                     width="5%",  # width of colorbar relative to parent axes
                     height="50%",  # height of colorbar relative to parent axes
                     loc='upper right',
                     borderpad=2)
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    plt.colorbar(sm, cax=cax, label=legend_title)


def add_legend(ax, colordict, unit_name, legend_title):
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label=f"{key}{unit_name}",
               markerfacecolor=color, markersize=10)
        for key, color in colordict.items()
    ]
    ax.legend(handles=legend_elements, title=legend_title)


def save_plot(filename):
    # write to file
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        # ignore the warning about tight layout as the result looks satisfactory
        # inset_axes will plate the colorbar inside the map, so no real problem with a tight_layout
        plt.tight_layout()
    plt.savefig(f"{filename}.png")


def get_plot_colorbar(df, values_col, map_box, kind="points", title="", legend_title="", outname="plot",
                      colormap_name="plasma"):
    print(f"Draw Plot: {title}")
    norm = mcolors.LogNorm(
        vmin=df[values_col].min(),
        vmax=df[values_col].max()
    )
    cmap = matplotlib.colormaps[colormap_name]

    map, ax = draw_map(map_box, title)
    if kind == "points":
        draw_data_points(map, ax, df, values_col, cmap=cmap, norm=norm)
    if kind == "lines":
        draw_data_lines(map, ax, df, values_col, cmap=cmap, norm=norm)

    add_colorbar(ax, norm, cmap, legend_title)
    save_plot(outname)


def get_plot_legend(df, values_col, map_box, kind="points", title="", legend_title="", unit_name="", outname="plot",
                    colormap_name="tab10"):
    print(f"Draw Plot: {title}")
    unique_values = sorted(df[values_col].unique())
    n_colors = len(unique_values)
    colors = matplotlib.colormaps[colormap_name]
    colordict = {value: colors(i) for i, value in enumerate(unique_values)}

    map, ax = draw_map(map_box, title)
    if kind == "points":
        draw_data_points(map, ax, df, values_col, colordict=colordict)
    if kind == "lines":
        draw_data_lines(map, ax, df, values_col, colordict=colordict)
    add_legend(ax, colordict, unit_name, legend_title)
    save_plot(outname)


if __name__ == '__main__':
    main()
