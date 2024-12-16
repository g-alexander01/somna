import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from data_collection.data_aggregator import update_data
from data_analysis.sleep_scores import optimal_bedtime, sleep_regularity_index, interdaily_stability, binary_sleep_wake_list
from data_analysis.environment_score import diff_to_ideal

# Schedule update daily at 09:00
# scheduler = BackgroundScheduler()
# scheduler.add_job(update_data, 'cron', hour=9)  # Schedule daily at 9 am
# scheduler.start()

# Set timezone to London and get the current date and time
london_timezone = ZoneInfo("Europe/London")
current_time_in_london = datetime.now(london_timezone)
current_date_in_london = current_time_in_london.date()

# Overwrite current_date_in_london for testing purposes
current_date_in_london = '2024-12-10'

#################################### SLEEP DATA ####################################
# Load last 7 days of binary sleep data to display (1 = awake, 0 = asleep)
binary_sleep_data = binary_sleep_wake_list(f'{current_date_in_london}', 24, 7)

# Load Sleep Regularity Index (SRI) and Interdaily Stability (IS)
sri = sleep_regularity_index(current_date_in_london)
is_metric = interdaily_stability(current_date_in_london)

# Obtain recommended optimal bedtime and wake time
opt_bedtime = optimal_bedtime(f'{current_date_in_london}')['bedtime']
opt_alarm = optimal_bedtime(f'{current_date_in_london}')['wake_time']


# interdaily stability metric for last 7 days 
interdaily_stab = interdaily_stability(current_date_in_london)




#################################### TEMP AND HUMIDITY ####################################
# Read night sensor data for temperature and humidity
nightdata_file_path = 'data_handling/night_sensor_data/nightdata_' + f'{current_date_in_london}' + '.csv'
try:
    df_nightdata = pd.read_csv(nightdata_file_path)
    df_environment = pd.DataFrame({
        "Time": pd.to_datetime(df_nightdata["created_at"]).dt.strftime('%H:%M'),
        "Temperature (°C)": df_nightdata["field1"],
        "Humidity (%)": df_nightdata["field2"]
    })
    avg_temperature = df_environment["Temperature (°C)"].mean()
    avg_humidity = df_environment["Humidity (%)"].mean()
except FileNotFoundError:
    df_environment = pd.DataFrame(columns=["Time", "Temperature (°C)", "Humidity (%)"])
    avg_temperature, avg_humidity = None, None
except Exception as e:
    raise RuntimeError(f"Error processing night sensor data: {e}")



# optimal temp and humidity data
environment_delta = diff_to_ideal(avg_temperature, avg_humidity)



#################################### TEMP AND HUMIDITY PLOT ####################################
temperature_humidity_plot = make_subplots(specs=[[{"secondary_y": True}]])
temperature_humidity_plot.add_trace(
    go.Scatter(
        x=df_environment["Time"],
        y=df_environment["Temperature (°C)"],
        mode="lines+markers",
        name="Temperature (°C)",
        line=dict(color="red")
    ),
    secondary_y=False
)
temperature_humidity_plot.add_trace(
    go.Scatter(
        x=df_environment["Time"],
        y=df_environment["Humidity (%)"],
        mode="lines+markers",
        name="Humidity (%)",
        line=dict(color="blue")
    ),
    secondary_y=True
)
temperature_humidity_plot.update_layout(
    title={
        'text': "Temperature and Humidity Trend Last Night",
        'x': 0.5,  # Center the title horizontally
        'xanchor': 'center',  # Align the anchor to the center
        'yanchor': 'top'  # Optional: Align the title vertically
    },
    xaxis_title="Time",
    yaxis=dict(title="Temperature (°C)"),
    yaxis2=dict(title="Humidity (%)"),
    legend_title="Metrics",
    hovermode="x unified",
    template="plotly_white",
    height=400,
    width=700
)

#################################### HEATMAP ####################################
heatmap = go.Figure(
    data=go.Heatmap(
        z=binary_sleep_data,
        colorscale=[[0, "green"], [1, "lightblue"]],  # Two discrete colors
        x=[f"{hour}:00" for hour in range(24)],
        y=[f"Day {7 - i}" for i in range(7)],
        showscale=True  # Disable the color scale bar
    )
)

heatmap.update_layout(
    title={
        'text': "Sleep/Wake Data (Last 7 Days)",
        'x': 0.5,  # Center the title horizontally
        'xanchor': 'center',  # Align the anchor to the center
        'yanchor': 'top'  # Optional: Align the title vertically
    },
    xaxis_title="Hour of the Day",
    yaxis_title="Day",
    xaxis=dict(tickangle=-45, ticks="outside", showgrid=True, gridcolor="lightgray", griddash="dash"),
    yaxis=dict(autorange="reversed", ticks="outside", showgrid=True, gridcolor="lightgray", griddash="dash"),
    template="plotly_white",
    height=300,
    width=600
)


#################################### TEXT DISPLAY ####################################
def create_text_display(time, label):
    return html.Div(
        style={
            "font-family": "Courier, monospace",
            "font-size": "24px",
            "text-align": "center",
            "border": "2px solid black",
            "padding": "10px",
            "margin": "10px",
            "background-color": "#f0f0f0",
            "width": "150px",
            "display": "inline-block",
            "box-shadow": "5px 5px 15px rgba(0,0,0,0.3)"
        },
        children=[
            html.Div(time, style={"font-weight": "bold"}),
            html.Div(label, style={"font-size": "16px"})
        ]
    )

def create_info_box(value, label):
    return html.Div(
        style={
            "font-family": "Arial, sans-serif",
            "font-size": "18px",
            "text-align": "center",
            "border": "2px solid black",
            "padding": "15px",
            "margin": "10px",
            "background-color": "#eaf7ff",
            "width": "200px",
            "display": "inline-block",
            "box-shadow": "3px 3px 10px rgba(0,0,0,0.2)"
        },
        children=[
            html.Div(f"{value:.2f}" if value is not None else "N/A", style={"font-weight": "bold"}),
            html.Div(label, style={"font-size": "16px"})
        ]
    )

bedtime_display = create_text_display(opt_bedtime, "Bedtime")
wake_time_display = create_text_display(opt_alarm, "Wake Time")
avg_temp_box = create_info_box(avg_temperature, "Avg Temp (°C)")
avg_hum_box = create_info_box(avg_humidity, "Avg Humidity (%)")

#################################### DASH APP SETUP ####################################
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])
server = app.server
app.title = "Sleep Metrics Dashboard"

#################################### LAYOUT ####################################
navbar = dbc.NavbarSimple(
    brand="Sleep Metrics Dashboard",
    brand_href="#",
    color="primary",
    dark=True
)

today_page = html.Div(
    style={"text-align": "center", "padding": "20px"},
    children=[
        html.Div(
            children=[
                html.H1("TONIGHT'S SLEEP AND WAKE TIMES", style={"margin-bottom": "20px", "font-family": "Arial, sans-serif", "font-weight": "bold"}),
                bedtime_display,
                wake_time_display
            ],
            style={
                "width": "70%",
                "margin": "auto",
                "display": "flex",
                "justify-content": "center",
                "align-items": "center",
                "vertical-align": "top",
                "border": "2px solid black",
                "padding": "30px 20px",
                "background-color": "#f8f9fa",
                "box-shadow": "5px 5px 15px rgba(0,0,0,0.3)",
                "margin-bottom": "40px"
            }
        ),
        html.Div(
            children=[dcc.Graph(figure=heatmap, style={"margin": "auto"})],
            style={
                "width": "70%",
                "margin": "auto",
                "display": "flex",
                "justify-content": "center",
                "align-items": "center",
                "vertical-align": "top",
                "border": "2px solid black",
                "padding": "30px 20px",
                "background-color": "#f8f9fa",
                "box-shadow": "5px 5px 15px rgba(0,0,0,0.3)",
                "margin-bottom": "40px"
            }
        ),
        html.Div(
            children=[
                dcc.Graph(figure=temperature_humidity_plot, style={"margin": "auto"})
            ],
            style={
                "width": "70%",
                "margin": "auto",
                "display": "flex",
                "justify-content": "center",
                "align-items": "center",
                "vertical-align": "top",
                "border": "2px solid black",
                "padding": "30px 20px",
                "background-color": "#f8f9fa",
                "box-shadow": "5px 5px 15px rgba(0,0,0,0.3)",
                "margin-bottom": "40px"
            }
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div(f"Avg Temp (°C): {avg_temperature:.2f}" if avg_temperature is not None else "Avg Temp (°C): N/A",
                                 style={"font-weight": "bold", "margin-bottom": "10px"}),
                    ],
                    style={
                        "font-family": "Arial, sans-serif",
                        "font-size": "18px",
                        "text-align": "center",
                        "border": "2px solid black",
                        "padding": "15px",
                        "margin": "10px",
                        "background-color": "#eaf7ff",
                        "width": "200px",
                        "display": "inline-block",
                        "box-shadow": "3px 3px 10px rgba(0,0,0,0.2)"
                    }
                ),
                html.Div(
                    children=[
                        html.Div(f"Temp Difference (°C): {environment_delta['temperature_difference']:.2f}",
                                 style={"font-weight": "bold", "margin-bottom": "10px"}),
                    ],
                    style={
                        "font-family": "Arial, sans-serif",
                        "font-size": "18px",
                        "text-align": "center",
                        "border": "2px solid black",
                        "padding": "15px",
                        "margin": "10px",
                        "background-color": "#ffcc99" if environment_delta['temperature_difference'] > 0 else "#99ccff",
                        "width": "200px",
                        "display": "inline-block",
                        "box-shadow": "3px 3px 10px rgba(0,0,0,0.2)"
                    }
                ),
                html.Div(
                    children=[
                        html.Div(f"Avg Humidity (%): {avg_humidity:.2f}" if avg_humidity is not None else "Avg Humidity (%): N/A",
                                 style={"font-weight": "bold", "margin-bottom": "10px"}),
                    ],
                    style={
                        "font-family": "Arial, sans-serif",
                        "font-size": "18px",
                        "text-align": "center",
                        "border": "2px solid black",
                        "padding": "15px",
                        "margin": "10px",
                        "background-color": "#eaf7ff",
                        "width": "200px",
                        "display": "inline-block",
                        "box-shadow": "3px 3px 10px rgba(0,0,0,0.2)"
                    }
                ),
                html.Div(
                    children=[
                        html.Div(f"Humidity Difference (%): {environment_delta['humidity_difference']:.2f}",
                                 style={"font-weight": "bold", "margin-bottom": "10px"}),
                    ],
                    style={
                        "font-family": "Arial, sans-serif",
                        "font-size": "18px",
                        "text-align": "center",
                        "border": "2px solid black",
                        "padding": "15px",
                        "margin": "10px",
                        "background-color": "#d3d3d3" if environment_delta['humidity_difference'] > 0 else "#f8f8f8",
                        "width": "200px",
                        "display": "inline-block",
                        "box-shadow": "3px 3px 10px rgba(0,0,0,0.2)"
                    }
                )
            ],
            style={
                "margin": "auto",
                "text-align": "center",
                "padding": "30px 20px",
                "background-color": "#f8f9fa",
                "box-shadow": "5px 5px 15px rgba(0,0,0,0.3)",
                "width": "70%"
            }
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Div("Temperature Advice", style={"font-weight": "bold", "margin-bottom": "10px"}),
                        html.Div(environment_delta['temperature_intervention'], style={"font-size": "16px"})
                    ],
                    style={
                        "font-family": "Arial, sans-serif",
                        "font-size": "18px",
                        "text-align": "center",
                        "border": "2px solid black",
                        "padding": "15px",
                        "margin": "10px",
                        "background-color": "#fffbea",
                        "width": "300px",
                        "display": "inline-block",
                        "box-shadow": "3px 3px 10px rgba(0,0,0,0.2)"
                    }
                ),
                html.Div(
                    children=[
                        html.Div("Humidity Advice", style={"font-weight": "bold", "margin-bottom": "10px"}),
                        html.Div(environment_delta['humidity_intervention'], style={"font-size": "16px"})
                    ],
                    style={
                        "font-family": "Arial, sans-serif",
                        "font-size": "18px",
                        "text-align": "center",
                        "border": "2px solid black",
                        "padding": "15px",
                        "margin": "10px",
                        "background-color": "#fffbea",
                        "width": "300px",
                        "display": "inline-block",
                        "box-shadow": "3px 3px 10px rgba(0,0,0,0.2)"
                    }
                )
            ],
            style={
                "margin": "auto",
                "border": "2px solid black",
                "padding": "30px 20px",
                "background-color": "#f8f9fa",
                "box-shadow": "5px 5px 15px rgba(0,0,0,0.3)",
                "width": "70%",
                "margin-top": "40px"
            }
        )
    ]
)


week_page = html.Div(
    style={"text-align": "center", "padding": "20px"},
    children=[
        html.H1("My Week", style={"margin-bottom": "20px", "font-family": "Arial, sans-serif", "font-weight": "bold"}),
        html.P("This page is under construction. More features coming soon!", style={"font-size": "18px"})
    ]
)

app.layout = html.Div([
    navbar,
    dcc.Tabs(id="tabs", value="today", children=[
        dcc.Tab(label="Today", value="today"),
        dcc.Tab(label="My Week", value="week")
    ]),
    html.Div(id="content")
])

@app.callback(
    Output("content", "children"),
    Input("tabs", "value")
)
def render_page(tab):
    if tab == "today":
        return today_page
    elif tab == "week":
        return week_page

#################################### RUN APP ####################################
if __name__ == "__main__":
    app.run_server()
