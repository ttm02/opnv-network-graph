# opnv-network-graph

compute all stations reachable from a given one in the allowed timeframe

build_full_network.py : reads in the Data in NeTEx (Network Timetable Exchange) format into a python shelve database

analyze_graph.py analyzes the resulting database, see --help for usage instructions

# data source for timetable data:
https://www.opendata-oepnv.de/ht/de/organisation/delfi/startseite?tx_vrrkit_view%5Baction%5D=details&tx_vrrkit_view%5Bcontroller%5D=View&tx_vrrkit_view%5Bdataset_name%5D=deutschlandweite-sollfahrplandaten&cHash=b9c9f5a01f93b45c83381b244ddf0606

## Other Ideas for visualization

* Visualize where vehicles tend to spend the most time waiting.
* Simulate small delays and see how they propagate—where do delays cause systemic problems? (tight transfers?)
* Get some data on vehicles on streets per day and compare to buses per day