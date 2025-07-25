from __future__ import annotations

import typing
from typing import Optional
from dataclasses import dataclass
import shelve
from heapq import heappush, heappop

from typing_extensions import TypeAlias
from utils import midnight


# a dataclass to define the information of a single connection
@dataclass(order=True, frozen=True)
class Connection:
    departure: int
    arrival: int
    line: str
    transport_type: str


# type aliases for ease of readability of the type annotations
Timetable: TypeAlias = typing.List[Connection]
ConnectionsDict: TypeAlias = typing.Dict[str, Timetable]
ReachableMap: TypeAlias = typing.Dict[str, typing.Tuple[int, str]]


class Network:
    def __init__(self, stops_file: Optional[str]) -> None:
        """
        Initializes the Network. If `stops_file` is given, it loads the network from a shelve file.
        Otherwise, initializes an empty network for manual building.

        Args:
            stops_file (Optional[str]): Path to a shelve file or None for an empty network.
        """
        if stops_file is None:
            self.stops = dict()  # empty network to build one
        else:
            self.stops = shelve.open(stops_file)

    def get_connections(self, stop_id: str) -> ConnectionsDict:
        """
        Returns all connections from a given stop.

        Args:
            stop_id (str): The stop ID to query.

        Returns:
            dict: Keys are connected stop IDs, values are lists of (departure, arrival, line, type) tuples.
        """
        return self.stops[stop_id]

    def get_reachable_stations_in_time(self, start_point: str, start_time: int, time_limit: int) -> ReachableMap:
        """
        Computes all reachable stations from a start point within a given time limit.

        Args:
            start_point (str): Starting stop ID.
            start_time (int): Time in minutes since midnight.
            time_limit (int): Time limit in minutes.

        Returns:
            dict: stop_id → (arrival_time, previous_stop_id)
        """
        return self._dijkstra(start_point, start_time, "", time_limit)

    def get_fastest_route(self, start_point: str, start_time: int, end_point: str) -> ReachableMap:
        """
        Computes the fastest route from start to end using Dijkstra search.

        Args:
            start_point (str): Starting stop ID.
            start_time (int): Start time in minutes since midnight.
            end_point (str): Destination stop ID.

        Returns:
            dict: stop_id → (arrival_time, previous_stop_id)
        """
        # end of search is 4 days, which should be sufficient to reach any other stop in germany
        return self._dijkstra(start_point, start_time, end_point, 4 * 24 * 60)

    def _dijkstra(self, start_point: str, start_time: int, end_point: str, time_limit: int) -> ReachableMap:
        """
        Dijkstra’s algorithm to compute the shortest paths
        see https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
        """
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
                timetable.sort()  # sort by departure
                idx = 0
                while idx < len(timetable) and timetable[idx].departure < cur_time:
                    idx += 1
                # found the next departure, check if it is still in bounds
                if idx < len(timetable) and timetable[idx].departure < end_time:
                    earliest_arrival = timetable[idx].arrival
                    cur_dep_time = timetable[idx].departure
                    # day wrap around (e.g. a night train)
                    if earliest_arrival < cur_dep_time:
                        earliest_arrival = earliest_arrival + midnight  # +1 Day
                    idx += 1
                    while cur_dep_time < earliest_arrival and idx < len(timetable):
                        assert timetable[idx].departure >= cur_dep_time
                        # is there a later connection that runs faster (unlikely but possible)
                        cur_dep_time = timetable[idx].departure
                        arrival2 = timetable[idx].arrival
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

    def get_stops(self) -> list:
        """
        Returns all stop IDs in the network.

        Returns:
            list: List of stop IDs.
        """
        return list(self.stops.keys())

    # code below is only needed to build the network from timetable data

    def remove_stop(self, to_remove_stop_id: str) -> None:
        """
        Removes a stop and all connections to/from it.

        Args:
            to_remove_stop_id (str): Stop ID to remove.
        """
        for stop_id, connections in self.stops.items():
            connections.pop(to_remove_stop_id, None)
        self.stops.pop(to_remove_stop_id, None)

    def _add_stop(self, stop_id: str) -> None:
        """
        Adds a new stop with no outgoing connections.

        Args:
            stop_id (str): New stop ID.
        """
        assert stop_id not in self.stops
        self.stops[stop_id] = {}

    def add_connection(self, stop_id_from: str, stop_id_to: str, departure: int, arrival: int, line: str,
                       transport_type: str) -> None:
        """
        Adds a connection between two stops.

        Args:
            stop_id_from (str): Origin stop ID.
            stop_id_to (str): Destination stop ID.
            departure (int): Departure time in minutes.
            arrival (int): Arrival time in minutes.
            line (str): Line number.
            transport_type (str): Transport type (e.g., bus, train).
        """
        if not stop_id_from in self.stops:
            self._add_stop(stop_id_from)
        if not stop_id_to in self.stops:
            self._add_stop(stop_id_to)

        if stop_id_to not in self.stops[stop_id_from]:
            self.stops[stop_id_from][stop_id_to] = []
        self.stops[stop_id_from][stop_id_to].append(Connection(departure, arrival, line, transport_type))

    def merge(self, other: Network) -> None:
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
