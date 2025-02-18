import ijson


class Network:
    def __init__(self, filename):
        self.file = open(filename, "r")
        self.stops = dict()

    def __del__(self):
        self.file.close()

    def _get_connections_for_stop(self, stop):
        if stop not in self.stops:
            # search for the correct timetable in the json
            self.file.seek(0)
            self.stops[stop] = {k: v for k, v in ijson.kvitems(self.file, stop)}
            # sport the timetables
            for conn in self.stops[stop]:
                self.stops[stop][conn].sort()
        return self.stops[stop]

    def get_reachable_stations_in_time(self, start_point, start_time, time_limit):
        end_time = start_time + time_limit
        if end_time > 24 * 60:
            raise ValueError("Time limit exceeds midnight")
        # (time,node)
        reachable_stations = [start_point]
        to_visit = [(start_time, start_point)]
        while len(to_visit) > 0:
            to_visit.sort()  # make sure we remove the item with the lowest travel time
            cur_time, visiting = to_visit.pop()
            for stop_id, timetable in self._get_connections_for_stop(visiting).items():
                idx = 0
                # TODO use binary search?
                while idx < len(timetable) and timetable[idx][0] < cur_time:
                    idx += 1
                # found the next departure check if it is still in bounds
                if idx < len(timetable) and timetable[idx][0] < end_time:
                    earliest_arrival = timetable[idx][1]
                    cur_dep_time = timetable[idx][0]
                    # no day wrap around (e.g. a night train)
                    if earliest_arrival < cur_dep_time:
                        earliest_arrival = 24 * 60 + 1  # sometime AFTER midnight (will be ruled out if no faste connection due to time limit)
                    idx += 1
                    while cur_dep_time < earliest_arrival and idx < len(timetable):
                        # is there a later connection that runs faster (unlikely but possible)
                        # no day wrap around (e.g. night trains)
                        if timetable[idx][1] > cur_dep_time:
                            earliest_arrival = min(earliest_arrival, timetable[idx][1])
                            cur_dep_time = timetable[idx][0]
                        idx += 1
                    # found the earliest arrival
                    if earliest_arrival <= end_time:
                        if stop_id not in reachable_stations:
                            reachable_stations.append(stop_id)
                            to_visit.append((earliest_arrival, stop_id))
                        else:
                            ## update arrival time
                            # need to find time to update
                            for idx in range(len(to_visit)):
                                if to_visit[idx][1] == stop_id:
                                    if to_visit[idx][0] > earliest_arrival:
                                        # update time
                                        to_visit[idx] = (earliest_arrival, stop_id)

                                    break
                else:
                    pass
                    # no further connection today
        return reachable_stations


# Convert minutes back to HH:MM
def minutes_to_time(minutes):
    return f"{minutes // 60:02}:{minutes % 60:02}"
