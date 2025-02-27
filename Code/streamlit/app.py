import sys
import os
# Making sure we have access to all the modules and are in the correct working directory
dirname = os.path.dirname(__file__)
code_dir = os.path.join(dirname, '../')
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
import ept
from io import BytesIO
import matplotlib
import bundler

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

st.title("Magnetic Connectivity between Flares and SEP Events")

with st.sidebar:
    START_DATE = st.date_input("Start", datetime.date(2021, 5, 21), first_flare, last_flare)
    END_DATE = st.date_input("End", START_DATE+datetime.timedelta(days=3), first_flare, last_flare)

    if START_DATE > END_DATE:
        st.warning("Startdate needs to be before enddate")
        st.stop()

    sensor_switch = datetime.date(2021, 10, 22)

    sensor = st.selectbox("Select a sensor", ("step", "ept"))

    VIEWING = "none"
    if sensor == "ept":
        VIEWING = st.selectbox("Direction", ('sun', 'asun', 'north', 'south', 'omni'))
    elif sensor == "step":
        if START_DATE <= sensor_switch and END_DATE >= sensor_switch:
            st.warning(f"Cannot include date before and after {sensor_switch} as mesurements changed")
            st.stop()

    download = st.toggle("Activate Downloads")

    with st.expander("More Options:"):
        DELTA = st.slider("Delta Flares", 1, 50, 10)

# --------------------------------------- STIX ---------------------------------------

# Filtering the flares to the date range
dates = pd.to_datetime(stix_flares['peak_UTC'])
mask = (pd.Timestamp(START_DATE) <= dates) & (dates < pd.Timestamp(END_DATE) + pd.Timedelta(days=1))
flare_range = stix_flares[mask]


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


st.text(f"Found {len(connected_flares)} of {len(flare_range)} flares identified by STIX are deemed "\
        "connected by the magnetic connectivty Tool")

# --------------------------------------- EPD ---------------------------------------

df_sensor = epd.load_pickles(sensor, str(START_DATE), str(END_DATE), viewing=VIEWING)

if sensor == "step":
    with st.spinner("Creating your plot...", show_time=True):
        plt = step.create_step(df_sensor, flare_range, connected_flares)
        st.pyplot(plt)
    if download:
        virtual_file = BytesIO()
        plt.savefig(virtual_file, format="svg")
        virtual_file.seek(0)
        st.download_button("Download Plot", data=virtual_file.read(),file_name=f"{START_DATE}-{END_DATE}.svg")

if sensor == "ept":
    with st.spinner("Creating your plot...", show_time=True):
        plt = ept.create_ept(df_sensor, flare_range, connected_flares)
        st.pyplot(plt)
    
    if download:
        virtual_file = BytesIO()
        plt.savefig(virtual_file, format="svg")
        virtual_file.seek(0)
        st.download_button("Download Plot", data=virtual_file.read(),file_name=f"{START_DATE}-{END_DATE}.svg")