
import os
from parse_input_file import get_line_info_from_file
from network import Network

file_to_read="data/20250210_fahrplaene_gesamtdeutschland/126_HEAGTRAM/NX-PI-01_DE_NAP_LINE_126-HEAGTRAM-6_20250208.xml"
dir_to_read="data/20250210_fahrplaene_gesamtdeutschland/126_HEAGTRAM"
#dir_to_read="data/20250210_fahrplaene_gesamtdeutschland"

network = Network()
all_stops={}

for root, dirs, files in os.walk(dir_to_read):
    path = root.split(os.sep)
    for file in files:
        if file.endswith(".xml"):
            qualified_path= os.path.join(root, file)
            print("Read "+ qualified_path)
            new_network,stops = get_line_info_from_file(qualified_path)
            network.merge(new_network)
            for stop_id,info in stops.items():
                if stop_id not in all_stops:
                    all_stops[stop_id] = info
                else:
                    assert(all_stops[stop_id] == info)

print("stops:")
print(len(all_stops))

print(all_stops)
