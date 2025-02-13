import pandas as pd
import datetime
import math
import config

import misc

def read_list():
    '''
    Reads csv flare list file and returns the contents as a database.
    '''
    return pd.read_csv(f"{config.CACHE_DIR}/flare_list/STIX_flarelist_w_locations_20210318_20240801_version1_pythom.csv")
 
def closest_timestamp(peak_utc):
    '''
    Finds the closest timestamp that allows to compare with the data of the connectivity tool.
    
    parameters:
    peak_utc: timestamp of flare from STIX dataset
    '''
    time = peak_utc[11:13]
    
    hour = int(time)
    if (int(time) % 6 >= 3):
        hour += 6 - int(time) % 6
        if hour == 24:
            hour = '00'
            start_date = peak_utc[2:4] + '/' + peak_utc[5:7] + '/' + peak_utc[8:10]
            temp = datetime.datetime.strptime(start_date, "%y/%m/%d")
            peak_utc = temp + datetime.timedelta(days = 1)
    else:
        hour -= int(time) % 6
        
    if(hour == 0):
        hour = '00'
    if(hour == 6):
        hour = '06'
    
    return str(peak_utc)[0:10] + 'T' + str(hour) + ':00:00.000'

def flares_range(start_date, end_date, flare_list_times):
    '''
    Get range of flare ids whose peak are within the defined timespan.
    
    parameters:
    start_date:         string of form yyyy-mm-dd
    end_date:           string of form yyyy-mm-dd
    flare_list_times:   column 'peak_UTC' of stix flare list pandas dataframe
    '''
    max_id = len(flare_list_times) - 1
    
    # no flares in this timespan
    if int(end_date[0:4]) <= 2020:
        return -1, -1
    if end_date[0:4] == 2021:
        if end_date[5:7] == '01':
            return -1, -1
        if end_date[5:7] == '02':
            if end_date[8:10] <= 13:
                return -1, -1
    
    # find start_id
    start_id = -1
    while(start_id == -1):
        i = 0
        while(start_id == -1 and i <= max_id):
            if (start_date == flare_list_times[i][0:10]):
                start_id = i
            i += 1
        start_date = misc.next_date(start_date)    
    
    # find end_id
    end_id = -1
    while(end_id == -1):
        i = max_id - 1
        while(end_id == -1 and i >= 0):
            if (end_date == flare_list_times[i][0:10]):
                end_id = i
            i -= 1
        end_date = misc.previous_date(end_date)
    
    return start_id, end_id

def convert_goes_decimal(stix_flares_goes, flare_ids):
    flare_classes = []
    
    for i in flare_ids:
        goes = stix_flares_goes[i]
        
        if str(goes) == 'nan':
            print('flare: ', i, ' has no GOES class assigned.')
            continue
    
        if goes[0] == 'A':
            flare_classes.append(0)
        if goes[0] == 'B':
            val = float(goes[1:])
            flare_classes.append(val)
        if goes[0] == 'C':
            val = 9 + float(goes[1:])
            flare_classes.append(val)
        if goes[0] == 'M':
            val = 19 + float(goes[1:])
            flare_classes.append(val)
        if goes[0] == 'X':
            val = 29 + float(goes[1:])
            flare_classes.append(val)
    
    return flare_classes

def convert_goes_variable(stix_flares_goes, flare_ids):
    flare_classes = []
    
    for i in flare_ids:
        if str(stix_flares_goes[i]) == 'nan':
            continue
        
        flare_classes.append(stix_flares_goes[i][0])
    
    return flare_classes