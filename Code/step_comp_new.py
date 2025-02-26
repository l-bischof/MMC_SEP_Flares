import matplotlib as mpl
import tqdm
import math
import config
import pandas as pd
import numpy as np
import datetime
import epd
import misc
import plots
from stix import closest_timestamp, read_list
from connectivity_tool import read_data


dpi = 300
mpl.rc("savefig", dpi = dpi)
sensor = "step" # ['het', 'ept', 'step']

# choose if additional output is requested
opt_output = False
# choose if plots for non-connected flares should be made
plot_non_connected = True
# show all events
show_all = False


# --------------------------------------- STIX ---------------------------------------

stix_flares = read_list()

# Filtering the flares to the date range
dates = pd.to_datetime(stix_flares['peak_UTC'])
mask = (pd.Timestamp(config.START_DATE) <= dates) & (dates < pd.Timestamp(config.END_DATE) + pd.Timedelta(days=1))
flare_range = stix_flares[mask]


flare_range["Rounded"] = flare_range["peak_UTC"].apply(closest_timestamp)

# Looping over all flare candidates because connectivity Tool returns Dataframe
for i in tqdm.tqdm(flare_range.index):
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

flare_range["MCT"] = flare_range["Min Dist"] <= config.DELTA
connected_flares = flare_range[flare_range["MCT"]]

# --------------------------------------- EPD ---------------------------------------

df_step = epd.load_pickles(sensor, config.START_DATE, config.END_DATE)

# For the first months a different number of energy channels is used. This detects if you are within that time.
length = 32
if ('Integral_Avg_Flux_47' in df_step.columns):
    length = 48

df_step_electron = pd.DataFrame(columns = [], index = df_step.index)
zipped_columns = [(f'Electron_Avg_Flux_{i}', f"Integral_Avg_Flux_{i}", f"Magnet_Avg_Flux_{i}") for i in range(length)]

for electron_col, integral_col, magnet_col in zipped_columns:
    df_step_electron[electron_col] = df_step[integral_col] - df_step[magnet_col]

running_mean, running_std = epd.running_average(df_step_electron)

# Using the precomputed parker spiral distance
parker_dist_series = pd.read_pickle(f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance.pkl")['Parker_Spiral_Distance']

if len(flare_range) > 0:
    first_index = flare_range.index[0]
    delay_frame = misc.step_delay(config.START_DATE, length, parker_dist=parker_dist_series[first_index])
else:
    delay_frame = misc.step_delay(config.START_DATE, length)

# The highest index contains the fastest electrons
dt_min = delay_frame[-1]

# Correcting the timedelta between the Electrons
offset = ((delay_frame - dt_min) // config.TIME_RESOLUTION).astype(np.int64)
df_offset_step = df_step_electron.copy()

for i, column in enumerate(df_offset_step.columns):
    df_offset_step[column] = df_offset_step[column].shift(-offset[i])

# try to find events in data
sigma_factor = 3.5
events = epd.find_event(df_offset_step, running_mean, running_std, sigma_factor)

print("Events found...")

# rename columns for output/figures
col_names_mean = []
col_names_std = []
for col in running_mean.columns:
    col_names_mean.append("Mean" + col[12:])
    col_names_std.append("Mean+" + str(sigma_factor) + "Sigma" + col[12:])

running_mean.columns = col_names_mean
running_std.columns = col_names_std

#----------------------------------------------------------------------------

epd_connected_flares_peak_utc = []
# find flares that peak during epd event
delayed_utc = []
delayed_utc_start = []
indirect_factor = 1.5
for i in flare_range.index:
    utc = flare_range['peak_UTC'][i]
    timestamp = pd.Timestamp(utc[0:10] + " " + utc[11:19])
    
    dt = misc.step_delay(utc, length, parker_dist_series[i])
    
    delay = []
    for j in range(length):
        delay_direct = timestamp + datetime.timedelta(0, math.floor(dt[j]))
        delay_indirect = timestamp + datetime.timedelta(0, math.floor(dt[j] * indirect_factor))
        
        delay.append([delay_direct, delay_indirect])
    
    delayed_utc.append(delay)
    
    utc_start = flare_range['start_UTC'][i]
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
                epd_connected_flares.append(flare_range.index[0] + count)
                temp = True
                break
        if temp:
            break
    count += 1
    
for i in epd_connected_flares:
    epd_connected_flares_peak_utc.append(stix_flares['peak_UTC'][i])

plots.plot_step_data(df_step_electron, 
                     running_mean, 
                     running_std, 
                     sigma_factor, 
                     offset, f'{config.OUTPUT_DIR}/Images/step.jpg', connected_flares["peak_UTC"].to_list(),
                     epd_connected_flares_peak_utc, events, flare_range['peak_UTC'])

print(epd_connected_flares)
print(epd_connected_flares_peak_utc)