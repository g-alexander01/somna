"""
Takes environment data for a night and calculates score
"""

# import sensor readings for last night

# take sensor readings and calculate averages for each metric

# using ideal values from reseach, calculate the delta
# next steps could lie in taking input from user if they were too warm or too cold to adjust

# determine which one is greatest delta and suggest improvement 
# under assumption that day-to-day temp / conditions dont change too much
# next steps in aligning with weather forecast 


ideal_conditions = {
    'temperature': 19,
    'humidity': 60
}


def diff_to_ideal(temperature, humidity):

    # Calculate differences from ideal conditions
    temp_diff = temperature - ideal_conditions['temperature']
    humidity_diff = humidity - ideal_conditions['humidity']

    # Initialize intervention levels
    temp_intervention = 0
    humidity_intervention = 0

    # Determine temperature intervention level
    if abs(temp_diff) > 3:  # Significant deviation
        temp_intervention = 2
    elif abs(temp_diff) > 1:  # Moderate deviation
        temp_intervention = 1

    # Determine humidity intervention level
    if abs(humidity_diff) > 10:  # Significant deviation
        humidity_intervention = 2
    elif abs(humidity_diff) > 5:  # Moderate deviation
        humidity_intervention = 1

    print(temp_diff)

    intervention = recommend_action(temp_intervention, humidity_intervention)


    # Return differences and intervention levels
    return {
        'temperature_difference': temp_diff,
        'humidity_difference': humidity_diff,
        'temperature_intervention': intervention['Temperature Recommendation'],
        'humidity_intervention': intervention['Humidity Recommendation']
    }


def recommend_action(temp_diff, humidity_diff):
    """
    Friendly recommendations to improve temperature and humidity conditions.

    Args:
        temp_diff (float): Difference between the current and ideal temperature.
        humidity_diff (float): Difference between the current and ideal humidity.

    Returns:
        dict: Personalized recommendations for temperature and humidity adjustments.
    """
    # Define actions for temperature differences
    temp_actions = {
        (3, 100): "Try opening the bedroom window a bit more to cool things down. A breeze might help!",
        (1, 3): "Opening the bedroom door can improve airflow and make it a bit more comfortable.",
        (-100, -3): "It's chilly! Adding an extra blanket or wearing layers should keep you cozy.",
        (-3, -1): "It feels a bit cool. Another layer might be just what you need."
    }

    # Define actions for humidity differences
    humidity_actions = {
        (10, 100): "How about adding some plants to your room? They can help balance the humidity and make the space feel fresher.",
        (5, 10): "Cracking the bedroom window open could help reduce the humidity a touch.",
        (-100, -10): "The air seems dry. Drinking a glass of water before bed might keep you hydrated overnight.",
        (-10, -5): "Opening the bedroom door a bit can help reduce dryness and improve airflow."
    }

    # Find the appropriate action for temperature
    temp_action = next(
        (action for (low, high), action in temp_actions.items() if low <= temp_diff < high),
        "Your room temperature is spot on! No changes needed."
    )

    # Find the appropriate action for humidity
    humidity_action = next(
        (action for (low, high), action in humidity_actions.items() if low <= humidity_diff < high),
        "Your room humidity is perfect! No adjustments needed."
    )

    # Combine and return the recommendations
    return {
        "Temperature Recommendation": temp_action,
        "Humidity Recommendation": humidity_action
    }
