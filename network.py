class stop:
    def __init__(self, stop_id, stop_name, stop_lat, stop_lon):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.stop_lat = stop_lat
        self.stop_lon = stop_lon
        self.connections =[]

class Network:
    def __init__(self):
        self.stops = dict()
        # for statistics
        self.num_edges=0

    def _add_stop(self,stop_id):
        assert stop_id not in self.stops
        self.stops[stop_id]= {}

    def add_connection(self,stop_id_from,stop_id_to,depature,arrival,line,type):
        self.num_edges += 1

        if not stop_id_from in self.stops:
            self._add_stop(stop_id_from)
        if not stop_id_to in self.stops:
            self._add_stop(stop_id_to)

        if stop_id_to not in self.stops[stop_id_from]:
            self.stops[stop_id_from][stop_id_to]=[]
        self.stops[stop_id_from][stop_id_to].append((depature,arrival,line,type))









