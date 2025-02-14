# initial test how to read in the data

import pandas as pd
from lxml import etree

import datetime

file_to_read="data/20250210_fahrplaene_gesamtdeutschland/126_HEAGTRAM/NX-PI-01_DE_NAP_LINE_126-HEAGTRAM-6_20250208.xml"

xml_namespace="{http://www.netex.org.uk/netex}"


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













# returns a network object
def consolidate_data(line_data,stop_points,stops,journeys,trips):
    network = Network()

    for trip_id,(pattern,trip) in trips.items():
        assert pattern in journeys
        line_id,journey_pattern = journeys[pattern]
        assert len(trip) == len(journey_pattern)
        for i in range(len(trip)-1):
            (stop_from, _, depature) = trip[i]
            (stop_to, arrival, _) = trip[i+1]
            assert arrival is not None
            assert depature is not None
            assert stop_from is not None
            assert stop_to is not None

            # get global id of stops
            assert journey_pattern[i][0]==stop_from
            stop_from = journey_pattern[i][1]
            stop_from= stop_points[stop_from][0]
            stop_from = stops[stop_from]["global_id"]

            assert journey_pattern[i+1][0] == stop_to
            stop_to = journey_pattern[i+1][1]
            stop_to = stop_points[stop_to][0]
            stop_to = stops[stop_to]["global_id"]

            network.add_connection(stop_from,stop_to,depature,arrival,line_data[line_id]["Name"],line_data[line_id]["type"])

    return network

def get_single_children(root, child_type):
    chlds = [c for c in root.getchildren() if c.tag == xml_namespace+child_type]
    assert len(chlds) == 1
    return chlds[0]

def get_single_children_value_or_none(root, child_type):
    chlds = [c for c in root.getchildren() if c.tag == xml_namespace+child_type]
    if len(chlds) == 1:
        return chlds[0].text
    else:
        return None

def get_frame_type(frame):
    return get_single_children(frame,"TypeOfFrameRef").get("ref")


#TODO one could clean unused code

def get_line_info_from_file(file_to_read):
    line_data = dict()
    # multiple stop_points can refer to the same stop (e.g. multiple platforms)
    stop_points = dict()
    stops = dict()

    tree = etree.parse(file_to_read)
    root = tree.getroot()
    assert root.get("version") == "ntx:1.1"
    composite_frame = get_single_children(get_single_children(root,"dataObjects"),"CompositeFrame")
    # check that this is indeed a line definition
    assert get_frame_type(composite_frame)=="epip:EU_PI_LINE_OFFER"

    frame = get_single_children(composite_frame,"frames")

    #ResourceFrame # vehicleTypes # listet die verwendeten Fahrzugtypen

    service_frame = get_single_children(frame,"ServiceFrame")
    assert get_frame_type(service_frame) =="epip:EU_PI_NETWORK"

    for line in get_single_children(service_frame,"lines"):
        id=line.get("id")
        name = get_single_children(line,"Name").text
        type = get_single_children(line,"TransportMode").text
        assert id not in line_data
        line_data[id] = {"Name": name,"type": type,"schedule":[]}

    # parse stop data
    for stop in get_single_children(service_frame,"scheduledStopPoints"):
        id = stop.get("id")
        if id not in stop_points:
            name = get_single_children(stop,"Name").text
            # re format only the part before |
            name = name[:name.index("|")]
            stop_points[id] = name

    # link stop to places
    for stop in get_single_children(service_frame,"stopAssignments"):
        scheduled_stop_point = get_single_children(stop,"ScheduledStopPointRef").get("ref")
        stop_place = get_single_children(stop,"StopPlaceRef").get("ref")
        assert scheduled_stop_point in stop_points
        stop_points[scheduled_stop_point] = [stop_place,stop_points[scheduled_stop_point]]

    # parse the stop links
    for link in get_single_children(service_frame,"serviceLinks"):
        origin = get_single_children(link,"FromPointRef").get("ref")
        dest = get_single_children(link,"ToPointRef").get("ref")

    journeys=dict()
    for journey in get_single_children(service_frame,"journeyPatterns"):
        journey_stops= []
        id = journey.get("id")
        line_id = get_single_children(get_single_children(journey,"RouteView"),"LineRef").get("ref")
        for point in get_single_children(journey,"pointsInSequence"):
            stop_point_id=point.get("id")
            stop_point_loc = get_single_children(point,"ScheduledStopPointRef").get("ref")
            journey_stops.append((stop_point_id,stop_point_loc))
        assert id not in journeys
        journeys[id]= (line_id,journey_stops)



    site_frame = get_single_children(frame,"SiteFrame")
    assert get_frame_type(site_frame) =="epip:EU_PI_STOP"
    for stop in get_single_children(site_frame,"stopPlaces"):
        id = stop.get("id")
        global_id_kv= get_single_children(get_single_children(stop,"keyList"),"KeyValue")
        assert get_single_children(global_id_kv,"Key").text =="GlobalID"
        global_id = get_single_children(global_id_kv,"Value").text
        name = get_single_children(stop,"Name").text
        loc = get_single_children(get_single_children(stop,"Centroid"),"Location")
        lat = get_single_children(loc,"Latitude").text
        lon = get_single_children(loc,"Longitude").text
        assert id not in stops
        stops[id] = {"Name": name ,"lat":lat,"lon":lon,"global_id":global_id}

    # parse timetable
    trips = dict()
    timetable_frame = get_single_children(frame, "TimetableFrame")
    assert get_frame_type(timetable_frame) == "epip:EU_PI_TIMETABLE"
    for journey in get_single_children(timetable_frame,"vehicleJourneys"):
        id=journey.get("id")
        pattern=get_single_children(journey,"ServiceJourneyPatternRef").get("ref")
        assert pattern in journeys
        journey_stops = []
        for time_info in get_single_children(journey,"passingTimes"):
            stop_ref=get_single_children(time_info,"StopPointInJourneyPatternRef").get("ref")
            arrival= get_single_children_value_or_none(time_info,"ArrivalTime")
            if arrival is not None:
                arrival=datetime.time.fromisoformat(arrival)
            depature=get_single_children_value_or_none(time_info,"DepartureTime")
            if depature is not None:
                depature = datetime.time.fromisoformat(depature)
            journey_stops.append((stop_ref,arrival,depature))
        trips[id] = (pattern,journey_stops)



    return consolidate_data(line_data,stop_points,stops,journeys,trips)

network = get_line_info_from_file(file_to_read)

print(network.num_edges)
print(network.stops["de:06411:4736"])