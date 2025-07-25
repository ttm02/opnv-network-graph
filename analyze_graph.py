import argparse
import json
import difflib
from typing import Optional

from matplotlib import pyplot as plt
from tqdm import tqdm
import pandas as pd
from network import Network
from utils import time_to_minutes, minutes_to_time,find_closest_station_id_by_name
import smopy


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

    print("Compute stations reachable in %i min from %s ..." % (time_limit, stops_data.loc[start_station, "Name"]))

    reachable = network.get_reachable_stations_in_time(start_station, start_time, time_limit)
    print("%i Stations are reachable" % len(reachable))
    print("Draw map")

    min_lat = 180
    min_long = 180
    max_lat = -180
    max_long = -180

    coordinates = []
    for station in reachable:
        lat = stops_data.loc[station]["Latitude"]
        lon = stops_data.loc[station]["Longitude"]
        coordinates.append((lat, lon))

        min_lat = min(min_lat, lat)
        min_long = min(min_long, lon)
        max_lat = max(max_lat, lat)
        max_long = max(max_long, lon)

    # area to plot
    map_box = (min_lat, min_long, max_lat, max_long)
    # print(map_box)
    map = smopy.Map(map_box)

    # figsize is used for resolution
    ax = map.show_mpl(figsize=(24, 24))

    # TODO annotation is not working correctly
    ax.annotate(
        "Reachable from %s (%s) until %s (%i stops)" % (
            stops_data.loc[start_station, "Name"],
            minutes_to_time(start_time),
            minutes_to_time(start_time + time_limit),
            len(reachable)),
        xy=(0.5, 1.02),  # Position relative to axes (centered above the map)
        xycoords="axes fraction",
        fontsize=24,
        ha="center",  # Center horizontally
        va="bottom",  # Position below the top edge
    )

    for lat, lon in coordinates:
        x, y = map.to_pixels(lat, lon)
        ax.plot(x, y, 'or', ms=10, mew=2)

    plt.savefig(args.output)


if __name__ == '__main__':
    main()
