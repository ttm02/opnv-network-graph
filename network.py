from bisect import bisect_left


class stop:
    def __init__(self, stop_id, stop_name, stop_lat, stop_lon):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.stop_lat = stop_lat
        self.stop_lon = stop_lon
        self.connections = []


class Network:
    def __init__(self):
        self.stops = dict()
        # needed for building

    def set_stops(self,stops):
        assert len(self.stops)==0
        self.stops = stops
        for stop,connections in stops.items():
            for connection,timetable in connections.items():
                timetable.sort()

    def _add_stop(self, stop_id):
        assert stop_id not in self.stops
        self.stops[stop_id] = {}

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

    def remove_unknown(self):
        for stop_id, connections in self.stops.items():
            connections.pop("UNKNOWN", None)
        self.stops.pop("UNKNOWN", None)


    def get_reachable_stations_in_time(self,start_point,start_time,time_limit):
        end_time = start_time + time_limit
        #(time,node)
        reachable_stations = [start_point]
        to_visit = [(start_time,start_point)]
        while len(to_visit) > 0:
            to_visit.sort()# make sure we remove teh item with lowest travel time
            cur_time,visiting= to_visit.pop()
            for stop_id,timetable in self.stops[visiting].items():
                idx = 0
                #TODO use binary search?
                while idx < len(timetable) and timetable[idx][0] < cur_time:
                    idx += 1
                # found the next departure
                if idx < len(timetable):
                    earliest_arrival = timetable[idx][1]
                    cur_dep_time = timetable[idx][0]
                    idx += 1
                    while cur_dep_time < earliest_arrival and idx < len(timetable):
                        # is there a later connection that runs faster (unlikely but possible)
                        earliest_arrival = min(earliest_arrival,timetable[idx][1])
                        cur_dep_time = timetable[idx][0]
                        idx += 1
                    # found the earliest arrival
                    if earliest_arrival <= end_time:
                        if stop_id not in reachable_stations:
                            reachable_stations.append(stop_id)
                            to_visit.append((earliest_arrival,stop_id))
                        else:
                            ## update arrival time
                            # need to find time to update
                            for idx in range(len(to_visit)):
                                if to_visit[idx][1] == stop_id:
                                    if to_visit[idx][0] > earliest_arrival:
                                        # update time
                                        to_visit[idx] = (earliest_arrival,stop_id)

                                    break
                else:
                    pass
                    #no further connection today
        return reachable_stations

# Convert minutes back to HH:MM
def minutes_to_time(minutes):
    return f"{minutes // 60:02}:{minutes % 60:02}"
