'''
This script allows for the comparison a flare in the STIX flare list with the magnetically connected points
computed by the magnetic connectivity tool (url: http://connect-tool.irap.omp.eu/)

It determines if the flares origin is within delta (to be chosen by the user) degrees of a magnetically
connected point on the sun's surface.

programming:
DONE: Find a better way to collect Magnetic Connectivity Tool (MCT) data, e.g. without opening a browser window for every 6-hour period needed to be downloaded

scientific:
TODO: improve metric to classify possible connection points and account for their likelyhood
TODO: take into account shape of AR when looking for a connection with the tool

!!! For new users it will be necessary to change some file paths and make new directories to allow the automation of downloads to work !!!
!!! This script will open browser tabs to download the magnetic connectivity tool data automatically. Google Chrome is recommended     !!!
'''

import pandas as pd
import numpy as np
import datetime

import stix
import connectivity_tool
import plots
import epd
import misc

import config

# --------------------------------- Input parameters ---------------------------------

# choose if additional output is requested
opt_output = False
# choose if plots for non-connected flares should be made
plot_non_connected = True

# work with data and search for events within the following timespan
start_date = config.START_DATE
end_date = config.END_DATE

# --------------------------------------- STIX ---------------------------------------

delta = 10      # radius of connection points that get accepted (degrees)

# read STIX flare list and extract coordinates of the origin
stix_flares = stix.read_list()

# get range of flares that are within the defined timeframe
flare_start_id, flare_end_id = stix.flares_range(start_date, end_date, stix_flares['peak_UTC'])

# returns a list of candidates the MCT (Magnetic Connectivity Tool) expects the Solar Orbiter to be connected with
# flare_distances is currently not used for anything (has been added as it might yield interesting data)
connected_flares, flare_distances = connectivity_tool.find_connected_flares(stix_flares, flare_start_id, flare_end_id, delta, opt_output, plot_non_connected)

# print("Connected flares in magentic connectivity tool: ", connected_flares)
# print(len(connected_flares))

# get timestamps of connected flares
connected_flares_peak_utc = []
for i in connected_flares:
    connected_flares_peak_utc.append(stix_flares['peak_UTC'][i])

# --------------------------------------- EPD ---------------------------------------

# The version using STEP is in a new file as the data from STEP has a different format. This could maybe be merged into one file.
# The viewing angle has to be manually chosen for now. Could be easily automated to use all four (without omni) angles. However I would recommend some optimization steps first to reduce runtime.
sensor = 'ept' # ['het', 'ept', 'step']
viewing = 'sun' # ['sun', 'asun', 'north', 'south', 'omni']

# load data from compressed EPD dataset
# epd_handler.load_pickles() loads dataframe of timespan defined (including end_date)
df = epd.load_pickles(sensor, start_date, end_date, 'electron', viewing)

print("Pickle files loaded...")

# compute running averade and standard deviation
running_mean, running_std = epd.running_average(df)

print("Running averages computed...")

# try to find events in data
sigma_factor = 2.5
events = epd.find_event(df, running_mean, running_std, sigma_factor)

print("Events found...")

if(opt_output):
    print(events)
    print(len(events))

if flare_end_id != -1:
    # find flares that peak during epd event
    delayed_utc = []
    delayed_utc_start = []
    indirect_factor = 1.5
    for i in range(flare_start_id, flare_end_id + 1):
        utc = stix_flares['peak_UTC'][i]
        timestamp = pd.Timestamp(utc[0:10] + " " + utc[11:19])
        
        # Timestamp of the flare peak
        delayed_utc.append(misc.add_delay('electron', i, timestamp, indirect_factor, stix_flares['solo_position_AU_distance'][i]))
        
        # Timestamp of the flare start
        utc_start = stix_flares['start_UTC'][i]
        timestamp = pd.Timestamp(utc_start[0:10] + " " + utc_start[11:19])
        
        delayed_utc_start.append(misc.add_delay('electron', i, timestamp, indirect_factor, stix_flares['solo_position_AU_distance'][i]))
        
    for i in range(len(delayed_utc)):
        # EPT has 34 energy channels
        for j in range(34):
            delayed_utc[i][j][0] = delayed_utc_start[i][j][0]
        
    epd_connected_flares = []
    # epd_flare_distances = []
    count = 0
    
    # check if flare and detected EPD event correlate
    # i loops through expected arrival time of particles from flares (count is used to keep track of the corresponding flare_id)
    for i in delayed_utc:
        temp = False # temporary variable to keep track if a flare has already been found to be connected
        for bin in range(34):
            for j in events:
                if i[bin][0] < j[0] and j[0] < i[bin][1]:
                    epd_connected_flares.append(flare_start_id + count)
                    # epd_flare_distances.append(flare_distances[count])
                    temp = True
                    break
            if temp:
                break
        count += 1

    # some plots that have been interesting during the project. Remove at own discretion...
    # plots.histogram(epd_flare_distances, range(0, 180, 5), "Images/Hist/epd_flares_distance_electrons.jpg", 'Distance to closest passible connection point [degrees]')
    # plots.histogram(epd_flare_distances_ions, range(0, 180, 5), "Images/Hist/epd_flares_distance_ions.jpg", 'Distance to closest passible connection point [degrees]')
        
    print("Connected flares in EPD (electrons): ", epd_connected_flares)
    print(len(epd_connected_flares))

    # get timestamps of connected flares
    epd_connected_flares_peak_utc = []
    for i in epd_connected_flares:
        epd_connected_flares_peak_utc.append(stix_flares['peak_UTC'][i])

# --------------------------------------- OUTPUT ---------------------------------------
# Output generation and preparation steps for it

# rename columns for output/figures
col_names_mean = []
col_names_std = []
for col in running_mean.columns:
    col_names_mean.append("Mean" + col[8:])
    col_names_std.append("Mean+" + str(sigma_factor) + "Sigma" + col[8:])
    
running_mean.columns = col_names_mean
running_std.columns = col_names_std

plots.plot_epd_data(df, running_mean, running_std, sigma_factor, f'{config.OUTPUT_DIR}/Images/Electron.jpg', connected_flares_peak_utc,
                    epd_connected_flares_peak_utc, events, stix_flares['peak_UTC'][flare_start_id:flare_end_id + 1])