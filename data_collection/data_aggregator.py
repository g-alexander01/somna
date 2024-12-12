"""
Combine data from bedroom and garmin sources into one datasheet
"""



# data_handling/data_collection.py
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import subprocess
import requests
from data_handling.data_recall import sleep_times 
from data_analysis.sleep_scores import sleep_regularity_index, social_jet_lag, st_devs, optimal_bedtime, composite_phase_dev, interdaily_stability

# Get current date and time in London timezone
london_timezone = ZoneInfo("Europe/London")


# thingspeak
channel_id = "2769273"  
api_key = "Y9BRF2CSL00WMO2X"  

save_path="data_handling/night_sensor_data"


def encoded_timestamp(date, time):
    """
    Combines a date and time into a URL-encoded ISO 8601 timestamp format.

    Parameters:
    - date_str (str): Date in "YYYY-MM-DD" format.
    - time_str (str): Time in "HH:MM" or "HH:MM:SS" format.

    Returns:
    - str: URL-encoded timestamp (e.g., "2024-12-06%20%07:00:00").
    """
    # Ensure time includes seconds
    if len(time.split(":")) == 2:
        time += ":00"  # Add seconds if not present

    # Combine date and time
    full_datetime = f"{date}T{time}"

    # Convert to datetime object to validate
    dt = datetime.fromisoformat(full_datetime)

    # Format with URL encoding for the space
    return dt.strftime("%Y-%m-%d%%20%H:%M:%S")



# Example function to fetch data from GarminDB
def fetch_garmin_data():
    """
    Runs the garmindb_cli.py command to download, import, and analyze the latest data.
    
    Returns:
    - str: The output of the command execution.
    """
    try:
        # Define the command to be executed
        command = ["garmindb_cli.py", "--all", "--download", "--import", "--analyze", "--latest"]
        
        # Run the command using subprocess
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # Return the command's output
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    

# Example function to fetch data from ThingSpeak
def fetch_night_data(date):
    """
    Fetches data from ThingSpeak between specified sleep and wake times and saves it to a CSV.

    Parameters:
    - channel_id (str): The ThingSpeak channel ID.
    - sleep_time (str): Start time in ISO 8601 format (e.g., "2024-12-01T07:16:00.0").
    - wake_time (str): End time in ISO 8601 format (e.g., "2024-12-01T07:16:00.0").
    - api_key (str): The Read API Key (required for private channels).

    Returns:
    - str: Path to the saved CSV file.
    """
    # obtain sleep and wake time for given date
    # print(date)
    
    sleep_data = sleep_times(date)  # Replace with your date
    sleep_time = encoded_timestamp(date, sleep_data["onset_time"]) 
    wake_time = encoded_timestamp(date, sleep_data["offset_time"])
    
    print(sleep_time)
    print(wake_time)




    
    try:
        
        # Parse ISO 8601 inputs into datetime objects
        print(f"sleeptime: {sleep_time}")
        print(f"waketime: {wake_time}")

        # Construct the ThingSpeak API URL
        url = f"https://api.thingspeak.com/channels/{channel_id}/feeds.csv?api_key={api_key}&start={sleep_time}&end={wake_time}"
        print(url)
        response = requests.get(url)

        # Ensure the save directory exists
        os.makedirs(save_path, exist_ok=True)

        # Define the file name 
        file_name = f"nightdata_{date}.csv"
        print(file_name)

        # Save the data to a CSV file
        with open(save_path + "/" + file_name, "wb") as file:
            file.write(response.content)
        print(f"CSV successfully saved to: {save_path}")
        return save_path

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Error processing data: {e}")
        return None
    


# Function to update CSV with new data
def update_data():

    # todays date
    current_time_in_london = datetime.now(london_timezone)
    date = current_time_in_london.date()

    five_metrics_csv_path="data_handling/sleep_metrics.csv"
    
    # Fetch data from GarminDB
    fetch_garmin_data()

    # Fetch data from ThingSpeak
    fetch_night_data(date)


    # write all sleep variables to sleep_metrics.csv 

    # Check if the file exists
    if not os.path.exists(five_metrics_csv_path):
        # If the file doesn't exist, create it with headers
        columns = [
            "Date", "StDevs", "StDev_onset", "StDev_offset", "StDev_duration",
            "IS", "SJL", "CPD", "SRI", "optimal_bedtime", "optimal_sleeptime"
        ]
        df = pd.DataFrame(columns=columns)
        df.to_csv(five_metrics_csv_path, index=False)
    else:
        # Read the existing CSV
        df = pd.read_csv(five_metrics_csv_path)

    # Check if the date exists in the file
    if date not in df["Date"].values:
        print(f"Date {date} not found in the file. Computing and adding data...")
        
        # Call the functions to compute data for the date

        standard_devs = st_devs(date)

        stdev_onset = standard_devs['StDev_onset']
        stdev_offset = standard_devs['StDev_offset']
        stdev_duration = standard_devs['StDev_duration']
        int_stab = interdaily_stability(date)
        sjl = social_jet_lag(date)
        cpd = composite_phase_dev(date)
        sri = sleep_regularity_index(date)

        optimal_time = optimal_bedtime(date)
        optimal_bed= optimal_time['bedtime']
        optimal_wake = optimal_time['wake_time']
        
        # Create a new row with the computed data
        new_row = {
            "Date": date,
            "StDev_onset": stdev_onset,
            "StDev_offset": stdev_offset,
            "StDev_duration": stdev_duration,
            "IS": int_stab,
            "SJL": sjl,
            "CPD": cpd,
            "SRI": sri,
            "optimal_bedtime": optimal_bed,
            "optimal_waketime": optimal_wake
        }
        
        # Convert the dictionary to a DataFrame with a single row
        new_row_df = pd.DataFrame([new_row])

        # Append to the CSV file
        new_row_df.to_csv(five_metrics_csv_path, mode='a', header=False, index=False)
        print(f"Data for {date} successfully added.")

        print(f"Data for {date} successfully added.")
    else:
        print(f"Date {date} already exists in the file.")



def compare_enviro_data(date):

    # get bedroom environment data from last night
    enviro_path = 'data_handling/night_sensor_data/nightdata_' + f'{date}' + '.csv'




    return

# if __name__ == "__main__":
#     update_csv()


# date_list = ['2024-11-25', '2024-11-26', '2024-11-27', '2024-11-28', '2024-11-29', '2024-11-30', '2024-12-01']
# for date in date_list:
#     # fetch_night_data(date)
#     update_data(date)

