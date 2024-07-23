import os
import pandas as pd
import numpy as np
import datetime

import misc_handler
import epd_handler

'''
Build own dataset of EPD data to reduce access time and memory usage.
Reduce data to temporal accuracy of 5 mins to further reduce dataset size by factor of 300.
Deletes automatically downloaded files with original data after data reduction is done.

1. Specify start and end date
    1.1 I do not recommend inputting a timespan of more than a few months due a higher chance of encountering a problem
2. Wait for downloads and data reduction to finish
    2.1 This may take a while
'''

dir_dest = 'EPD_Dataset/'
sensor = 'ept'

# Downloads complete for 2021-01-01 to 2023-05-02
date = '2021-02-14'
end_date = '2021-04-30'

ion_columns = ['Ion_Flux_0', 'Ion_Flux_1', 'Ion_Flux_2', 'Ion_Flux_3', 'Ion_Flux_4', 'Ion_Flux_5', 'Ion_Flux_6', 'Ion_Flux_7', 'Ion_Flux_8', 'Ion_Flux_9', 'Ion_Flux_10', 'Ion_Flux_11',
               'Ion_Flux_12', 'Ion_Flux_13', 'Ion_Flux_14', 'Ion_Flux_15', 'Ion_Flux_16', 'Ion_Flux_17', 'Ion_Flux_18', 'Ion_Flux_19', 'Ion_Flux_20', 'Ion_Flux_21', 'Ion_Flux_22',
               'Ion_Flux_23', 'Ion_Flux_24', 'Ion_Flux_25', 'Ion_Flux_26', 'Ion_Flux_27', 'Ion_Flux_28', 'Ion_Flux_29', 'Ion_Flux_30', 'Ion_Flux_31', 'Ion_Flux_32', 'Ion_Flux_33',
               'Ion_Flux_34', 'Ion_Flux_35', 'Ion_Flux_36', 'Ion_Flux_37', 'Ion_Flux_38', 'Ion_Flux_39', 'Ion_Flux_40', 'Ion_Flux_41', 'Ion_Flux_42', 'Ion_Flux_43', 'Ion_Flux_44',
               'Ion_Flux_45', 'Ion_Flux_46', 'Ion_Flux_47', 'Ion_Flux_48', 'Ion_Flux_49', 'Ion_Flux_50', 'Ion_Flux_51', 'Ion_Flux_52', 'Ion_Flux_53', 'Ion_Flux_54', 'Ion_Flux_55',
               'Ion_Flux_56', 'Ion_Flux_57', 'Ion_Flux_58', 'Ion_Flux_59', 'Ion_Flux_60', 'Ion_Flux_61', 'Ion_Flux_62', 'Ion_Flux_63']
            
electron_columns = ['Electron_Flux_0', 'Electron_Flux_1', 'Electron_Flux_2', 'Electron_Flux_3', 'Electron_Flux_4', 'Electron_Flux_5', 'Electron_Flux_6', 'Electron_Flux_7', 'Electron_Flux_8',
                    'Electron_Flux_9', 'Electron_Flux_10', 'Electron_Flux_11', 'Electron_Flux_12', 'Electron_Flux_13', 'Electron_Flux_14', 'Electron_Flux_15', 'Electron_Flux_16',
                    'Electron_Flux_17', 'Electron_Flux_18', 'Electron_Flux_19', 'Electron_Flux_20', 'Electron_Flux_21', 'Electron_Flux_22', 'Electron_Flux_23', 'Electron_Flux_24',
                    'Electron_Flux_25', 'Electron_Flux_26', 'Electron_Flux_27', 'Electron_Flux_28', 'Electron_Flux_29', 'Electron_Flux_30', 'Electron_Flux_31', 'Electron_Flux_32',
                    'Electron_Flux_33']

step_columns = ['DELTA_EPOCH', 'Integral_Avg_Flux_0', 'Integral_Avg_Flux_1', 'Integral_Avg_Flux_2', 'Integral_Avg_Flux_3', 'Integral_Avg_Flux_4', 'Integral_Avg_Flux_5', 'Integral_Avg_Flux_6',
                'Integral_Avg_Flux_7', 'Integral_Avg_Flux_8', 'Integral_Avg_Flux_9', 'Integral_Avg_Flux_10', 'Integral_Avg_Flux_11', 'Integral_Avg_Flux_12', 'Integral_Avg_Flux_13',
                'Integral_Avg_Flux_14', 'Integral_Avg_Flux_15', 'Integral_Avg_Flux_16', 'Integral_Avg_Flux_17', 'Integral_Avg_Flux_18', 'Integral_Avg_Flux_19', 'Integral_Avg_Flux_20',
                'Integral_Avg_Flux_21', 'Integral_Avg_Flux_22', 'Integral_Avg_Flux_23', 'Integral_Avg_Flux_24', 'Integral_Avg_Flux_25', 'Integral_Avg_Flux_26', 'Integral_Avg_Flux_27',
                'Integral_Avg_Flux_28', 'Integral_Avg_Flux_29', 'Integral_Avg_Flux_30', 'Integral_Avg_Flux_31', 'Integral_Avg_Flux_32', 'Integral_Avg_Flux_33', 'Integral_Avg_Flux_34',
                'Integral_Avg_Flux_35', 'Integral_Avg_Flux_36', 'Integral_Avg_Flux_37', 'Integral_Avg_Flux_38', 'Integral_Avg_Flux_39', 'Integral_Avg_Flux_40', 'Integral_Avg_Flux_41',
                'Integral_Avg_Flux_42', 'Integral_Avg_Flux_43', 'Integral_Avg_Flux_44', 'Integral_Avg_Flux_45', 'Integral_Avg_Flux_46', 'Integral_Avg_Flux_47', 'Integral_Avg_Uncertainty_0',
                'Integral_Avg_Uncertainty_1', 'Integral_Avg_Uncertainty_2', 'Integral_Avg_Uncertainty_3', 'Integral_Avg_Uncertainty_4', 'Integral_Avg_Uncertainty_5', 'Integral_Avg_Uncertainty_6',
                'Integral_Avg_Uncertainty_7', 'Integral_Avg_Uncertainty_8', 'Integral_Avg_Uncertainty_9', 'Integral_Avg_Uncertainty_10', 'Integral_Avg_Uncertainty_11', 'Integral_Avg_Uncertainty_12',
                'Integral_Avg_Uncertainty_13', 'Integral_Avg_Uncertainty_14', 'Integral_Avg_Uncertainty_15', 'Integral_Avg_Uncertainty_16', 'Integral_Avg_Uncertainty_17', 'Integral_Avg_Uncertainty_18',
                'Integral_Avg_Uncertainty_19', 'Integral_Avg_Uncertainty_20', 'Integral_Avg_Uncertainty_21', 'Integral_Avg_Uncertainty_22', 'Integral_Avg_Uncertainty_23', 'Integral_Avg_Uncertainty_24',
                'Integral_Avg_Uncertainty_25', 'Integral_Avg_Uncertainty_26', 'Integral_Avg_Uncertainty_27', 'Integral_Avg_Uncertainty_28', 'Integral_Avg_Uncertainty_29', 'Integral_Avg_Uncertainty_30',
                'Integral_Avg_Uncertainty_31', 'Integral_Avg_Uncertainty_32', 'Integral_Avg_Uncertainty_33', 'Integral_Avg_Uncertainty_34', 'Integral_Avg_Uncertainty_35', 'Integral_Avg_Uncertainty_36',
                'Integral_Avg_Uncertainty_37', 'Integral_Avg_Uncertainty_38', 'Integral_Avg_Uncertainty_39', 'Integral_Avg_Uncertainty_40', 'Integral_Avg_Uncertainty_41', 'Integral_Avg_Uncertainty_42',
                'Integral_Avg_Uncertainty_43', 'Integral_Avg_Uncertainty_44', 'Integral_Avg_Uncertainty_45', 'Integral_Avg_Uncertainty_46', 'Integral_Avg_Uncertainty_47', 'Magnet_Avg_Flux_0',
                'Magnet_Avg_Flux_1', 'Magnet_Avg_Flux_2', 'Magnet_Avg_Flux_3', 'Magnet_Avg_Flux_4', 'Magnet_Avg_Flux_5', 'Magnet_Avg_Flux_6', 'Magnet_Avg_Flux_7', 'Magnet_Avg_Flux_8',
                'Magnet_Avg_Flux_9', 'Magnet_Avg_Flux_10', 'Magnet_Avg_Flux_11', 'Magnet_Avg_Flux_12', 'Magnet_Avg_Flux_13', 'Magnet_Avg_Flux_14', 'Magnet_Avg_Flux_15', 'Magnet_Avg_Flux_16',
                'Magnet_Avg_Flux_17', 'Magnet_Avg_Flux_18', 'Magnet_Avg_Flux_19', 'Magnet_Avg_Flux_20', 'Magnet_Avg_Flux_21', 'Magnet_Avg_Flux_22', 'Magnet_Avg_Flux_23', 'Magnet_Avg_Flux_24',
                'Magnet_Avg_Flux_25', 'Magnet_Avg_Flux_26', 'Magnet_Avg_Flux_27', 'Magnet_Avg_Flux_28', 'Magnet_Avg_Flux_29', 'Magnet_Avg_Flux_30', 'Magnet_Avg_Flux_31', 'Magnet_Avg_Flux_32',
                'Magnet_Avg_Flux_33', 'Magnet_Avg_Flux_34', 'Magnet_Avg_Flux_35', 'Magnet_Avg_Flux_36', 'Magnet_Avg_Flux_37', 'Magnet_Avg_Flux_38', 'Magnet_Avg_Flux_39', 'Magnet_Avg_Flux_40',
                'Magnet_Avg_Flux_41', 'Magnet_Avg_Flux_42', 'Magnet_Avg_Flux_43', 'Magnet_Avg_Flux_44', 'Magnet_Avg_Flux_45', 'Magnet_Avg_Flux_46', 'Magnet_Avg_Flux_47', 'Magnet_Avg_Uncertainty_0',
                'Magnet_Avg_Uncertainty_1', 'Magnet_Avg_Uncertainty_2', 'Magnet_Avg_Uncertainty_3', 'Magnet_Avg_Uncertainty_4', 'Magnet_Avg_Uncertainty_5', 'Magnet_Avg_Uncertainty_6',
                'Magnet_Avg_Uncertainty_7', 'Magnet_Avg_Uncertainty_8', 'Magnet_Avg_Uncertainty_9', 'Magnet_Avg_Uncertainty_10', 'Magnet_Avg_Uncertainty_11', 'Magnet_Avg_Uncertainty_12',
                'Magnet_Avg_Uncertainty_13', 'Magnet_Avg_Uncertainty_14', 'Magnet_Avg_Uncertainty_15', 'Magnet_Avg_Uncertainty_16', 'Magnet_Avg_Uncertainty_17', 'Magnet_Avg_Uncertainty_18',
                'Magnet_Avg_Uncertainty_19', 'Magnet_Avg_Uncertainty_20', 'Magnet_Avg_Uncertainty_21', 'Magnet_Avg_Uncertainty_22', 'Magnet_Avg_Uncertainty_23', 'Magnet_Avg_Uncertainty_24',
                'Magnet_Avg_Uncertainty_25', 'Magnet_Avg_Uncertainty_26', 'Magnet_Avg_Uncertainty_27', 'Magnet_Avg_Uncertainty_28', 'Magnet_Avg_Uncertainty_29', 'Magnet_Avg_Uncertainty_30',
                'Magnet_Avg_Uncertainty_31', 'Magnet_Avg_Uncertainty_32', 'Magnet_Avg_Uncertainty_33', 'Magnet_Avg_Uncertainty_34', 'Magnet_Avg_Uncertainty_35', 'Magnet_Avg_Uncertainty_36',
                'Magnet_Avg_Uncertainty_37', 'Magnet_Avg_Uncertainty_38', 'Magnet_Avg_Uncertainty_39', 'Magnet_Avg_Uncertainty_40', 'Magnet_Avg_Uncertainty_41', 'Magnet_Avg_Uncertainty_42',
                'Magnet_Avg_Uncertainty_43', 'Magnet_Avg_Uncertainty_44', 'Magnet_Avg_Uncertainty_45', 'Magnet_Avg_Uncertainty_46', 'Magnet_Avg_Uncertainty_47', 'QUALITY_BITMASK', 'QUALITY_FLAG']

# read data day by day and store it as pickle file
while date != misc_handler.next_date(end_date) and sensor == 'ept':
    print('Currently working on files of: ' + date)
    
    # initialize dataframes for omni viewing (sum of all angles divided by 4)
    df_ion_omni = pd.DataFrame()
    df_electron_omni = pd.DataFrame()
    
    for viewing in ['sun', 'asun', 'south', 'north']:
        df_ions_alpha, df_electrons, energies = epd_handler.load_data(sensor, date, date, viewing)
        
        print(energies)
        
        # check if there is no data available -> empty dataframe (nan)
        if len(df_ions_alpha) == 0:
            df_ion = pd.Series(np.nan, ion_columns).to_frame().T
            df_electron = pd.Series(np.nan, electron_columns).to_frame().T
            
            df_ion.set_index(pd.Series(datetime.datetime.strptime(date[2:] + " 00:00:00", "%y-%m-%d %H:%M:%S")), inplace = True)
            df_electron.set_index(pd.Series(datetime.datetime.strptime(date[2:] + " 00:00:00", "%y-%m-%d %H:%M:%S")), inplace = True)
            
        else:
            df_ion = df_ions_alpha['Ion_Flux']
            df_electron = df_electrons['Electron_Flux']

        # combine data to 5min intervals and fill missing data with nan
        df_ion_red = epd_handler.reduce_data(df_ion)
        df_electron_red = epd_handler.reduce_data(df_electron)
        
        # define location to save files
        dest_ion = dir_dest + sensor + '/' + viewing + '/ion/' + date + '.pkl'
        dest_electron = dir_dest + sensor + '/' + viewing + '/electron/' + date + '.pkl'
        
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
    dest_ion = dir_dest + sensor + '/omni/ion/' + date + '.pkl'
    dest_electron = dir_dest + sensor + '/omni/electron/' + date + '.pkl'
    
    # division by 4 as currently data is sum of 4 angles
    df_ion_omni = df_ion_omni.div(4)
    df_electron_omni = df_electron_omni.div(4)
    
    # save omni viewing to pickle file
    df_ion_omni.to_pickle(dest_ion)
    df_electron_omni.to_pickle(dest_electron)
    
    # delete downloaded files to free up memory space
    # depending on timeframe files end with: '_V01.cdf', '_V02.cdf' or '_V03.cdf'
    for viewing in ['sun', 'asun', 'south', 'north']:
        path = "l2/epd/" + sensor + "/solo_L2_epd-" + sensor + "-" + viewing + "-rates_" + date[0:4] + date[5:7] + date[8:10] + "_V01.cdf"
        if os.path.isfile(path):
            os.remove(path)
        path = "l2/epd/" + sensor + "/solo_L2_epd-" + sensor + "-" + viewing + "-rates_" + date[0:4] + date[5:7] + date[8:10] + "_V02.cdf"
        if os.path.isfile(path):
            os.remove(path)
        path = "l2/epd/" + sensor + "/solo_L2_epd-" + sensor + "-" + viewing + "-rates_" + date[0:4] + date[5:7] + date[8:10] + "_V03.cdf"
        if os.path.isfile(path):
            os.remove(path)
    
    # get next date
    date = misc_handler.next_date(date)   
    
while date != misc_handler.next_date(end_date) and sensor == 'step':
    print('Currently working on files of: ' + date)
    
    df_step, energies = epd_handler.load_data(sensor, date, date)
    
    print(energies)
    
    # check if there is no data available -> empty dataframe (nan)
    if len(df_step) == 0:
        df_step = pd.Series(np.nan, step_columns).to_frame().T
        
        df_step.set_index(pd.Series(datetime.datetime.strptime(date[2:] + " 00:00:00", "%y-%m-%d %H:%M:%S")), inplace = True)
    
    else:
        # remove unnecessary columns
        col_to_drop = []
        length = 32
        if len(df_step.columns) < 1000:
            length = 8
        for i in range(length):
            for j in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15']:
                col_to_drop.append('Integral_' + j + '_Flux_' + str(i))
                col_to_drop.append('Integral_' + j + '_Uncertainty_' + str(i))
                col_to_drop.append('Magnet_' + j + '_Flux_' + str(i))
                col_to_drop.append('Magnet_' + j + '_Uncertainty_' + str(i))
        df_step = df_step.drop(col_to_drop, axis = 1)
    
    # check if there is no data available -> empty dataframe (nan)
    if len(df_step) == 0:
        df_step = pd.Series(np.nan, df_step.columns).to_frame().T
        
        df_step.set_index(pd.Series(datetime.datetime.strptime(date[2:] + " 00:00:00", "%y-%m-%d %H:%M:%S")), inplace = True)

    # combine data to 5min intervals and fill missing data with nan
    # then save the reduced data to a pickle file
    epd_handler.reduce_data(df_step, sensor).to_pickle(dir_dest + sensor + '/' + date + '.pkl')
    
    # delete downloaded files to free up memory space
    # depending on timeframe files end with: '_V01.cdf', '_V02.cdf' or '_V03.cdf'
    path = "l2/epd/" + sensor + "/solo_L2_epd-" + sensor + "-rates_" + date[0:4] + date[5:7] + date[8:10] + "_V01.cdf"
    if os.path.isfile(path):
        os.remove(path)
    path = "l2/epd/" + sensor + "/solo_L2_epd-" + sensor + "-rates_" + date[0:4] + date[5:7] + date[8:10] + "_V02.cdf"
    if os.path.isfile(path):
        os.remove(path)
    path = "l2/epd/" + sensor + "/solo_L2_epd-" + sensor + "-rates_" + date[0:4] + date[5:7] + date[8:10] + "_V03.cdf"
    if os.path.isfile(path):
        os.remove(path)
    path = "l2/epd/" + sensor + "/solo_L2_epd-" + sensor + "-main_" + date[0:4] + date[5:7] + date[8:10] + "_V01.cdf"
    if os.path.isfile(path):
        os.remove(path)
    
    # get next date
    date = misc_handler.next_date(date)