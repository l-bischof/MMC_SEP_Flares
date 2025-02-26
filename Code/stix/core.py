import pandas as pd
import datetime
import config

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

def flares_range(start_date, end_date, dates_series):
    '''
    Get range of flare ids whose peak are within the defined timespan.
    
    parameters:
    start_date:         string of form yyyy-mm-dd
    end_date:           string of form yyyy-mm-dd
    flare_list_times:   column 'peak_UTC' of stix flare list pandas dataframe
    '''
    dates = pd.to_datetime(dates_series)
    mask = (pd.Timestamp(start_date) <= dates) & (dates < pd.Timestamp(end_date) + pd.Timedelta(days=1))
    flare_range = dates_series[mask]
    return  flare_range.index[0], flare_range.index[-1]

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