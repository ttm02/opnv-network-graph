import datetime
import os
from time import strftime
from tqdm import tqdm

from parse_input_file import get_line_info_from_file
from network import Network
import pickle
import json

file_to_read = "data/20250210_fahrplaene_gesamtdeutschland/126_HEAGTRAM/NX-PI-01_DE_NAP_LINE_126-HEAGTRAM-6_20250208.xml"
dir_to_read = "data/20250210_fahrplaene_gesamtdeutschland/126_HEAGTRAM"
#dir_to_read = "data/20250210_fahrplaene_gesamtdeutschland"

network = Network()
all_stops = {}

# Pre-count total files
total_files = sum(len(files) for _, _, files in os.walk(dir_to_read))

with tqdm(total=total_files, desc="Parse files", unit="files") as pbar:
    for root, dirs, files in os.walk(dir_to_read):
        path = root.split(os.sep)
        for file in files:
            if file.endswith(".xml"):
                qualified_path = os.path.join(root, file)
                # print("Read " + qualified_path)
                new_network, stops = get_line_info_from_file(qualified_path)
                network.merge(new_network)
                for stop_id, info in stops.items():
                    if stop_id not in all_stops:
                        all_stops[stop_id] = info
                    else:
                        pass
                        # there is some ambiguity in the data regarding stop naming
                        # assert (all_stops[stop_id] == info)

            pbar.update(1)

print("Write Result to Json file...")


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.time):
            return obj.strftime("%H:%M")  # Convert to string
        return super().default(obj)


with open('network.json', 'w') as f:
    json.dump(network.stops, f, cls=CustomJSONEncoder)
with open('stations.json', 'w') as f:
    json.dump(all_stops, f)

print("done")
