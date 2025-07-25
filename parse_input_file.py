# initial test how to read in the data

from lxml import etree

from datetime import datetime
from network import Network, time_to_minutes

xml_namespace = "{http://www.netex.org.uk/netex}"

date_format = "%Y-%m-%dT00:00:00"


# returns a network object
def consolidate_data(line_data, stop_points, stops, journeys, trips):
    network = Network(None)

    for trip_id, (pattern, trip) in trips.items():
        assert pattern in journeys
        line_id, journey_pattern = journeys[pattern]
        assert len(trip) == len(journey_pattern)
        for i in range(len(trip) - 1):
            (stop_from, _, depature) = trip[i]
            (stop_to, arrival, _) = trip[i + 1]
            assert arrival is not None
            assert depature is not None
            assert stop_from is not None
            assert stop_to is not None

            # get global id of stops
            assert journey_pattern[i][0] == stop_from
            stop_from = journey_pattern[i][1]
            if not isinstance(stop_points[stop_from], list):
                stop_from = "UNKNOWN"
            else:
                stop_from = stop_points[stop_from][0]
                stop_from = stops[stop_from]["global_id"]

            assert journey_pattern[i + 1][0] == stop_to
            stop_to = journey_pattern[i + 1][1]
            if not isinstance(stop_points[stop_to], list):
                stop_to = "UNKNOWN"
            else:
                stop_to = stop_points[stop_to][0]
                stop_to = stops[stop_to]["global_id"]

            network.add_connection(stop_from, stop_to, depature, arrival, line_data[line_id]["Name"],
                                   line_data[line_id]["type"])

    return network


def get_single_children(root, child_type, allow_none=False):
    chlds = [c for c in root.getchildren() if c.tag == xml_namespace + child_type]
    if not allow_none and len(chlds) != 1:
        raise ValueError("Parsing error in {}".format(root))
    elif len(chlds) == 0:
        return None
    else:
        return chlds[0]


def get_single_children_value_or_none(root, child_type):
    chlds = [c for c in root.getchildren() if c.tag == xml_namespace + child_type]
    if len(chlds) == 1:
        return chlds[0].text
    else:
        return None


def get_frame_type(frame):
    return get_single_children(frame, "TypeOfFrameRef").get("ref")


# TODO one could clean unused code, where fields are imported that are not used later

def get_line_info_from_file(file_to_read, date_to_use):
    line_data = dict()
    # multiple stop_points can refer to the same stop (e.g. multiple platforms)
    stop_points = dict()
    stops = dict()

    tree = etree.parse(file_to_read)
    root = tree.getroot()
    assert root.get("version") == "ntx:1.1"
    composite_frame = get_single_children(get_single_children(root, "dataObjects"), "CompositeFrame")
    # check that this is indeed a line definition
    assert get_frame_type(composite_frame) == "epip:EU_PI_LINE_OFFER"

    frame = get_single_children(composite_frame, "frames")

    # ResourceFrame # vehicleTypes # listet die verwendeten Fahrzugtypen

    service_frame = get_single_children(frame, "ServiceFrame")
    assert get_frame_type(service_frame) == "epip:EU_PI_NETWORK"

    for line in get_single_children(service_frame, "lines"):
        id = line.get("id")
        name = get_single_children(line, "Name").text
        type = get_single_children(line, "TransportMode").text
        assert id not in line_data
        line_data[id] = {"Name": name, "type": type, "schedule": []}

    # parse stop data
    for stop in get_single_children(service_frame, "scheduledStopPoints"):
        id = stop.get("id")
        if id not in stop_points:
            name = get_single_children(stop, "Name").text
            stop_points[id] = name

    # link stop to places
    # check if liks are missing
    stop_assignment = get_single_children(service_frame, "stopAssignments", allow_none=True)
    if stop_assignment is None:
        # could not read data
        return Network(None)

    for stop in stop_assignment:
        scheduled_stop_point = get_single_children(stop, "ScheduledStopPointRef").get("ref")
        stop_place = get_single_children(stop, "StopPlaceRef").get("ref")
        assert scheduled_stop_point in stop_points
        stop_points[scheduled_stop_point] = [stop_place, stop_points[scheduled_stop_point]]

    # parse the stop links
    for link in get_single_children(service_frame, "serviceLinks"):
        origin = get_single_children(link, "FromPointRef").get("ref")
        dest = get_single_children(link, "ToPointRef").get("ref")

    journeys = dict()
    for journey in get_single_children(service_frame, "journeyPatterns"):
        journey_stops = []
        id = journey.get("id")
        line_id = get_single_children(get_single_children(journey, "RouteView"), "LineRef").get("ref")
        for point in get_single_children(journey, "pointsInSequence"):
            stop_point_id = point.get("id")
            stop_point_loc = get_single_children(point, "ScheduledStopPointRef").get("ref")
            journey_stops.append((stop_point_id, stop_point_loc))
        assert id not in journeys
        journeys[id] = (line_id, journey_stops)

    site_frame = get_single_children(frame, "SiteFrame")
    assert get_frame_type(site_frame) == "epip:EU_PI_STOP"
    for stop in get_single_children(site_frame, "stopPlaces"):
        id = stop.get("id")
        # if some stations are defined multiple times
        if id not in stop_points or stops[id]["Name"] == "UNKNOWN":
            global_id_kl = get_single_children(stop, "keyList", allow_none=True)
            if global_id_kl is not None:
                global_id_kv = get_single_children(global_id_kl, "KeyValue")
                assert get_single_children(global_id_kv, "Key").text == "GlobalID"
                global_id = get_single_children(global_id_kv, "Value").text
                name = get_single_children(stop, "Name").text
                centeroid = get_single_children(stop, "Centroid", allow_none=True)
                if centeroid is not None:
                    loc = get_single_children(centeroid, "Location")
                    lat = get_single_children(loc, "Latitude").text
                    lon = get_single_children(loc, "Longitude").text
                else:
                    lat = "0"
                    lon = "0"
                stops[id] = {"Name": name, "lat": lat, "lon": lon, "global_id": global_id}
            else:
                stops[id] = {"Name": "UNKNOWN", "lat": "0", "lon": "0", "global_id": "UNKNOWN"}

    # add a default stop
    stops["UNKNOWN"] = {"Name": "UNKNOWN", "lat": "0", "lon": "0", "global_id": "UNKNOWN"}

    # read in <dayTypes> from ServiceCalendarFrame
    day_types = dict()
    operating_periods = dict()
    service_calendar_frame = get_single_children(frame, "ServiceCalendarFrame")
    assert get_frame_type(service_calendar_frame) == "epip:EU_PI_CALENDAR"
    ## UicOperatingPeriod are the dates
    # DayTypeAssignment are the assignment of operatingeriods to day Types
    calendar = get_single_children(service_calendar_frame, "ServiceCalendar")
    for period in get_single_children(calendar, "operatingPeriods"):
        id = period.get("id")
        from_date = datetime.strptime(get_single_children_value_or_none(period, "FromDate"), date_format).date()
        to_date = datetime.strptime(get_single_children_value_or_none(period, "ToDate"), date_format).date()
        valid_day_bits = get_single_children_value_or_none(period, "ValidDayBits")
        assert len(valid_day_bits) == (to_date - from_date).days + 1  # +1 as date range is inclusive
        valid_day = 0
        if from_date <= date_to_use <= to_date:
            valid_day = int(valid_day_bits[(date_to_use - from_date).days])
        operating_periods[id] = valid_day
    for assignment in get_single_children(calendar, "dayTypeAssignments"):
        op_period = get_single_children(assignment, "OperatingPeriodRef").get("ref")
        day_type = get_single_children(assignment, "DayTypeRef").get("ref")
        assert op_period is not None and day_type is not None
        day_types[day_type] = operating_periods[op_period]

    # parse timetable
    trips = dict()
    timetable_frame = get_single_children(frame, "TimetableFrame")
    assert get_frame_type(timetable_frame) == "epip:EU_PI_TIMETABLE"
    # < dayTypes >
    for journey in get_single_children(timetable_frame, "vehicleJourneys"):
        id = journey.get("id")
        valid_for_date = False
        pattern = get_single_children(journey, "ServiceJourneyPatternRef").get("ref")
        for day_type_node in get_single_children(journey, "dayTypes"):
            if day_types[day_type_node.get("ref")]:
                valid_for_date = True
        assert pattern in journeys

        if valid_for_date:
            journey_stops = []
            for time_info in get_single_children(journey, "passingTimes"):
                stop_ref = get_single_children(time_info, "StopPointInJourneyPatternRef").get("ref")
                arrival = get_single_children_value_or_none(time_info, "ArrivalTime")
                if arrival is not None:
                    arrival = time_to_minutes(arrival)
                depature = get_single_children_value_or_none(time_info, "DepartureTime")
                if depature is not None:
                    depature = time_to_minutes(depature)
                journey_stops.append((stop_ref, arrival, depature))
            trips[id] = (pattern, journey_stops)

    network = consolidate_data(line_data, stop_points, stops, journeys, trips)
    return network
