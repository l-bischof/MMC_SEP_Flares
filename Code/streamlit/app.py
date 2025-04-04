import sys
import os
# Making sure we have access to all the modules and are in the correct working directory
dirname = os.path.dirname(__file__)
code_dir = os.path.join(dirname, '../')
sys.path.insert(0, dirname)
sys.path.insert(0, code_dir)
os.chdir(code_dir)

import streamlit as st
import datetime
from stix import read_list, closest_timestamp
import pandas as pd
import numpy as np
import math
from connectivity_tool import read_data
import epd
import step
import misc
from classes import Config, SensorData
import matplotlib
import matplotlib.pyplot as plt
import bundler
import config

st.set_page_config(layout="centered", page_icon=":material/flare:", page_title="MMC Flares")
dpi = 800
matplotlib.rc("savefig", dpi = dpi)

@st.cache_resource
def setup():
    bundler.auto_download()

@st.cache_resource
def get_stix_flares():
    return read_list()

setup()
stix_flares = get_stix_flares()

# Filtering the flares to the date range
dates = pd.to_datetime(stix_flares['peak_UTC'])

first_flare = dates.min()
last_flare = dates.max()

stix_flares["_date"] = dates

st.title("SOLINK")
st.subheader("Automated Linkage between Solar Flares and Energetic Particle Events")

with st.sidebar:
    START_DATE = st.date_input(f"Start (after {first_flare.date()})", datetime.date(2021, 5, 21), first_flare, last_flare)
    END_DATE = st.date_input(f"End (before {last_flare.date()})", START_DATE+datetime.timedelta(days=3), first_flare, last_flare)

    if START_DATE > END_DATE:
        st.warning("Startdate needs to be before enddate")
        st.stop()

    sensor_switch = datetime.date(2021, 10, 22)
    if START_DATE <= sensor_switch and sensor_switch <= END_DATE:
        st.warning(f"On the {sensor_switch} the data format of STEP was changed and thus can't be compared.")
        st.stop()

    with st.expander("Settings for mag. connectivity and SEP event detection"):
        DELTA = st.slider("Flare accepteance radius", 1, 50, 10, format="%d°")
        WINDOW_LEN = st.slider("SEP run. avg. window length", 6*5, 24*5, 18*5, 5, format="%d min") // 5
        SIGMA_STEP = st.slider("STEP sigma threshold", 2., 5., 3.5, format="%.1fσ")
        SIGMA_EPT = st.slider("EPT sigma threshold", 1., 4., 2.5, format="%.1fσ")
        INDIRECT = st.slider("Parker Spiral extension factor", 1.1, 2., 1.5, format="%.1f")
        N_CHANNELS = st.slider("Number of channels needed for connection", 1, 20, 5)


        CONFIG = Config(window_length=WINDOW_LEN, 
                        step_sigma=SIGMA_STEP, 
                        ept_sigma=SIGMA_EPT, 
                        delta_flares=DELTA, 
                        start_date=START_DATE, 
                        end_date=END_DATE,
                        indirect_factor=INDIRECT,
                        needed_channels=N_CHANNELS)

# --------------------------------------- STIX ---------------------------------------
# Filtering the flares to the date range
dates = pd.to_datetime(stix_flares['peak_UTC'])
mask = (pd.Timestamp(START_DATE) <= dates) & (dates < pd.Timestamp(END_DATE) + pd.Timedelta(days=1))
flare_range = stix_flares[mask]
if not mask.any():
    st.error("No STIX Flares found in the selected timeframe.")
    st.stop()

parker_dist_series = pd.read_pickle(f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance.pkl")['Parker_Spiral_Distance']

flare_range["Rounded"] = flare_range["peak_UTC"].apply(closest_timestamp)


# Making sure the flare time is suntime
AU_TO_M = 149597870700
SPEED = 299_792_458 # m/s
time_difference = pd.to_timedelta((flare_range["solo_position_AU_distance"] * AU_TO_M) / SPEED, unit="s")

flare_range["_date_start"] = pd.to_datetime(stix_flares['start_UTC']).dt.floor("60s") - time_difference
flare_range["_date_peak"] = pd.to_datetime(stix_flares['peak_UTC']).dt.floor("60s") - time_difference
flare_range["_date_end"] = pd.to_datetime(stix_flares['end_UTC']).dt.floor("60s")- time_difference

# Looping over all flare candidates because connectivity Tool returns Dataframe
for i in flare_range.index:
    flare_lon = flare_range['hgc_lon'][i]
    flare_lat = flare_range['hgc_lat'][i]
    # Returns Dataframe
    try:
        con_tool_data = read_data(flare_range["Rounded"][i])
    except Exception as e:
        print(flare_range["Rounded"][i], repr(e))
        st.error(f"We are missing the connectivity tool data for {flare_range.loc[i]} and thus can't give a prediction.")
        st.stop()
        

    con_longitudes = con_tool_data["CRLN"]
    con_latitudes = con_tool_data["CRLT"]

    # Making sure we get the shortest distance
    lon_dist = np.min([(con_longitudes-flare_lon) % 360, (flare_lon-con_longitudes) % 360], axis=0)
    lat_dist = con_latitudes - flare_lat

    dist_sq = lon_dist ** 2 + lat_dist ** 2

    min_dist = math.sqrt(np.min(dist_sq))

    flare_range.loc[i, "Min Dist"] = min_dist


flare_range["MCT"] = flare_range["Min Dist"] <= DELTA
connected_flares = flare_range[flare_range["MCT"]]
# --------------------------------------- EPD ---------------------------------------
dict_sensor:dict[str, SensorData] = {}

for direction in ["sun", "asun", "north", "south"]:
    sensor = SensorData(is_step=False, sigma=CONFIG.ept_sigma)
    sensor.df_data = epd.load_pickles("ept", str(START_DATE), str(END_DATE), viewing=direction)

    sensor.df_mean, sensor.df_std = epd.running_average(sensor.df_data, CONFIG.window_length)

    dict_sensor[f"EPT-{direction.upper()}"] = sensor



step_sensor = SensorData(is_step=True, sigma=CONFIG.step_sigma)
df_step = epd.load_pickles("step", str(START_DATE), str(END_DATE))
df_step = step.cleanup_sensor(df_step)

step_sensor.df_data = df_step
step_sensor.df_mean, step_sensor.df_std = epd.running_average(step_sensor.df_data, CONFIG.window_length)

dict_sensor["STEP"] = step_sensor

for sensor_name in dict_sensor:
    # Getting the Sensor Object
    sensor = dict_sensor[sensor_name]

    # To shorten the code
    df_sensor = sensor.df_data
    running_mean = sensor.df_mean
    running_std = sensor.df_std
    sigma = sensor.sigma


    # Getting all events
    columns =  df_sensor.columns

    threshold = running_mean + sigma * running_std
    selected = df_sensor > threshold

    # If mean is zero, we want to ignore it
    selected &= (running_mean != 0) # Bitwise and

    # If we have a nan we also want to ignore it
    nan_mask = df_sensor.isna() | running_mean.isna() | running_std.isna() # Bitwise OR
    selected &= ~nan_mask

    # Implementing the idea described here for effecient detection of events: 
    # https://joshdevlin.com/blog/calculate-streaks-in-pandas/

    diff = (selected != selected.shift()) & ~selected.shift().isna()
    indexed = diff.cumsum()
    streaks = selected * indexed
    streaks = streaks[streaks != 0]
    streaks["Index"] = streaks.index

    event_starts = []
    event_ends = []


    for i, column in enumerate(columns):
        time_corrected = streaks["Index"]
        group = time_corrected.groupby(streaks[column])

        # Remove singular events
        mask = group.count().reset_index(drop=True) > 1

        # Getting the Event Starts
        min_group = group.min().reset_index(drop=True)[mask]

        # And Ends
        max_group = group.max().reset_index(drop=True)[mask]


        channel_event = pd.Series(min_group)
        event_starts.append(channel_event)

        event_ends.append(pd.Series(max_group))


    # Fully parallize the computation of the events and only loop over the flares
    df_starts = pd.DataFrame(event_starts, index=columns).T
    df_ends = pd.DataFrame(event_ends, index=columns).T

    df_conn = flare_range.copy()

    if sensor.is_step:
        speeds = misc.physics.get_step_speeds(length=len(columns))
    else:
        speeds = misc.misc_handler.compute_particle_speed(34, "electron")
    
    if df_starts.empty:
        df_conn["channels"] = 0
    else:
        for flare_index in flare_range.index:
            arrive_time = pd.to_timedelta(parker_dist_series[i] / speeds, unit="s")
            
            low = df_conn["_date_start"][flare_index] + arrive_time
            high = df_conn["_date_end"][flare_index] + arrive_time * CONFIG.indirect_factor

            mask = low < df_starts
            mask &= df_starts < high

            df_conn.loc[flare_index, "channels"] = mask.any().sum()
    
    events = pd.concat({"Start": df_starts, "End": df_ends}, axis=1)
    events = events.swaplevel(axis=1)
    df_conn["EPD_EVENT"] = df_conn["channels"] >= CONFIG.needed_channels

    dict_sensor[sensor_name].df_event = events
    dict_sensor[sensor_name].df_connection = df_conn
    

            
            
table = []
total_indecies = set()
ept_indecies = set()
# Collecting the events in sets to display which sensor captured which events

for sensor_name in dict_sensor:
    df_conn = dict_sensor[sensor_name].df_connection
    mask = df_conn["EPD_EVENT"] & df_conn["MCT"]
    table.append([sensor_name, len(df_conn[mask])])
    total_indecies = total_indecies.union(df_conn[mask].index)
    if not dict_sensor[sensor_name].is_step:
        ept_indecies = ept_indecies.union(df_conn[mask].index)

table.append(["Total (All Sensors)", len(total_indecies)])
table.append(["EPT (All Directions)", len(ept_indecies)])

ORDER = ["EPT-SUN", "EPT-ASUN", "EPT-NORTH", "EPT-SOUTH", "EPT (All Directions)","STEP", "Total (All Sensors)"]

table = sorted(table, key=lambda x: ORDER.index(x[0]))

table = pd.DataFrame(table, columns=["Sensor", f"Flares deemed connected ({CONFIG.start_date} - {CONFIG.end_date})"])
# Making the total columns bold
def bold_total(val, props=''):
    value = props if np.isin(val, ["EPT (All Directions)", "Total (All Sensors)"]).any() else ""
    return np.array([value]*len(val))
s1 = table.style.apply(bold_total, props='color:black;background-color:lightgrey;', axis=1)


st.dataframe(s1, hide_index=True, use_container_width=True)

# --------------------------------------- FLARES ---------------------------------------

with st.expander("Show Flare Details"):
    tab_names = {}
    flare_list = list(total_indecies)
    flare_list.sort()
    flare_list = flare_list[:10]
    for i, flare_index in enumerate(flare_list):
        tab_names[f"{i+1}\u200B. Flare"] = flare_index

    keys = list(tab_names.keys())

    tabs = []
    if keys:
        tabs = st.tabs(keys)


    for i, tab in enumerate(tabs):
        with tab:
            key = keys[i]
            index = tab_names[key]
            flare = flare_range.loc[index]
            st.markdown(f"""#### Stix Flare ID: {flare["flare_id"]}""")
            flare["Start UTC"] = pd.to_datetime(flare["start_UTC"]).to_pydatetime()
            flare["Peak UTC"] = pd.to_datetime(flare["peak_UTC"]).to_pydatetime()
            flare["End UTC"] = pd.to_datetime(flare["end_UTC"]).to_pydatetime()
            long = flare["Hel. Carr. longitude [°]"] = flare["hgc_lon"]
            lat = flare["Hel. Carr. latitude [°]"] = flare["hgc_lat"]
            flare["Solar Orbiter distance to Sun [AU]"] = flare["solo_position_AU_distance"]
            flare["Distance of mag. footpoint to flare [°]"] = flare["Min Dist"]
            st.dataframe(pd.DataFrame(
                                [flare], 
                                columns=[
                                    "Start UTC", "Peak UTC", 
                                    # "End UTC", 
                                    "Hel. Carr. longitude [°]",
                                    "Hel. Carr. latitude [°]",
                                    "Solar Orbiter distance to Sun [AU]",
                                    "Distance of mag. footpoint to flare [°]"
                                ]
                        ), 
                        hide_index=True,
                        use_container_width=True)
            
            connected_sensors = []

            for sensor in dict_sensor:
                df_conn = dict_sensor[sensor].df_connection
                row = df_conn.loc[index]
                if (not row["EPD_EVENT"]) or (not row["MCT"]):
                    connected_sensors.append([sensor, "No"])
                    continue
                connected_sensors.append([sensor, "Yes"])
            st.dataframe(pd.DataFrame(connected_sensors, columns=["Sensor", "Connected Event Detected"]), hide_index=True, use_container_width=True)

            # Highlight Flare
            if st.button("Highlight me in the graph!", key=index):
                st.session_state["Selected_Flare"] = index

            # Display Connectivity Tool
            flare_start = flare["_date_start"].round("6h")
            file = flare_start.strftime('SOLO_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_%Y%m%dT%H0000_finallegendmag.png')
            st.image(f"{config.CACHE_DIR}/connectivity_tool_downloads/{file}", 
                     caption="Magnetic Connectivity Tool output (http://connect-tool.irap.omp.eu/)")


highlighted = st.session_state.get("Selected_Flare", -1)
highlighted = highlighted if highlighted in flare_range.index else -1

# --------------------------------------- PLOTTING ---------------------------------------
sensor_name = st.selectbox("Render", dict_sensor.keys())

if highlighted != -1:
    st.info(f"The Flare with ID {flare_range.loc[highlighted]["flare_id"]} will be highlighted")

sensor = dict_sensor[sensor_name]
df_flares = sensor.df_connection
df_mean = sensor.df_mean
df_std = sensor.df_std
df_sensor = sensor.df_data
events = sensor.df_event

sigma = sensor.sigma
columns = []
column_indecies = []

for i in range(1, len(df_sensor.columns), len(df_sensor.columns)//4):
    columns.append(df_sensor.columns[int(i)])
    column_indecies.append(int(i))

plt.rcParams["figure.figsize"] = (20, 9)

fig, (flare_ax, *axs) = plt.subplots(5, sharex = False)
plt.subplots_adjust(hspace = 0)

df_hold = df_std.copy()
df_hold[""] = np.nan
df_hold[""].plot(color="black", ax=flare_ax)


for ax, column in zip(axs, columns):
    num = int(column.split("_")[-1])
    energies = epd.get_energies(sensor_name, len(df_sensor.columns))
    df_sensor[column].plot(color="black", logy=True, ax=ax, label=f"{sensor_name} Channel {num}\n{energies[num]}")
    df_threshhold = df_std[column] * sigma + df_mean[column]
    df_threshhold.plot(color="g", logy=True, ax=ax, label=f'run. avg. mean + {sigma} $\sigma$')


# Only plot each label once, else the whole legend is filled
shown_labels = set()

for i in df_flares.index:
    kwargs = {"color": "black", "label": "flare"}

    if df_flares["MCT"][i]:
        kwargs["color"] = "orange"
        kwargs["label"] = "candidate flare\n(mag. connectivity tool)"
    
    if i == highlighted:
        kwargs["color"] = "magenta"
        kwargs["label"] = "highlighted flare (candidate)"
    
    if kwargs["label"] in shown_labels:
        del kwargs["label"]
    else:
        shown_labels.add(kwargs["label"])
    flare_ax.axvline(df_flares["_date"][i], **kwargs)

if sensor.is_step:
    speeds = misc.physics.get_step_speeds(length=len(columns))
else:
    speeds = misc.misc_handler.compute_particle_speed(34, "electron")

first = True
for col, ax in zip(columns, axs):
    for event in events[col].iloc:
        if event.isna().all():
            continue
        kwargs = {}
        if first:
            first = False
            kwargs["label"] = "electron event"

        ax.axvspan(event["Start"], event["End"], color = 'b', alpha = 0.2, **kwargs)

# Plotting EPD-Connected Flares (candidates/connected)
shown_labels = set()

# Used for showing the connections, we use top and bottom to not upstruct the plot
positions = axs[0].get_ylim()
for i in df_flares[df_flares["EPD_EVENT"] == True].index:
    kwargs = {"color": "blue", "label": "coincidence flare"}

    if df_flares["MCT"][i]:
        kwargs["color"] = "red"
        kwargs["label"] = "connected flare"
        if i == highlighted:
            kwargs["color"] = "magenta"
            kwargs["label"] = None
        

    for ax in axs:
        if kwargs.get("label", None) in shown_labels:
            del kwargs["label"]
        elif kwargs.get("label", None):
            shown_labels.add(kwargs["label"])
        
        ax.axvline(df_flares["_date"][i], **kwargs)


if highlighted != -1:
    spiral = parker_dist_series[highlighted]
    arrive_times = pd.to_timedelta(spiral / speeds, unit="s")
    for col_i, ax in zip(column_indecies, axs):
        arrive_time = arrive_times[col_i]
                    
        low = flare_range["_date_start"][highlighted] + arrive_time
        high = flare_range["_date_end"][highlighted] + arrive_time * CONFIG.indirect_factor

        ax.axvspan(low, high, color = 'magenta', alpha = 0.2)

flare_ax.set_xlim(*axs[0].get_xlim())
flare_ax.xaxis.tick_top()
flare_ax.get_yaxis().set_visible(False)

handles, labels = flare_ax.get_legend_handles_labels()
# sort both labels and handles by labels
labels, handles = zip(*sorted(zip(labels, handles), key=lambda t: t[0], reverse=True))
flare_ax.legend(handles, labels, loc="lower right")

for ax in axs[:-1]:
    ax.legend(loc = 'lower right')
    ax.get_xaxis().set_visible(False)

axs[-1].legend(loc = 'lower right')

# Grouping the plot to align the labels
fig.add_subplot(111, frameon = False)
plt.ylabel('electron intensity [$(cm^2 \ s \ sr \ MeV)^{-1}$]', fontsize = 20, loc="center")
plt.xlabel('time', fontsize = 20, labelpad=20)
plt.tick_params(labelcolor='none', top=False, bottom=False, left=False, right=False)
st.pyplot(plt)