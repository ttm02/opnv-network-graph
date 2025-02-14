# initial test how to read in the data

import pandas as pd
from lxml import etree

file_to_read="data/20250210_fahrplaene_gesamtdeutschland/126_HEAGTRAM/NX-PI-01_DE_NAP_LINE_126-HEAGTRAM-6_20250208.xml"

tree = etree.parse(file_to_read)
root = tree.getroot()
assert root.get("version") == "ntx:1.1"
xml_namespace="http://www.netex.org.uk/netex"

def get_single_children(root, child_type):
    chlds = [c for c in root.getchildren() if c.tag == xml_namespace+child_type]
    print(chlds)
    assert len(chlds) == 1
    return chlds[0]



def get_frame_type(frame):
    return (frame,"TypeOfFrameRef").get("ref")

line_data=dict()
stops=dict()
def get_line_info_from_file(data):

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
        if id not in stops:
            name = get_single_children(stop,"Name").text
            # re format onl the part before |
            name = name[:name.index("|")]
            stops[id] = name
            #de:06411:24200

            #DE::StopPlace:380024454_1000

            #ScheduledStopPointRef
          #to StopPlaceRef

    # link stop to places
    for stop in get_single_children(service_frame,"stopAssignments"):
        scheduled_stop_point = get_single_children(stop,"ScheduledStopPointRef").get("ref")
        stop_place = get_single_children(stop,"StopPlaceRef").get("ref")
        assert scheduled_stop_point in stops
        stops[scheduled_stop_point] = [stop_place,stops[scheduled_stop_point]]

    # parse the stop links
    for link in get_single_children(service_frame,"serviceLinks"):
        origin = get_single_children(link,"FromPointRef").get("ref")
        dest = get_single_children(link,"ToPointRef").get("ref")

    journeys=dict()
    for journey in get_single_children(service_frame,"journeyPatterns"):
        journes_stops= []
        id = journey.get("id")
        for point in get_single_children(journey,"pointsInSequence"):
            journes_stops.append(get_single_children(point,"ScheduledStopPointRef").get("ref"))
        assert id not in journeys
        journeys[id]= journes_stops


    site_frame = get_single_children(composite_frame,"SiteFrame")
    assert get_frame_type(site_frame) =="epip:EU_PI_STOP"


    #print (stops)





get_line_info_from_file(file_to_read)