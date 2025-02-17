import argparse
import json
import difflib

from matplotlib import pyplot as plt
from tqdm import tqdm
import pandas as pd
from network import Network
import smopy


def find_closest_station_id_by_name(target_name, df):
    # Check if 'Name' column exists
    if 'Name' not in df.columns:
        raise ValueError("The DataFrame must have a 'Name' column.")

    # Try exact match first
    exact_match = df[df["Name"] == target_name]
    if not exact_match.empty:
        return exact_match.index[0]  # Return the index of the exact match

    # Find closest match
    closest_match = difflib.get_close_matches(target_name, df["Name"], n=1, cutoff=0.5)

    if closest_match:
        return df[df["Name"] == closest_match[0]].index[0]  # Return the index of the closest match

    return None  # No close match found


# Convert HH:MM to minutes since midnight
def time_to_minutes(time_str):
    h, m = map(int, time_str.split(':'))
    return h * 60 + m


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--network_file', default='network.json', required=False)
    parser.add_argument('--stations_file', default='data/20250210_zHV_gesamt/zHV_aktuell_csv.2025-02-10.csv',
                        required=False)
    parser.add_argument('--time_limit', default=30, type=int, help='time limit in minutes', required=False)
    parser.add_argument('--start_time', default='09:00', type=str, help='start time in HH:MM', required=False)
    parser.add_argument('--station', default='Frankfurt Hauptbahnhof', type=str, required=False)

    return parser.parse_args()


def main():
    args = parse_arguments()

    network = Network()
    print("Read Network data (Timetables)")
    with open(args.network_file, 'r') as f:
        network.set_stops(json.load(f))
    print("Read Station Positions")
    stops_data = pd.read_csv(args.stations_file,
                             delimiter=';', index_col="DHID",
                             usecols=["DHID", "Name", "Latitude", "Longitude"],
                             dtype={"DHID": str, "Name": str, "Latitude": float, "Longitude": float},
                             decimal=","
                             )
    stops_data.dropna(inplace=True)
    print("Cross-Reference Data")
    # only keep relevant ones
    stops_data = stops_data.loc[stops_data.index.isin(network.get_stops())]
    # and remove unknown stops
    valid_stops = set(stops_data.index)
    stops_to_remove = [stop for stop in network.get_stops() if stop not in valid_stops]
    for stop in tqdm(stops_to_remove):
        network.remove_stop(stop)

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
    # ax = map.show_mpl(figsize=(8,8))

    for lat, lon in coordinates:
        x, y = map.to_pixels(lat, lon)
        ax.plot(x, y, 'or', ms=10, mew=2)

    plt.show()
    plt.savefig('map.pdf')


if __name__ == '__main__':
    main()
