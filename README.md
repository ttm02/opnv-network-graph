# opnv-network-graph

compute all stations reachable from a given one in the allowed timeframe

build_full_network.py : reads in the Data in NeTEx (Network Timetable Exchange) format into a python shelve database

analyze_graph.py analyzes teh resulting database, see --help for usage instructions


## Other Ideas for visualization

* function give me all/possible connections from A to B weighted waiting times after little wait vs fastest connection, few changes
* remove duplication of visualization with city A and city B
* Visualize routes
* Visualize intersections (e.g. important network nodes)
* Frequency of departures
* Visualize where vehicles tend to spend the most time waiting.
* Frequency or wait time for a specific station over the course of a day
* Show how the 30-minute reachable area from a stop changes across the day (e.g. 7am vs 2pm vs 9pm).
* At what point is the area no longer accessible in the evening
* Density of stops
* Simulate small delays and see how they propagate—where do delays cause systemic problems? (tight transfers?)
* Use population density data (e.g. https://ghsl.jrc.ec.europa.eu) to show what stops serve the most number of people
