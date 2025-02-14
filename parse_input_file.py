# initial test how to read in the data

import pandas as pd
from lxml import etree

import datetime

file_to_read="data/20250210_fahrplaene_gesamtdeutschland/126_HEAGTRAM/NX-PI-01_DE_NAP_LINE_126-HEAGTRAM-6_20250208.xml"

xml_namespace="{http://www.netex.org.uk/netex}"


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

line_data=dict()
# multiple stop_points can refer to the same stop (e.g. multiple platforms)
stop_points=dict()
stops=dict()

def get_line_info_from_file(file_to_read):
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
            # re format onl the part before |
            name = name[:name.index("|")]
            stop_points[id] = name
            #de:06411:24200

            #DE::StopPlace:380024454_1000

            #ScheduledStopPointRef
          #to StopPlaceRef

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
        for point in get_single_children(journey,"pointsInSequence"):
            stop_point_id=point.get("ref")
            stop_point_loc = get_single_children(point,"ScheduledStopPointRef").get("ref")
            journey_stops.append((stop_point_id,stop_point_loc))
        assert id not in journeys
        journeys[id]= journey_stops



    site_frame = get_single_children(frame,"SiteFrame")
    assert get_frame_type(site_frame) =="epip:EU_PI_STOP"
    for stop in get_single_children(site_frame,"stopPlaces"):
        id = stop.get("id")
        global_id_kv= get_single_children(get_single_children(stop,"keyList"),"KeyValue")
        assert get_single_children(global_id_kv,"Key").text =="GlobalID"
        global_id = get_single_children(global_id_kv,"Value").text =="GlobalID"
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
        for time_info in get_single_children(journey,"passingTimes"):
            stop_ref=get_single_children(time_info,"StopPointInJourneyPatternRef").get("ref")
            arrival= get_single_children_value_or_none(time_info,"ArrivalTime")
            if arrival is not None:
                arrival=datetime.time.fromisoformat(arrival)
            depature=get_single_children_value_or_none(time_info,"DepartureTime")
            if depature is not None:
                depature = datetime.time.fromisoformat(depature)



get_line_info_from_file(file_to_read)