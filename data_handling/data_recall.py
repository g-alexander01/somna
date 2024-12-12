"""
Contains helper functions to return required data for different functions
"""

import json
import datetime
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

file_path = "HealthData/Sleep"




def date_list(start_date, period):
    """
    Takes a date and returns a list of dates preceeding that by X days, week by default
    """


    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    dates = [(start_date_obj - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(period)]
    
    return dates


def extract_HHMM(timestamp):

    # take UTC timestamp and extract HH:MM
    return timestamp.strftime("%H:%M")


def convert_to_local(UTC_time):
    """
    Converts a UTC timestamp to the specified local time zone.
    """
    # print(UTC_time)
    utc_time = datetime.fromisoformat(UTC_time).replace(tzinfo=timezone.utc)
    local_time = utc_time.astimezone(ZoneInfo("Europe/London"))
    updated_time = local_time + timedelta(hours=1)

    return updated_time




def sleep_times(date):
    """
    Return the onset and offset times for nights sleep
    """

    # garmin stores time in UTC, but at time of project are UTC+1

    file = "sleep_" + str(date) + ".json"

    with open(file_path + "/" + file, 'r') as file:
            data = json.load(file)

    # extract the sleepMovement array
    sleep_movement = data.get('sleepMovement', [])
    
    if not sleep_movement:
        return None, None  # return None if the array is empty

    # get the first and last timestamps directly in ISO fromat 
    first_timestamp = sleep_movement[0].get('startGMT')
    last_timestamp = sleep_movement[-1].get('endGMT')

    # convert time
    # print(f"last tstamp: {last_timestamp}")
    new_first = convert_to_local(first_timestamp[:-2])
    new_last = convert_to_local(last_timestamp[:-2])

    # extract the HH:MM
    onset = extract_HHMM(new_first)
    offset = extract_HHMM(new_last)
    # print(f"onset_time: {onset}, offset_time: {offset}")

    return {"onset_time": onset, "offset_time": offset}


