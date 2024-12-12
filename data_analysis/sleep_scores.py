"""
Takes sleep data for a night and calculates scores
- default callback period of 7 days for webapp
"""

import numpy as np
from datetime import datetime, timedelta
from data_handling.data_recall import sleep_times, date_list



# Convert minutes to HH:MM format
def format_time(minutes):
    hours = int((minutes // 60) % 24)
    mins = int(minutes % 60)
    return f"{hours:02d}:{mins:02d}"



def st_devs(date, callback_period = 7):
    """
    Calculates one of the 5 metrics outlined in the return_5_metrics function. Also returns nighly duration, sleep and wake times
    Parameters:
    str: day to calculate for
    int: number of prev days to include in calculation

    Returns:
    dict: StDevs - {"StDev_onset": float, "StDev_offset": float, "StDev_duration": float, "values": {"duration": [], "sleep_times": [], "wake_times": []}}
    """

    # obtain sleep and wake times for last X nights - default 7. date format YYYY-MM-DD
    dates = date_list(date, callback_period)
    sleep_time_dict = {}

    for date in dates:
        sleep_time_dict[str(date)] = sleep_times(date)

    # calculate st dev for sleep and wake times
    sleep_times_array = []
    wake_times_array = []

    for day, time in sleep_time_dict.items():

        # extract sleep times, taking time in minutes before 00:00 as positive
        sleep_time_str = time['onset_time']
        sleep_time_obj = datetime.strptime(sleep_time_str, "%H:%M") # turn intp datetime
        minutes = sleep_time_obj.hour * 60 + sleep_time_obj.minute  # calculate the minutes from midnight
        
        if minutes > 12 * 60:
            minutes -= 24 * 60
        sleep_times_array.append(minutes*-1)
    
        # extract wake times, taking time past 00:00 as positive
        wake_time_str = time['offset_time']
        wake_time_obj = datetime.strptime(wake_time_str, "%H:%M") # turn intp datetime
        minutes = wake_time_obj.hour * 60 + wake_time_obj.minute  # calculate the minutes from midnight
        
        if minutes > 12 * 60:
            minutes -= 24 * 60
        wake_times_array.append(minutes)

    # print(sleep_times_array)
    # print(wake_times_array)

    # calculate duration
    duration_array = []

    for i in range(len(sleep_times_array)):
        dur = sleep_times_array[i] + wake_times_array[i]
        duration_array.append(dur)
    
    st_dev_duration = np.std(duration_array, ddof=1)
    # print(f"Duration array: {duration_array}")
    # print(st_dev_duration)

    # calc standard dev of sleep time
    st_dev_sleep = np.std(sleep_times_array, ddof=1)
    # print(f"sleep array: {sleep_times_array}")
    # print(st_dev_sleep)

    # calc standard dev of wake time 
    st_dev_wake = np.std(wake_times_array, ddof=1)
    # print(f"wake array: {wake_times_array}")
    # print(float(st_dev_wake))

    return {"StDev_onset": float(st_dev_sleep), "StDev_offset": float(st_dev_wake), "StDev_duration": float(st_dev_duration), "values": {"duration": duration_array, "sleep_times": sleep_times_array, "wake_times": wake_times_array}}


def generate_binary_sleep_wake(sleep_time, wake_time, epochs_per_day=24):
    """
    Generate binary sleep (0) vs awake (1) data for a single day based on sleep and wake times.

    Parameters:
    - sleep_time (str): Sleep time in "HH:MM" format.
    - wake_time (str): Wake time in "HH:MM" format.
    - epochs_per_day (int): Number of epochs per day (default: 24 for hourly resolution).

    Returns:
    - list: Binary sleep/awake data for the day (0 for sleep, 1 for awake).
    """
    sleep_dt = datetime.strptime(sleep_time, "%H:%M")
    wake_dt = datetime.strptime(wake_time, "%H:%M")

    # Handle cases where bedtime is after midnight
    if wake_dt <= sleep_dt:
        wake_dt += timedelta(days=1)

    # Create epoch intervals
    epoch_duration = 1440 // epochs_per_day  # Duration of each epoch in minutes
    binary_data = []

    for minute in range(0, 1440, epoch_duration):
        # Generate the timestamp for the current epoch
        current_time = (datetime.min + timedelta(minutes=minute)).time()

        # Determine sleep or awake status
        if sleep_dt.time() <= current_time < wake_dt.time() or (
            sleep_dt.time() > wake_dt.time() and (current_time >= sleep_dt.time() or current_time < wake_dt.time())
        ):
            binary_data.append(0)  # Sleep
        else:
            binary_data.append(1)  # Awake

    # print(f"Binrary data: {binary_data}")

    return binary_data


def binary_sleep_wake_list(date, epochs, callback_period = 7):



    # generate date list for the callback period
    reference_date = datetime.strptime(date, "%Y-%m-%d")
    date_list = [(reference_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(callback_period)]

    # Generate binary data for all days
    binary_sleep_wake_list = []

    for date in date_list:
        sleep_time = sleep_times(date)['onset_time']
        wake_time = sleep_times(date)['offset_time']
        binary_data = generate_binary_sleep_wake(sleep_time, wake_time, epochs)
        binary_sleep_wake_list.append(binary_data)

    # If only one night of data is provided, IS = 1
    if len(binary_sleep_wake_list) == 1:
        return 1.0

    return binary_sleep_wake_list



def interdaily_stability(date, callback_period = 7):
    """
    Calculate interdaily stability (IS) metric. IS evaluates the degree to which an individual's sleep or activity pattern aligns with a consistent daily rhythm.
    It assesses the regularity of these patterns across multiple days.

    Parameters:
    - date (Str): day to calculate from - from 00:00 to 23:59
    - callback_period (int): days preceeding date for which to calculate IS

    Returns:
    - float: The calculated IS value. Closer to 1 indicates more regular 
    """
    epochs_per_day = 24

    binary_sw_list = binary_sleep_wake_list(date, epochs_per_day, callback_period)

    # Flatten the data to compute the overall mean (X̄)
    all_data = np.concatenate(binary_sw_list)
    overall_mean = np.mean(all_data)  # X̄

    # print("Binary Sleep/Wake List:", binary_sleep_wake_list)

    # Compute hourly means across all days (X̄_h)
    hourly_means = []

    for epoch in range(epochs_per_day):
        hourly_values = [day[epoch] for day in binary_sw_list if len(day) > epoch]
        hourly_means.append(np.mean(hourly_values))

    # Numerator: Variance of hourly means across days, scaled by N
    N = len(binary_sw_list)  # Number of days
    numerator = N * np.sum((np.array(hourly_means) - overall_mean) ** 2)

    #  print(f"overall:{overall_mean}")
    # Denominator: Total variance of all data, scaled by p
    p = epochs_per_day
    denominator = p * np.sum((all_data - overall_mean) ** 2)
    IS = numerator / denominator if denominator > 0 else 0  # Handle edge case if denominator is zero
    return IS


def calculate_sleep_midpoint(sleep_time, wake_time):
    """
    Calculate the sleep midpoint given sleep and wake times.

    Parameters:
    - sleep_time (str): Sleep time in "HH:MM" format.
    - wake_time (str): Wake time in "HH:MM" format.

    Returns:
    - datetime.time: The sleep midpoint as a time object.
    """
    sleep_dt = datetime.strptime(sleep_time, "%H:%M")
    wake_dt = datetime.strptime(wake_time, "%H:%M")

    # Handle next-day wake time
    if wake_dt <= sleep_dt:
        wake_dt += timedelta(days=1)

    duration = wake_dt - sleep_dt
    midpoint = sleep_dt + duration / 2
    return midpoint.time()


def social_jet_lag(date, callback_period = 7):
    """
    Social jet lag is the mismatch in average midsleep timing between workdays and free days
    Free days are classified as saturday and sunday 

    Parameters:
    - date (str): day to calculate from - from 00:00 to 23:59
    - callback_period (int): days over which to calculate

    Returns:
    - float: Social Jet Lag (SJL) in hours (can be positive or negative).
    """

    # obtain list of sleep and wake time pairs
    time_dict = {}

    # generate date list
    dates = date_list(date, callback_period)

    # iterate date list to generate list of sleep and wake pairs
    for date in dates:
        new_times = sleep_times(date)
        time_dict[date] = ((new_times['onset_time'], new_times['offset_time']))

    #  print(time_dict)

    workday_midpoints = []
    freeday_midpoints = []

    # calculate midpoint for each night, handling sleep time past midnight
    for date, times in time_dict.items():
        sleep_time = times[0]
        wake_time = times[1]
        midpoint = calculate_sleep_midpoint(sleep_time, wake_time)

        # Determine if the date is a workday or free day
        date_dt = datetime.strptime(date, "%Y-%m-%d")
        if date_dt.weekday() in [5, 6]:  # Saturday (5) and Sunday (6)
            freeday_midpoints.append(midpoint)
        else:
            workday_midpoints.append(midpoint)

    # Convert midpoints to hours for averaging
    work_midpoint_avg = sum(mp.hour + mp.minute / 60 for mp in workday_midpoints) / len(workday_midpoints) if workday_midpoints else 0
    free_midpoint_avg = sum(mp.hour + mp.minute / 60 for mp in freeday_midpoints) / len(freeday_midpoints) if freeday_midpoints else 0

    # Calculate SJL
    sjl = free_midpoint_avg - work_midpoint_avg
    return sjl

#  print(social_jet_lag('2024-12-01', 1))


def composite_phase_dev(date, callback_period = 7):

    return 0


def sleep_regularity_index(date, callback_period = 7):
    
    return 0



def sleep_score():
    """
    Calculates holistic sleep score for a night
    
    Parameters:

    
    Returns:
    float: Calculated sleep score between 0 and 100
    """

    return


def optimal_bedtime(date, callback_period = 7):
    """
    Takes st dev in sleep, wake time and midpoint for last 7 days
    Takes target sleep duration
    Returns optimal bedtime and waketime

    """

   # Parse the input date and calculate the target date 3 days later
    target_date = datetime.strptime(date, '%Y-%m-%d') + timedelta(days=3)
    today = datetime.strptime(date, '%Y-%m-%d')
    days_to_target = (target_date - today).days

    if days_to_target < 0 or days_to_target > 3:
        raise ValueError("The input date should be within 3 days of the target date.")
    
    stdev_7_days = st_devs(date, 7)

    # calc avg wake time
    wake_times = stdev_7_days['values']['wake_times']
    avg_wake_time = sum(wake_times) / len(wake_times)

    # calc avg sleep time
    sleep_times = stdev_7_days['values']['sleep_times']
    avg_sleep_time = sum(sleep_times) / len(sleep_times)

    # call each of the sleep score metrics for the last 7 day average value

    stdev_wake_time = stdev_7_days['StDev_offset']
    stdev_sleep_time = stdev_7_days['StDev_onset']

    # SJL in minutes
    sjl_minutes = social_jet_lag(date, callback_period) * 60

  # Target sleep duration (adjust slightly for SJL)
    target_sleep_duration = 480  # 8 hours in minutes
    if abs(sjl_minutes) > 30:  # Adjust duration if SJL is significant
        target_sleep_duration += -10 if sjl_minutes > 0 else 10  # Small adjustment

    # Calculate the ideal midpoint
    avg_midpoint = (avg_sleep_time + avg_wake_time) / 2
    ideal_midpoint = avg_midpoint - sjl_minutes / 2  # Adjust midpoint based on SJL

    # Calculate bedtime and wake time
    ideal_bedtime = ideal_midpoint - target_sleep_duration / 2
    ideal_wake_time = ideal_midpoint + target_sleep_duration / 2

    # Gradual adjustment factor based on days to target
    adjustment_factor = 1 / days_to_target

    # Adjust bedtime and wake time gradually toward ideal values
    optimized_bedtime = avg_sleep_time + adjustment_factor * (ideal_bedtime - avg_sleep_time)
    optimized_wake_time = avg_wake_time + adjustment_factor * (ideal_wake_time - avg_wake_time)

    # Reduce variability by nudging toward averages
    optimized_bedtime -= stdev_sleep_time * adjustment_factor
    optimized_wake_time -= stdev_wake_time * adjustment_factor

    # Ensure sleep duration aligns with adjusted times
    optimized_sleep_duration = (optimized_wake_time - optimized_bedtime) % (24 * 60)  # Handle midnight rollover

    return {
        "sleep_duration": optimized_sleep_duration,
        "bedtime": format_time(optimized_bedtime),
        "wake_time": format_time(optimized_wake_time)
    }



