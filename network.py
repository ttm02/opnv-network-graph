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

            # duplicates can be removed later
            # nevertheless there should not be any duplicated anyway
            # self.stops[stop_id]=list(set( self.stops[stop_id]))

    def remove_unknown(self):
        for stop_id, connections in self.stops.items():
            connections.pop("UNKNOWN", None)
        self.stops.pop("UNKNOWN",None)

# Convert HH:MM to minutes since midnight
def time_to_minutes(time_str):
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

# Convert minutes back to HH:MM
def minutes_to_time(minutes):
    return f"{minutes // 60:02}:{minutes % 60:02}"

#TODO better name
class LookupNetwork:
    def __init__(self, network):
        self.stops = dict()
        if isinstance(network,Network):
            for stop_id, connections in network.stops.items():
                self.stops[stop_id] = dict()
                for connecting_stop, timetable in connections.items():
                    new_timetable= []
                    for conn in timetable:
                        start_time =time_to_minutes(conn[0])
                        end_time =time_to_minutes(conn[1])
                        new_timetable.append((start_time,end_time, conn[2], conn[3]))
                    #de-duplicate
                    new_timetable = list(set(new_timetable))
                    new_timetable.sort()
                    self.stops[stop_id][connecting_stop] = new_timetable
                    print(new_timetable)
        else:
            raise TypeError("Network must be of type Network")