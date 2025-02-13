import pandas as pd
import numpy as np
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt

import stix_handler
import connectivity_tool
import plots
import epd_handler
import misc_handler
import math
import config

dpi = 300
mpl.rc("savefig", dpi = dpi)

# --------------------------------- Input parameters ---------------------------------

# choose if additional output is requested
opt_output = False
# choose if plots for non-connected flares should be made
plot_non_connected = True
# show all events
show_all = False

# work with data and search for events within the following timespan
# -> do not simulate before and after 22.10.2021 in one run!!!
# --> the change in energy bin ranges does not allow for an automated comparison of data before and after the change.
start_date = config.START_DATE
end_date = config.END_DATE

# --------------------------------------- STIX ---------------------------------------

delta = 10      # radius of connection points that get accepted (degrees)

# read STIX flare list and extract coordinates of the origin
stix_flares = stix_handler.read_list()

# get range of flares that are within the defined timeframe
flare_start_id, flare_end_id = stix_handler.flares_range(start_date, end_date, stix_flares['peak_UTC'])

# returns a list of candidates the MCT (Magnetic Connectivity Tool) expects the Solar Orbiter to be connected with
# flare_distances is currently not used for anything (has been added as it might yield interesting data)
connected_flares, flare_distances = connectivity_tool.find_connected_flares(stix_flares, flare_start_id, flare_end_id, delta, opt_output, plot_non_connected)
connected_flares_utc = []

for i in connected_flares:
    if (i >= flare_start_id) and (i <= flare_end_id):
        connected_flares_utc.append(stix_flares['peak_UTC'][i])

# --------------------------------------- EPD ---------------------------------------

sensor = 'step' # ['het', 'ept', 'step']

# columns of step data
# ['DELTA_EPOCH', 'Integral_Avg_Flux_0-47', 'Integral_Avg_Uncertainty_0-47', 'Magnet_Avg_Flux_0-47', 'Magnet_Avg_Uncertainty_0-47', 'QUALITY_BITMASK', 'QUALITY_FLAG', 'SMALL_PIXELS_FLAG']
df_step = epd_handler.load_pickles(sensor, start_date, end_date)

# remove flag columns as currently not used
drop_columns = ['DELTA_EPOCH', 'QUALITY_BITMASK', 'QUALITY_FLAG']
if ('SMALL_PIXELS_FLAG' in df_step.columns):
    drop_columns.append('SMALL_PIXELS_FLAG')

# For the first months a different number of energy channels is used. This detects if you are withing that time.
length = 32
if ('Integral_Avg_Flux_47' in df_step.columns):
    length = 48

# find names of columns that are not needed
drop_magnet = []
drop_integral = []
electron_cols = []
for i in range(length):
    drop_columns.append('Integral_Avg_Uncertainty_' + str(i))
    drop_columns.append('Magnet_Avg_Uncertainty_' + str(i))
    drop_integral.append('Integral_Avg_Flux_' + str(i))
    drop_magnet.append('Magnet_Avg_Flux_' + str(i))
    electron_cols.append('Electron_Avg_Flux_' + str(i))

# remove unnecessary data  
df_step_data = df_step.drop(drop_columns, axis = 1)

# compute electron counts (integral - magnet ~> all - ions)
df_step_electron = pd.DataFrame(columns = electron_cols, index = df_step.index)
df_integral = df_step_data.drop(drop_magnet, axis = 1)
df_magnet = df_step_data.drop(drop_integral, axis = 1)
for i in range(length):
    integral_col = df_integral.columns[i]
    magnet_col = df_magnet.columns[i]
    df_step_electron[electron_cols[i]] = pd.Series(df_integral[integral_col].to_numpy() - df_magnet[magnet_col].to_numpy(), index = df_step_electron.index)  

# compute running averade and standard deviation
running_mean, running_std = epd_handler.running_average(df_step_electron)

print("Running averages computed...")

# compute expected delay of arriving particles
dt = misc_handler.step_delay(start_date, length)

# find fastest channel -> minimal delay
if length == 32:
    dt_min = dt[31]
else:
    dt_min = dt[47]

offset = []
for i in range(length):
    offset.append(math.floor((dt[i] - dt_min) / 300))

df_offset_step = df_step_electron.copy()
count = 0

for i in df_offset_step.columns:
    for j in df_offset_step.index:
        idx = df_offset_step.index.get_loc(j)
        
        if(idx + offset[count] >= len(df_offset_step.index)):
            df_offset_step[i][j] = np.nan
        else:
            df_offset_step[i][j] = df_offset_step[i][df_offset_step.index[idx + offset[count]]]
            
    count += 1

# try to find events in data
sigma_factor = 3.5
events = epd_handler.find_event(df_offset_step, running_mean, running_std, sigma_factor)

print("Events found...")

# rename columns for output/figures
col_names_mean = []
col_names_std = []
for col in running_mean.columns:
    col_names_mean.append("Mean" + col[12:])
    col_names_std.append("Mean+" + str(sigma_factor) + "Sigma" + col[12:])
    
running_mean.columns = col_names_mean
running_std.columns = col_names_std

epd_connected_flares_peak_utc = []

if flare_end_id != -1:
    # find flares that peak during epd event
    delayed_utc = []
    delayed_utc_start = []
    indirect_factor = 1.5
    for i in range(flare_start_id, flare_end_id + 1):
        utc = stix_flares['peak_UTC'][i]
        timestamp = pd.Timestamp(utc[0:10] + " " + utc[11:19])
        
        dt = misc_handler.step_delay(utc, length)
        
        delay = []
        for j in range(length):
            delay_direct = timestamp + datetime.timedelta(0, math.floor(dt[j]))
            delay_indirect = timestamp + datetime.timedelta(0, math.floor(dt[j] * indirect_factor))
            
            delay.append([delay_direct, delay_indirect])
        
        delayed_utc.append(delay)
        
        utc_start = stix_flares['start_UTC'][i]
        timestamp = pd.Timestamp(utc_start[0:10] + " " + utc_start[11:19])
        
        delay = []
        for j in range(length):
            delay_direct = timestamp + datetime.timedelta(0, math.floor(dt[j]))
            delay_indirect = timestamp + datetime.timedelta(0, math.floor(dt[j] * indirect_factor))
            
            delay.append([delay_direct, delay_indirect])
        
        delayed_utc_start.append(delay)
                
    for i in range(len(delayed_utc)):
        for j in range(length):
            delayed_utc[i][j][0] = delayed_utc_start[i][j][0]
        
    epd_connected_flares = []
    count = 0
    for i in delayed_utc:
        temp = False
        for bin in range(length):
            for j in events:
                if i[bin][0] < j[0] and j[0] < i[bin][1]:
                    epd_connected_flares.append(flare_start_id + count)
                    temp = True
                    break
            if temp:
                break
        count += 1
        
    for i in epd_connected_flares:
        epd_connected_flares_peak_utc.append(stix_flares['peak_UTC'][i])

plots.plot_step_data(df_step_electron, running_mean, running_std, sigma_factor, offset, f'{config.OUTPUT_DIR}/Images/step.jpg', connected_flares_utc,
                     epd_connected_flares_peak_utc, events, stix_flares['peak_UTC'][flare_start_id:flare_end_id + 1])

print(epd_connected_flares)
print(epd_connected_flares_peak_utc)