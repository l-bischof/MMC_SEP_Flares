import numpy as np
import pandas as pd
import math
import config

DATA_QUALITY_COLUMNS = {'QUALITY_BITMASK', 'QUALITY_FLAG', 'SMALL_PIXELS_FLAG'}

def reduce_data(_df: pd.DataFrame, sensor=""):
    '''
    Sums up particle counts for each minute to decrease amount of data load by factor (time_resolution, currently 300 (5 mins))
    Factor has to be a divisor of 86400
    
    Accounts for missing data and fills these timespans with empty data (nan)
    
    parameters:
    df: Pandas Dataframe that holds data to be reduced
    '''
    df = _df.copy()
    # Assuming that the next hour of the first index is 00:00 of the correct day
    date = df.index[0].round("d")
    grouped = df.resample(f"{config.TIME_RESOLUTION}s", origin=date)
    df_new = pd.DataFrame()
    df_new = grouped.sum()

    # Data-Quality Columns
    column_intersection = DATA_QUALITY_COLUMNS.intersection(df_new.columns)
    # Pandas doesn't like sets
    column_intersection = list(column_intersection)

    # For Quality Columns the worst (highest) value is of interest
    df_new[column_intersection] = grouped[column_intersection].max()

    # To cap it at end of day
    max_index = (24*60*60) // config.TIME_RESOLUTION

    # Filling up with NaNs, if not enough Datapoints (shouldn't happen very often)
    required_indicies = pd.date_range(date, periods=max_index, freq=f"{config.TIME_RESOLUTION}s")
    df_new = pd.DataFrame(data=df_new, index=required_indicies)
    
    return df_new[:max_index]


def is_peak_persistent(peak: pd.Timestamp, df, df_mean, df_std, sigma_factor):
    slice_start = peak
    end = peak + pd.Timedelta(minutes=5)

    current_std = df_std.loc[peak - pd.Timedelta(minutes=5)]
    current_mean = df_mean.loc[peak - pd.Timedelta(minutes=5)]

    outlier_test = df[slice_start: end] - current_mean >= sigma_factor * current_std
    mask = df[slice_start: end].isna()
    # (df_mean != 0) # Not done here for some reason?

    outlier_test |= mask
    
    results = outlier_test.sum(axis=1) >= 5

    return results.sum() == 2

def find_event(df, df_mean, df_std, sigma_factor):
    '''
    Finds event in pandas dataframe provided and returns the pairs of [start_time, end_time] in an array.
    
    Event if incoming particle numbers are at sigma_factor times the standard deviation above the running average in 5 of the particle bins.
    '''    
    min_bins = 5 # min number of bins required to measure a rise in particles to classify as an event

    # Check if we exceed background noise
    high = df - df_mean >= sigma_factor * df_std

    # If mean is zero, we want to ignore it
    high &= (df_mean != 0) # Bitwise and

    # If we have a nan we also want to ignore it
    nan_mask = df.isna() | df_mean.isna() | df_std.isna() # Bitwise OR
    high &= ~nan_mask

    # Check when enough bins are triggered
    peaks = high.sum(axis=1) >= min_bins

    # Checking if peak are persistent, by checking the next point with the data from the previous point
    # Grouping events which happen in succession
    events = []

    start = None
    last = None

    for peak in high.sum(axis=1)[peaks].keys():
        if start is None:
            if is_peak_persistent(peak, df, df_mean, df_std, sigma_factor):
                start = peak
                last = peak
            continue

        if last + pd.Timedelta(minutes=5) == peak:
            last = peak
            continue

        events.append((start, last))
        start = None
        last = None

        if is_peak_persistent(peak, df, df_mean, df_std, sigma_factor):
            start = peak
            last = peak

    if start and last:
        events.append((start, last))
    
    return events
    

def running_average(df: pd.DataFrame):
    '''
    Computes running average to enable finding events in EPD data
    
    parameters:
    df:     Pandas Dataframe with EPD data
    '''
    length = 18 # number of bins to average over (x * time resolution)

    df_mean = df.rolling(window=length).mean()
    df_std = df.rolling(window=length).std(ddof=0)

    # Shifting the Data to exclude the current Datapoint from the calculations
    # Creating new Dataframe to make sure the correct indecies are there
    df_mean = pd.DataFrame(df_mean.shift(5, freq="min"), index=df.index)
    df_std = pd.DataFrame(df_std.shift(5, freq="min"), index=df.index)
    
    return df_mean, df_std