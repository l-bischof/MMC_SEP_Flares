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
from classes import Config
import matplotlib
import matplotlib.pyplot as plt
import bundler
import config
from matplotlib.dates import date2num

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

st.header("Automated Linkage between Solar Flares and Energetic Particle Events")

with st.sidebar:
    START_DATE = st.date_input(f"Start (after {first_flare.date()})", datetime.date(2021, 5, 21), first_flare, last_flare)
    END_DATE = st.date_input(f"End (before {last_flare.date()})", START_DATE+datetime.timedelta(days=3), first_flare, last_flare)

    if START_DATE > END_DATE:
        st.warning("Startdate needs to be before enddate")
        st.stop()

    sensor_switch = datetime.date(2021, 10, 22)

    with st.expander("Settings for mag. connectivity and SEP event detection"):
        DELTA = st.slider("Flare accepteance radius", 1, 50, 10, format="%d°")
        WINDOW_LEN = st.slider("SEP run. avg. window length", 6*5, 24*5, 18*5, 5, format="%d min") // 5
        SIGMA_STEP = st.slider("STEP sigma threshold", 2., 5., 3.5, format="%.1fσ")
        SIGMA_EPT = st.slider("EPT sigma threshold", 1., 4., 2.5, format="%.1fσ")

        CONFIG = Config(window_length=WINDOW_LEN, 
                        step_sigma=SIGMA_STEP, 
                        ept_sigma=SIGMA_EPT, 
                        delta_flares=DELTA, 
                        start_date=START_DATE, 
                        end_date=END_DATE)

# --------------------------------------- STIX ---------------------------------------

# Filtering the flares to the date range
dates = pd.to_datetime(stix_flares['peak_UTC'])
mask = (pd.Timestamp(START_DATE) <= dates) & (dates < pd.Timestamp(END_DATE) + pd.Timedelta(days=1))
flare_range = stix_flares[mask]

parker_dist_series = pd.read_pickle(f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance.pkl")['Parker_Spiral_Distance']

flare_range["Rounded"] = flare_range["peak_UTC"].apply(closest_timestamp)

# Looping over all flare candidates because connectivity Tool returns Dataframe
for i in flare_range.index:
    flare_lon = flare_range['hgc_lon'][i]
    flare_lat = flare_range['hgc_lat'][i]
    # Returns Dataframe
    try:
        con_tool_data = read_data(flare_range["Rounded"][i])
    except Exception as e:
        print(flare_range["Rounded"][i], repr(e))
        

    con_longitudes = con_tool_data["CRLN"]
    con_latitudes = con_tool_data["CRLT"]

    # Making sure we get the shortest distance
    lon_dist = np.min([(con_longitudes-flare_lon) % 360, (flare_lon-con_longitudes) % 360], axis=0)
    lat_dist = con_latitudes - flare_lat

    dist_sq = lon_dist ** 2 + lat_dist ** 2

    min_dist = math.sqrt(np.min(dist_sq))

    flare_range.loc[i, "Min Dist"] = min_dist

if len(flare_range) == 0:
    st.warning("No Flares found in the selected time frame")
    st.stop()

flare_range["MCT"] = flare_range["Min Dist"] <= DELTA
connected_flares = flare_range[flare_range["MCT"]]

# --------------------------------------- EPD ---------------------------------------

dict_df_sensor:dict[str, pd.DataFrame] = {}

for direction in ["sun", "asun", "north", "south"]:
    dict_df_sensor[f"EPT-{direction.upper()}"] = epd.load_pickles("ept", str(START_DATE), str(END_DATE), viewing=direction)


df_step = epd.load_pickles("step", str(START_DATE), str(END_DATE))
df_step = step.cleanup_sensor(df_step)
df_step, step_offsets = step.shift_sensor(df_step, flare_range, length=len(df_step.columns), parker_dist_series=parker_dist_series, _config=CONFIG)
dict_df_sensor["STEP"] = df_step

dict_df_mean:dict[str, pd.DataFrame] = {}
dict_df_std:dict[str, pd.DataFrame] = {}
dict_df_event:dict[str, pd.DataFrame] = {}
dict_df_connection:dict[str, pd.DataFrame] = {}
dict_df_offset:dict[str, pd.DataFrame] = {}

flare_range["_date_start"] = pd.to_datetime(stix_flares['start_UTC']).dt.floor("60s")
flare_range["_date_peak"] = pd.to_datetime(stix_flares['peak_UTC']).dt.floor("60s")

for sensor in dict_df_sensor:
    running_mean, running_std = epd.running_average(dict_df_sensor[sensor], CONFIG.window_length)
    dict_df_mean[sensor] = running_mean
    dict_df_std[sensor] = running_std
    sigma = CONFIG.ept_sigma if "EPT" in sensor else CONFIG.step_sigma
    events = epd.find_event(dict_df_sensor[sensor], dict_df_mean[sensor], dict_df_std[sensor], sigma)
    events = pd.DataFrame(events, columns=["Start", "End"])
    dict_df_event[sensor] = events

    if "STEP" in sensor:
        step_connections = flare_range.copy()
        step_connections["EPD_EVENT"] = np.nan
        for i in flare_range.index:
            utc_start = flare_range['_date_start'][i]
            utc_peak = flare_range['_date_peak'][i]

            
            dt = misc.step_delay(utc_start, len(df_step.columns), parker_dist_series[i])
            
            delay = []
            for j in range(len(df_step.columns)):
                delay_start = utc_start + datetime.timedelta(0, math.floor(dt[j]))
                delay_peak_indirect = utc_peak + datetime.timedelta(0, math.floor(dt[j] * CONFIG.indirect_factor))
                
                mask = (delay_start < events["Start"]) & (events["Start"] < delay_peak_indirect)
                for event in events[mask].index:
                    step_connections.loc[i, "EPD_EVENT"] = event
                    break
            
        dict_df_connection[sensor] = step_connections
    else:
        ept_connection = flare_range.copy()
        ept_connection["EPD_EVENT"] = np.nan

        for i in flare_range.index:
            utc_start = flare_range['_date_start'][i]
            utc_peak = flare_range['_date_peak'][i]
            solo_distance = flare_range['solo_position_AU_distance'][i]
            
            # Timestamp of the flare start
            flare_start = misc.add_delay('electron', i, utc_start, CONFIG.indirect_factor, solo_distance)
            # Timestamp of the flare peak
            flare_peak = misc.add_delay('electron', i, utc_peak, CONFIG.indirect_factor, solo_distance)

            for (flare_start_direct, _), (_, flare_peak_indirect) in zip(flare_start, flare_peak):
                mask = (flare_start_direct < events["Start"]) & (events["Start"] < flare_peak_indirect)
                for event in events[mask].index:
                    ept_connection.loc[i, "EPD_EVENT"] = event
                    break


        dict_df_connection[sensor] = ept_connection
            
            
            
table = []
total_indecies = set()
ept_indecies = set()

for sensor in dict_df_sensor:
    df_conn = dict_df_connection[sensor]
    mask = (~df_conn["EPD_EVENT"].isna()) & df_conn["MCT"]
    table.append([sensor, len(df_conn[mask])])
    total_indecies = total_indecies.union(df_conn[mask].index)
    if "EPT" in sensor:
        ept_indecies = ept_indecies.union(df_conn[mask].index)

table.append(["Total", len(total_indecies)])

ORDER = ["EPT-SUN", "EPT-ASUN", "EPT-NORTH", "EPT-SOUTH", "EPT","STEP", "Total"]

table = sorted(table, key=lambda x: ORDER.index(x[0]))
table = pd.DataFrame(table, columns=["Sensor", f"Flares deemed connected ({CONFIG.start_date} - {CONFIG.end_date})"])



st.dataframe(table, hide_index=True, use_container_width=True)

# --------------------------------------- FLARES ---------------------------------------

with st.expander("Show Flare Details"):
    tab_names = {}
    for i, flare_index in enumerate(list(total_indecies)[:10]):
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
            flare["Hel. Carr. longitude [°]"] = flare["hgc_lon"]
            flare["Hel. Carr. latitude [°]"] = flare["hgc_lat"]
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

            for sensor in dict_df_sensor:
                df_conn = dict_df_connection[sensor]
                row = df_conn.loc[index]
                print(row[['EPD_EVENT', 'MCT']])
                if pd.isna(row["EPD_EVENT"]) or (not row["MCT"]):
                    connected_sensors.append([sensor, "No"])
                    continue
                connected_sensors.append([sensor, "Yes"])
            st.dataframe(pd.DataFrame(connected_sensors, columns=["Sensor", "Connected Event Detected"]), hide_index=True, use_container_width=True)
            flare_start = flare["_date_start"].round("6h")
            file = flare_start.strftime('SOLO_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_%Y%m%dT%H0000_finallegendmag.png')
            st.image(f"{config.CACHE_DIR}/connectivity_tool_downloads/{file}", 
                     caption="Magnetic Connectivity Tool output (http://connect-tool.irap.omp.eu/)")


# --------------------------------------- PLOTTING ---------------------------------------

sensor = st.selectbox("Render", dict_df_connection.keys())


df_flares = dict_df_connection[sensor]
df_mean = dict_df_mean[sensor]
df_std = dict_df_std[sensor]
df_sensor = dict_df_sensor[sensor]
events = dict_df_event[sensor]

sigma = CONFIG.ept_sigma if "EPT" in sensor else CONFIG.step_sigma
columns = []

for i in range(1, len(df_sensor.columns), len(df_sensor.columns)//4):
    columns.append(df_sensor.columns[int(i)])

plt.rcParams["figure.figsize"] = (20, 9)

fig, (flare_ax, *axs) = plt.subplots(5, sharex = False)
plt.subplots_adjust(hspace = 0)

df_hold = df_std.copy()
df_hold[""] = np.nan
df_hold[""].plot(color="black", ax=flare_ax)


for ax, column in zip(axs, columns):
    num = int(column.split("_")[-1])
    energies = epd.get_energies(sensor, len(df_sensor.columns))
    df_sensor[column].plot(color="black", logy=True, ax=ax, label=f"{sensor} Channel {num}")
    df_threshhold = df_std[column] * sigma + df_mean[column]
    df_threshhold.plot(color="g", logy=True, ax=ax, label=f'mean + {sigma} $\sigma$ (Channel {num}){energies[num]}')


# Only plot each label once, else the whole legend is filled
shown_labels = set()

for i in df_flares.index:
    kwargs = {"color": "black", "label": "Flare"}

    if df_flares["MCT"][i]:
        kwargs["color"] = "orange"
        kwargs["label"] = "candidate flare (mag. connectivity tool)"
    
    if kwargs["label"] in shown_labels:
        del kwargs["label"]
    else:
        shown_labels.add(kwargs["label"])
    flare_ax.axvline(df_flares["_date"][i], **kwargs)


first = True
for i in events.index:    
    for col, ax in zip(columns, axs):
        kwargs = {}
        if first:
            first = False
            kwargs["label"] = "electron event"
        
        offset = pd.Timedelta(0)
        if sensor == "STEP":
            step_value = step_offsets[int(col.split("_")[-1])] * config.TIME_RESOLUTION
            offset = pd.Timedelta(seconds=int(step_value))
        ax.axvspan(events["Start"][i]+offset, events["End"][i]+offset, color = 'b', alpha = 0.2, **kwargs)

shown_labels = set()
positions = axs[0].get_ylim()
for i in df_flares[~df_flares["EPD_EVENT"].isna()].index:
    kwargs = {"color": "blue", "label": "flare in temporal coincidence with electron \nevent (not connected by mag. connectivity tool)"}

    if df_flares["MCT"][i]:
        kwargs["color"] = "red"
        kwargs["label"] = "connected flare"
        event = events.loc[int(df_flares["EPD_EVENT"][i])]
        offset = pd.Timedelta(0)
        if sensor == "STEP":
            step_value = step_offsets[int(columns[0].split("_")[-1])] * config.TIME_RESOLUTION
            offset = pd.Timedelta(seconds=int(step_value))
        event_mid = (event["End"] - event["Start"]) / 2 + event["Start"] + offset

        axs[0].arrow(df_flares["_date"][i], positions[i%2], 
                     axs[0].get_xaxis().get_converter().convert((event_mid-df_flares["_date"][i])/pd.Timedelta(seconds=60), "s", axs[0]), 
                       0, lw=2)

    for ax in axs:
        if kwargs.get("label", None) in shown_labels:
            del kwargs["label"]
        elif kwargs.get("label", None):
            shown_labels.add(kwargs["label"])
        
        ax.axvline(df_flares["_date"][i], **kwargs)


flare_ax.set_xlim(*axs[0].get_xlim())
flare_ax.xaxis.tick_top()
flare_ax.get_yaxis().set_visible(False)

flare_ax.legend()

for ax in axs[:-1]:
    ax.legend(loc = 'lower right')
    ax.get_xaxis().set_visible(False)

axs[-1].legend(loc = 'lower right')
plt.ylabel('electron intensity [$(cm^2 \ s \ sr \ MeV)^{-1}$]', fontsize = 20, loc="bottom")
plt.xlabel('time', fontsize = 20)

st.pyplot(plt)