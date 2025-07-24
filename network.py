import shelve
from bisect import bisect_left
from heapq import heappush, heappop


class stop:
    def __init__(self, stop_id, stop_name, stop_lat, stop_lon):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.stop_lat = stop_lat
        self.stop_lon = stop_lon
        self.connections = []


# TODO documentation
# TODO the network has no accessible arrival data e.g. searching for the arrivals of a stop is difficult

midnight = 24 * 60


class Network:
    def __init__(self):
        self.stops = dict()
        # needed for building

    def set_stops(self, stops_file):
        self.stops = shelve.open(stops_file)

    def get_stops(self):
        return list(self.stops.keys())

    def remove_stop(self, to_remove_stop_id):
        for stop_id, connections in self.stops.items():
            connections.pop(to_remove_stop_id, None)
        self.stops.pop(to_remove_stop_id, None)

    def _add_stop(self, stop_id):
        assert stop_id not in self.stops
        self.stops[stop_id] = {}

    # returns a dict key = connected stop values= list of connections each as a tuple: (depature, arrival (at next stop), line number, transport type)
    def get_connections(self, stop_id):
        return self.stops[stop_id]

    def add_connection(self, stop_id_from, stop_id_to, depature, arrival, line, type):
        if not stop_id_from in self.stops:
            self._add_stop(stop_id_from)
        if not stop_id_to in self.stops:
            self._add_stop(stop_id_to)

        if stop_id_to not in self.stops[stop_id_from]:
            self.stops[stop_id_from][stop_id_to] = []
        self.stops[stop_id_from][stop_id_to].append((depature, arrival, line, type))

    def merge(self, other):
        for stop_id, connections in other.stops.items():
            if stop_id not in self.stops:
                self._add_stop(stop_id)
            for connecting_stop, timetable in connections.items():
                if connecting_stop not in self.stops[stop_id]:
                    self.stops[stop_id][connecting_stop] = []
                    # concat lists
                self.stops[stop_id][connecting_stop] += timetable
                # de-duplicate
                self.stops[stop_id][connecting_stop] = list(set(self.stops[stop_id][connecting_stop]))

            # duplicates can be removed later
            # nevertheless there should not be any duplicated anyway
            # self.stops[stop_id]=list(set( self.stops[stop_id]))

    def get_reachable_stations_in_time(self, start_point, start_time, time_limit):
        return self.dijkstra(start_point, start_time, None, time_limit)

    def get_fastest_route(self, start_point, start_time, end_point):
        # end of search is 4 days
        return self.dijkstra(start_point, start_time, end_point, 4 * 24 * 60)

    def dijkstra(self, start_point, start_time, end_point, time_limit):
        end_time = start_time + time_limit
        # (arrival time, from node)
        reachable_stations = {start_point: (start_time, start_point)}
        # (time,node)
        to_visit = []
        heappush(to_visit, (start_time, start_point))  # first node to visit
        visited = set()
        while len(to_visit) > 0:
            cur_time, visiting = heappop(to_visit)
            if visiting == end_point:
                break  # terminate search: found the endpoint
            if visiting in visited:
                # already visited
                continue
                # this implementation keeps multiple instances of this node in the priority queue.
                # This way don't actually need to update the priorities, but just insert a new instance with different priority
                # python does not offer an update priority implementation
            visited.add(visiting)
            for stop_id, timetable in self.stops[visiting].items():
                timetable.sort()
                idx = 0
                # TODO use binary search?
                while idx < len(timetable) and timetable[idx][0] < cur_time:
                    idx += 1
                # found the next departure, check if it is still in bounds
                if idx < len(timetable) and timetable[idx][0] < end_time:
                    earliest_arrival = timetable[idx][1]
                    cur_dep_time = timetable[idx][0]
                    # day wrap around (e.g. a night train)
                    if earliest_arrival < cur_dep_time:
                        earliest_arrival = earliest_arrival + midnight  # +1 Day
                    idx += 1
                    while cur_dep_time < earliest_arrival and idx < len(timetable):
                        assert timetable[idx][0] >= cur_dep_time
                        # is there a later connection that runs faster (unlikely but possible)
                        cur_dep_time = timetable[idx][0]
                        arrival2 = timetable[idx][1]
                        if arrival2 < cur_dep_time:
                            arrival2 = arrival2 + midnight  # +1 Day
                        earliest_arrival = min(earliest_arrival, arrival2)
                        idx += 1
                    # found the earliest arrival
                    if earliest_arrival <= end_time:
                        if stop_id not in reachable_stations:
                            reachable_stations[stop_id] = (earliest_arrival, visiting)
                            heappush(to_visit, (earliest_arrival, stop_id))
                        else:
                            ## update arrival time
                            # need to find time to update
                            old_time = reachable_stations[stop_id][0]
                            if old_time > earliest_arrival:
                                reachable_stations[stop_id] = (earliest_arrival, visiting)
                                heappush(to_visit, (earliest_arrival, stop_id))
                else:
                    pass
                    # no further connection today
        return reachable_stations


# Convert minutes back to HH:MM
def minutes_to_time(minutes):
    return f"{minutes // 60:02}:{minutes % 60:02}"
