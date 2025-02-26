import os
import pandas as pd
import numpy as np
import datetime

import misc
from .data_helper import reduce_data
from .loader import load_data
import config

dir_dest = f'{config.CACHE_DIR}/EPD_Dataset/'
# define column names arrays for ept and step
ion_columns = []
electron_columns = []

for i in range(64):
    ion_columns.append('Ion_Flux_' + str(i))
    if i < 34:
        electron_columns.append('Electron_Flux_' + str(i))


step_columns_long = ['DELTA_EPOCH']
step_columns_short = ['DELTA_EPOCH']

for i in ['Integral_Avg_', 'Magnet_Avg_']:
    for j in ['Flux_', "Uncertainty_"]:
        for k in range(48):
            if k < 32:
                step_columns_short.append(i + j + str(k))
            step_columns_long.append(i + j + str(k))
            
for i in [step_columns_short, step_columns_long]:
    i.append('QUALITY_BITMASK')
    i.append('QUALITY_FLAG')



def download_step(start_date: str, end_date: str):
    sensor = "step"
    while start_date != misc.next_date(end_date):
        print('Currently working on files of: ' + start_date)
        
        df_step, _ = load_data(sensor, start_date, start_date)
        
        # check if there is no data available -> empty dataframe (nan)
        if len(df_step) == 0:
            if datetime.datetime.strptime(start_date[2:], "%y-%m-%d") >= datetime.datetime.strptime("21-10-23", "%y-%m-%d"):
                df_step = pd.Series(np.nan, step_columns_short).to_frame().T
            else:
                df_step = pd.Series(np.nan, step_columns_long).to_frame().T
            
            df_step.set_index(pd.Series(datetime.datetime.strptime(start_date[2:] + " 00:00:00", "%y-%m-%d %H:%M:%S")), inplace = True)
        
        else:
            # remove unnecessary columns
            col_to_drop = []
            length = 32
            if len(df_step.columns) < 1000:
                length = 8
            for i in range(length):
                for j in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15']:
                    for k in ['Integral_', 'Magnet_']:
                        col_to_drop.append(k + j + '_Flux_' + str(i))
                        col_to_drop.append(k + j + '_Uncertainty_' + str(i))
            df_step = df_step.drop(col_to_drop, axis = 1)
        
        # check if there is no data available -> empty dataframe (nan)
        if len(df_step) == 0:
            df_step = pd.Series(np.nan, df_step.columns).to_frame().T
            
            df_step.set_index(pd.Series(datetime.datetime.strptime(start_date[2:] + " 00:00:00", "%y-%m-%d %H:%M:%S")), inplace = True)

        # combine data to 5min intervals and fill missing data with nan
        # then save the reduced data to a pickle file
        directory = dir_dest + sensor + '/'
        os.makedirs(directory, exist_ok=True)
        reduce_data(df_step, sensor).to_pickle(directory + start_date + '.pkl')
        
        # get next date
        start_date = misc.next_date(start_date)


def download_ept(start_date: str, end_date: str):
    sensor = "ept"
    while start_date != misc.next_date(end_date):
        print('Currently working on files of: ' + start_date)
        
        # initialize dataframes for omni viewing (sum of all angles divided by 4)
        df_ion_omni = pd.DataFrame()
        df_electron_omni = pd.DataFrame()
        
        for viewing in ['sun', 'asun', 'south', 'north']:
            df_ions_alpha, df_electrons, _ = load_data(sensor, start_date, start_date, viewing)
            
            # check if there is no data available -> empty dataframe (nan)
            if len(df_ions_alpha) == 0:
                df_ion = pd.Series(np.nan, ion_columns).to_frame().T
                df_electron = pd.Series(np.nan, electron_columns).to_frame().T
                
                df_ion.set_index(pd.Series(datetime.datetime.strptime(start_date[2:] + " 00:00:00", "%y-%m-%d %H:%M:%S")), inplace = True)
                df_electron.set_index(pd.Series(datetime.datetime.strptime(start_date[2:] + " 00:00:00", "%y-%m-%d %H:%M:%S")), inplace = True)
                
            else:
                df_ion = df_ions_alpha['Ion_Flux']
                df_electron = df_electrons['Electron_Flux']

            # combine data to 5min intervals and fill missing data with nan
            df_ion_red = reduce_data(df_ion)
            df_electron_red = reduce_data(df_electron)
            
            # define location to save files
            os.makedirs(dir_dest + sensor + '/' + viewing + '/ion/', exist_ok=True)
            dest_ion = dir_dest + sensor + '/' + viewing + '/ion/' + start_date + '.pkl'
            os.makedirs(dir_dest + sensor + '/' + viewing + '/electron/', exist_ok=True)
            dest_electron = dir_dest + sensor + '/' + viewing + '/electron/' + start_date + '.pkl'
            
            # sum up all data for omni viewing
            if viewing == 'sun':
                df_ion_omni = df_ion_red
                df_electron_omni = df_electron_red
            else:
                df_ion_omni += df_ion_red
                df_electron_omni += df_electron_red
            
            # save data to pickle files
            df_ion_red.to_pickle(dest_ion)
            df_electron_red.to_pickle(dest_electron)
        
        # define location to save omni files 
        os.makedirs(dir_dest + sensor + '/omni/ion/', exist_ok=True)
        dest_ion = dir_dest + sensor + '/omni/ion/' + start_date + '.pkl'
        os.makedirs(dir_dest + sensor + '/omni/electron/', exist_ok=True)
        dest_electron = dir_dest + sensor + '/omni/electron/' + start_date + '.pkl'
        
        # division by 4 as currently data is sum of 4 angles
        df_ion_omni = df_ion_omni.div(4)
        df_electron_omni = df_electron_omni.div(4)
        
        # save omni viewing to pickle file
        df_ion_omni.to_pickle(dest_ion)
        df_electron_omni.to_pickle(dest_electron)
        
        # get next date
        start_date = misc.next_date(start_date)


def download_files(start_date: str, end_date: str, sensor):
    match sensor:
        case "ept":
            download_ept(start_date, end_date)
        case "step":
            download_step(start_date, end_date)
        case _:
            raise Exception("Unexpected Sensor")
 
    
