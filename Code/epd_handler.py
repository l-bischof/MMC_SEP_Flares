from solo_epd_loader import epd_load
import pandas as pd
import numpy as np
import math
import datetime
import config

import misc_handler
import plots

# Factor with which epd data gets compressed. (Sum over x seconds)
time_resolution = 300

def load_data(sensor, utc_start, utc_end, viewing = 'omni'):
    '''
    (string) sensor: 'ept', 'het', or 'step'
    (int) startdate: yyyymmdd
    (int) enddate:  yyyymmdd
    (string) level: 'l2' or 'll' -> defines level of data product: level 2 ('l2') or low-latency ('ll'). By default 'l2'.
    (string) viewing: 'sun', 'asun', 'north', 'south', 'omni' or None; not eeded for sensor = 'step'.
        'omni' is just calculated as the average of the other four viewing directions: ('sun'+'asun'+'north'+'south')/4
    (string) path: directory in which Solar Orbiter data is/should be organized; e.g. '/home/userxyz/solo/data/'. See `Data folder structure` for more details.
    (bool) autodownload: if True, will try to download missing data files from SOAR
    (bool) only_averages: If True, will for STEP only return the averaged fluxes, and not the data of each of the 15 Pixels. This will reduce the memory consumption. By default False.
    '''
    level = 'l2' # always load l2 data!
    
    startdate = int(utc_start[0:4] + utc_start[5:7] + utc_start[8:10])
    enddate = int(utc_end[0:4] + utc_end[5:7] + utc_end[8:10])
    
    # df_1: includes Ion_Flux, Ion_Uncertainty, Ion_Rate, Alpha_Flux, Alpha_Uncertainty, Alpha_Rate, ...
    # df_2: includes Electron_Flux, Electron_Uncertainty, Electron_Rate, ...
    # energies: includes the bins of energy ranges
    if sensor == 'ept':
        df_1, df_2, energies = epd_load(sensor, startdate, enddate, level, viewing, path = None, autodownload = True, only_averages = False)
        
        return df_1, df_2, energies
    
    if sensor == 'step':
        df_1, energies = epd_load(sensor, startdate, enddate, level, viewing, path = None, autodownload = True, only_averages = False)
        
        return df_1, energies

def reduce_data(df, sensor = 'ept'):
    '''
    Sums up particle counts for each minute to decrease amount of data load by factor (time_resolution, currently 300 (5 mins))
    Factor has to be a divisor of 86400
    
    Accounts for missing data and fills these timespans with empty data (nan)
    
    parameters:
    df: Pandas Dataframe that holds data to be reduced
    '''  
    utc = str(df.index[0])[0:10] # get date as string
    if(len(df) >= 2):
        utc = str(df.index[1])[0:10]  #take second entry as first may be rounded up
    date = utc[2:]
    
    df_new = pd.DataFrame()
    
    time_limit = datetime.datetime.strptime(date + " 00:00:00", "%y-%m-%d %H:%M:%S") + datetime.timedelta(0, time_resolution)
    if (sensor == 'ept'):
        time = datetime.datetime.strptime(date + " 00:00:00", "%y-%m-%d %H:%M:%S")
        time_delta = 1
    if (sensor == 'step'):
        date_str = df.index[0].strftime("%y-%m-%d %H:%M:%S")
        time = datetime.datetime.strptime(date_str, "%y-%m-%d %H:%M:%S")
        time_delta = 10
    
    start_index = df.index[0]
    
    # loop through every index of given dataframe, this ensures to include all data that is given to be copied to reduced data
    for i in df.index:
        next_timestamp = i.replace(microsecond = 0) # round to seconds (always round down)
        
        # if one second is skipped due to instrument delay, adjust time
        if (next_timestamp == time + datetime.timedelta(0, 1)):
            time += datetime.timedelta(0, 1)
        
        # there is no data to work with
        if (next_timestamp != time):
            # loop through timeframe of missing data
            while time < next_timestamp:
                # if we hit the end of a time interval or the end of the day, add current interval
                if (time == time_limit or time == datetime.datetime.strptime(date + " 23:59:59", "%y-%m-%d %H:%M:%S")):
                    # add complete interval to dataframe
                    df_new = pd.concat([df_new, df.iloc[df.index.get_loc(start_index):df.index.get_loc(i)].sum().to_frame().T], ignore_index = True)
                    
                    # increase time limit to end of next interval
                    time_limit += datetime.timedelta(0, time_resolution)
                    # adjust start index of next interval
                    start_index = i

                    # see if it is possible to skip next timeinterval
                    while next_timestamp > time_limit:
                        # add empty row to dataframe
                        df_new = pd.concat([df_new, pd.Series(np.nan, df.columns).to_frame().T], ignore_index = True)
                        # increase time limit to end of next interval
                        time_limit += datetime.timedelta(0, time_resolution)
                        time += datetime.timedelta(0, time_resolution)
                        
                time += datetime.timedelta(0, time_delta)
        
        # there is data to work with:
        # check if we switch to next 5min interval
        if (next_timestamp >= time_limit or (len(df.index) in [86399, 86400] and next_timestamp == datetime.datetime.strptime(date + " 23:59:59", "%y-%m-%d %H:%M:%S"))
            or (len(df.index) == 1440 and next_timestamp >= datetime.datetime.strptime(date + " 23:59:00", "%y-%m-%d %H:%M:%S"))
            or (len(df.index) == 8640 and next_timestamp >= datetime.datetime.strptime(date + " 23:59:50", "%y-%m-%d %H:%M:%S"))
            or (len(df.index) == 17280 and next_timestamp >= datetime.datetime.strptime(date + " 23:59:55", "%y-%m-%d %H:%M:%S"))):
            
            last_element = 0
            if ((len(df.index) in [86399, 86400] and next_timestamp == datetime.datetime.strptime(date + " 23:59:59", "%y-%m-%d %H:%M:%S"))
            or (len(df.index) == 1440 and next_timestamp >= datetime.datetime.strptime(date + " 23:59:00", "%y-%m-%d %H:%M:%S"))
            or (len(df.index) == 8640 and next_timestamp >= datetime.datetime.strptime(date + " 23:59:50", "%y-%m-%d %H:%M:%S"))
            or (len(df.index) == 17280 and next_timestamp >= datetime.datetime.strptime(date + " 23:59:55", "%y-%m-%d %H:%M:%S"))):
                last_element = 1
            
            # add complete interval to dataframe
            df_new = pd.concat([df_new, df.iloc[df.index.get_loc(start_index):df.index.get_loc(i) + last_element].sum().to_frame().T], ignore_index = True)

            if (sensor == 'step'):
                for col in ['QUALITY_BITMASK', 'QUALITY_FLAG', 'SMALL_PIXELS_FLAG']:
                    if (col in df_new.columns):
                        df_new[col][df_new.index[-1]] = df.iloc[df.index.get_loc(start_index):df.index.get_loc(i) + last_element][col].max()
            
            # increase time limit to end of next interval
            time_limit += datetime.timedelta(0, time_resolution)
            # adjust start index of next interval
            start_index = i
            
        time += datetime.timedelta(0, time_delta)
    
    # fill with empty rows if there is space after last entries in dataframe
    while len(df_new) < 288:
        df_new = pd.concat([df_new, pd.Series(np.nan, df.columns).to_frame().T], ignore_index = True)
    
    # change index back to datetime with correct minutes
    datetime_series = pd.Series(pd.date_range(utc, periods = 86400 / time_resolution, freq = str(time_resolution) + "S"))
    df_new.set_index(datetime_series, inplace = True)
    
    return df_new

def load_pickles(sensor, start_date, end_date, particle = 'electron', viewing = 'none'):
    '''
    load data from self built database
    
    parameters:
    sensor:     string with name of sensor
    viewing:    string with name of viewing angle [sun, asun, north, south]
    start_date: string of starting date
    end_date:   string of end date
    particle:   string of particle type [ion, electron]
    '''
    df = pd.DataFrame()
    date = start_date
    count = 0
    while date != misc_handler.next_date(end_date):
        if sensor == 'ept':
            df_new = pd.read_pickle(f'{config.CACHE_DIR}/EPD_Dataset/' + sensor + '/' + viewing + '/' + particle + '/' + date + '.pkl')
            
        if sensor == 'step':
            df_new = pd.read_pickle(f'{config.CACHE_DIR}/EPD_Dataset/' + sensor + '/' + date + '.pkl')
        
        df = pd.concat([df, df_new], ignore_index = True)
        
        count += 1
        date = misc_handler.next_date(date)
    
    # change index back to datetime with correct minutes
    datetime_series = pd.Series(pd.date_range(start_date, periods = 86400 / time_resolution * count, freq = str(time_resolution) + "S"))
    df.set_index(datetime_series, inplace = True)
    return df

def background(df):
    '''
    !!! Not in use anymore  !!!
    !!! Use running average !!!
    compute background noise of arriving particle count
    
    TODO: find better way to compute background than using the mean (or mean of log) of non-nan-values
    '''
    df += 1.1 # prevent zero division (adding a count of one does hardly change anything in this dataset)
    data = df.loc[:, :]
    data[data == 0] = np.nan
    
    '''
    # 1 average over log of measurements (reduces influence of peaks, if there are any during the timeframe)
    background = np.nanmean(np.log(data.to_numpy()), axis = 0)
        
    return np.exp(background)
    '''
    
    # 2 average measurements (might be too high as small events during timeframe already increase value by orders of magnitude)
    background = np.nanmean(data.to_numpy(), axis = 0)
        
    return background
    

def find_event(df, mean, std, sigma_factor):
    '''
    Finds event in pandas dataframe provided and returns the pairs of [start_time, end_time] in an array.
    
    Event if incoming particle numbers are at sigma_factor times the standard deviation above the running average in 5 of the particle bins.
    '''    
    min_bins = 5 # min number of bins required to measure a rise in particles to classify as an event
    
    ongoing_event = False
    event_start = False
    event_end = False
    
    events = []
    new_event = []
    max_val = 0
    max_mem = []
    
    for j in range(len(df.index)):
        # print("Working on:", df.index[j])
        num_bins = 0
        if not ongoing_event: # there is currently no event going on -> check if new event starts
            for i in df.columns[:]:
                if mean[i][j] == 0:
                    continue
                if df[i][j] - mean[i][j] >= sigma_factor * std[i][j] and not np.isnan(df[i][j]):
                    num_bins += 1
            
            if num_bins >= min_bins:
                # search for next point that has value lower than threshold
                temp = j
                last = max(0, j - 1)
                temp_bins = num_bins
                while temp < len(df.index) and temp_bins >= min_bins:
                    temp_bins = 0
                    for i in df.columns[:]:
                        if df[i][temp] - mean[i][last] >= sigma_factor * std[i][last] or np.isnan(df[i][temp]):
                            temp_bins += 1
                    temp += 1
                if temp - j > (600 / time_resolution):
                    event_start = True
                    max_val = df[df.columns[1]][j]
                
        else: # there is currently already an event going on -> check if event continues
            ongoing_event = False
            for i in df.columns[:]:
                if mean[i][j] == 0:
                    continue
                if df[i][j] - mean[i][j] >= sigma_factor * std[i][j] and not np.isnan(df[i][j]):
                    num_bins += 1
                    
            if num_bins >= min_bins:
                ongoing_event = True
                if df[df.columns[1]][j] > max_val:
                    max_val = df[df.columns[1]][j]
                
            if not ongoing_event:
                event_end = True
        
        if event_start:
            ongoing_event = True
            event_start = False
            start_time = df.index[j]
            new_event.append(start_time) # save starting time of newly found event
            # print('Event started at: ' + str(start_time))
        if event_end:
            event_end = False
            end_time = df.index[j - 1]
            new_event.append(end_time) # save ending time of newly found event
            events.append(new_event) # save newly found event in list
            if (max_val <= 0):
                print("log of <= 0 on ", end_time)
            else:
                max_mem.append(math.log10(max_val)) # save max mesurement during event
            new_event = [] # clear for next event
            # print('event lasted until: ' + str(end_time))
            
    if ongoing_event:
        end_time = df.index[j]
        new_event.append(end_time) # save ending time of newly found event
        events.append(new_event) # save newly found event in list
        # print('event lasted until: ' + str(end_time) + ' and might continue longer then time horizon spezified.')

    plots.histogram(max_mem, np.arange(0, 12, 0.5), f"{config.OUTPUT_DIR}/Images/Hist/magnitude_detected_events.jpg")
    
    return events

def bin_upper_energy_limit(bin, type):
    '''
    returns upper energy limit of chosen bin
    
    parameters:
    bin:    int of energy bin that we look at
    type:   string of particle type [ion, electron]
    '''
    return float(misc_handler.get_epd_bins(type)[bin][0][9:15])
    

def compute_particle_speed(n_bins, particle_type):
    '''
    Compute the relativistic speed of the fastest particles that are measured in the corresponding bin using E = 1/2 * m * v**2
    
    Parameters:
    bin = number of bin of which the particle speed should be returned
    particle_type = ['ion', 'electron']
    '''
    m = 0
    c = 299792458 # [m/s] speed of light
    if particle_type == 'ion':
        # mass of proton
        m = 1.67262192e-27
    if particle_type == 'electron':
        # mass of electron
        m = 9.1093837015e-31
        
    KE = np.empty(n_bins)
    
    for i in range(n_bins):
        KE[i] = bin_upper_energy_limit(i, particle_type) * 1.60218e-13 # get energy from bins in [MeV] and convert to Joules [J]
    
    return np.sqrt(1 - (1 / (KE / (m * c**2) + 1)**2)) * c  # relativistic formula for kinetic energy

def running_average(df):
    '''
    Computes running average to enable finding events in EPD data
    
    parameters:
    df:     Pandas Dataframe with EPD data
    '''
    df_background = df.copy()
    df_std = df.copy()
    length = 18 # number of bins to average over (x * time resolution)
    delay = 0   # number of bins to delay the average (x * time resolution). This allows for the detection of more gradual peaks
    
    df_temp = df.iloc[0:length].reset_index(drop = True)
    
    '''
    for i in df_temp.columns:
        for j in df_temp[i]:
            if j < 0:
                df_temp[i][j] = 0
    '''
    
    count = 0
    # loop over all rows to calculate running average
    for idx in df.index:
        # exit if end of timeframe is reached
        if count + delay >= len(df_background):
            break
        
        # write running average to current row
        df_background.iloc[count + delay] = df_temp.sum() / length
        
        for col in df.columns:
            df_std.iloc[count + delay][col] = np.std(df_temp[col].to_numpy())

        df_temp.loc[count % length] = df.iloc[count]
        
        count += 1
    
    for i in range(delay):  
        df_background.iloc[i] = df_background.iloc[delay]
        df_std.iloc[i] = df_std.iloc[delay]
    
    return df_background, df_std