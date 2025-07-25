import difflib
import typing
from typing import Optional, Tuple

import pandas as pd
import smopy
import diskcache

# helper functions for converting times
midnight = 24 * 60


def minutes_to_time(minutes: int) -> str:
    """
    Converts minutes since midnight to HH:MM format.

    Args:
        minutes (int): Minutes since midnight.

    Returns:
        str: Formatted time string (e.g., "08:30").
    """
    return f"{minutes // 60:02}:{minutes % 60:02}"


def time_to_minutes(time_str: str) -> int:
    """
    Converts a HH:MM time string to minutes since midnight.

    Args:
        time_str (str): Time string in format "HH:MM".

    Returns:
        int: Minutes since midnight.
    """
    h, m = map(int, time_str.split(':'))
    return h * 60 + m


def find_closest_station_id_by_name(target_name: str, df: pd.DataFrame) -> Optional[str]:
    """
    Finds the closest station ID for the given name, either a station with the given name exist or it returns station with a similar name.

    Args:
        target_name (str): Station name to find.
        df (pd.DataFrame): Dataframe with station data.

    Returns:
        Optional[str]: ID of suitable station if found, None Otherwise.
    """
    # Check if 'Name' column exists
    if 'Name' not in df.columns:
        raise ValueError("The DataFrame must have a 'Name' column.")

    # Try exact match first
    exact_match = df[df["Name"] == target_name]
    if not exact_match.empty:
        return exact_match.index[0]  # Return the index of the exact match

    # Find the closest match
    closest_match = difflib.get_close_matches(target_name, df["Name"], n=1, cutoff=0.5)

    if closest_match:
        return df[df["Name"] == closest_match[0]].index[0]  # Return the index== station ID of the closest match

    return None  # No close match found


# Round to this many decimal places to consider maps "similar"
COORD_ROUND_PRECISION = 4

# caches the used maps on disk, so that we don't have to re-download it again
cache = diskcache.Cache("map_cache")


def get_map(map_box: typing.Tuple[float, float, float, float]) -> smopy.Map:
    """
    Get a suitable map for the given coordinates.

    Args:
        map_box (tuple): Lat1 Lon1 Lat2 Lon2 defining the boundaries of the map.

    Returns:
        smopy.Map: Map object
    """
    rounded_box = tuple(round(coord, COORD_ROUND_PRECISION) for coord in map_box)

    with diskcache.Cache(cache.directory) as map_cache:
        if rounded_box not in map_cache:
            map_cache[rounded_box] = smopy.Map(rounded_box)  # download new map from openstreetmap
        return map_cache[rounded_box]
