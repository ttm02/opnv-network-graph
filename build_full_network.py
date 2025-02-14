
import os
from parse_input_file import get_line_info_from_file
from network import Network

file_to_read="data/20250210_fahrplaene_gesamtdeutschland/126_HEAGTRAM/NX-PI-01_DE_NAP_LINE_126-HEAGTRAM-6_20250208.xml"

dir_to_read="data/20250210_fahrplaene_gesamtdeutschland/126_HEAGTRAM"

network = Network()

for root, dirs, files in os.walk(dir_to_read):
    path = root.split(os.sep)
    for file in files:
        qualified_path= os.path.join(root, file)
        print("Read "+ qualified_path)
        network = get_line_info_from_file(qualified_path)

network = get_line_info_from_file(file_to_read)