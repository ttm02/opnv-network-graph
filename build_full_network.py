import datetime
import os
from time import strftime
import zipfile
from datetime import datetime

import pandas as pd
from tqdm import tqdm

import shelve

from parse_input_file import get_line_info_from_file
from network import Network
import pickle
import json
from concurrent.futures import ProcessPoolExecutor, as_completed

#TODO argparse for these settings
file_to_read = "data/20250721_fahrplaene_gesamtdeutschland.zip"
use_parallel_processing = True
# 4 batches per worker, as the files have different sizes (mostly depending on frequency of the respective service)
batches_per_worker = 4

date_to_use = datetime.strptime("2025-10-22", "%Y-%m-%d").date()  # a Wednesday outside of Holidays


def process_xml_batch(xml_files):
    local_network = Network(None)
    with zipfile.ZipFile(file_to_read, 'r') as zip_file:
        for xml_file in xml_files:
            local_network.merge(get_line_info_from_file(zip_file.open(xml_file), date_to_use))
    return local_network


network = Network(None)
print("Read Timetable Data ...")
with zipfile.ZipFile(file_to_read, 'r') as zip_file:
    xml_files = [f for f in zip_file.namelist() if f.endswith(".xml")]

    num_workers = os.cpu_count()
    batch_size = len(xml_files) // (num_workers * batches_per_worker)
    print("Batch_size %i" % batch_size)
    # batch the xml_files
    batches = [xml_files[i:i + batch_size] for i in range(0, len(xml_files), batch_size)]

    if not use_parallel_processing:
        for batch in tqdm(batches):
            network.merge(process_xml_batch(batch))
    else:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            # dynamic scheduling of batches
            futures = {executor.submit(process_xml_batch, b): b for b in batches}

            # retrieve results in any order
            for future in tqdm(as_completed(futures), total=len(batches)):
                try:
                    result = future.result()
                    network.merge(result)  # Merge results globally
                except Exception as e:
                    print(f"Error processing Files: {e}")
                    exit(1)

print("Read Station Positions")
stops_data = pd.read_csv("data/20250721_zHV_gesamt/zHV_aktuell_csv.2025-07-21.csv",
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

with shelve.open('network.db') as db:
    for key, value in network.stops.items():
        db[key] = value
# with open('network.json', 'w') as f:
#    json.dump(network.stops, f)

# and the stops
stops_data.to_csv("stops.csv")

print("done")
