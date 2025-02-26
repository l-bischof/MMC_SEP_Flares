import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import math
import misc
import epd
import config


def _cleanup_sensor(df_step: pd.DataFrame, length):
    df_step_electron = pd.DataFrame(columns = [], index = df_step.index)
    zipped_columns = [(f'Electron_Avg_Flux_{i}', f"Integral_Avg_Flux_{i}", f"Magnet_Avg_Flux_{i}") for i in range(length)]

    for electron_col, integral_col, magnet_col in zipped_columns:
        df_step_electron[electron_col] = df_step[integral_col] - df_step[magnet_col]

    running_mean, running_std = epd.running_average(df_step_electron)

    return df_step_electron, running_mean, running_std


def _calculate_delays(flare_range: pd.DataFrame, length, parker_dist_series, df_step_electron):
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
    
    return df_offset_step, offset


def _find_electron_events_flare(flare_range: pd.DataFrame, length, parker_dist_series, events):
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
        epd_connected_flares_peak_utc.append(flare_range['peak_UTC'][i])
    
    return epd_connected_flares_peak_utc
    

def _plot_step_data(df, df_mean, df_std, sigma_factor, offset, connected_flares_peak_utc = [], epd_connected_flares_peak_utc = [], events_epd_utc = [], all_flare_utc = []):
    '''
    plots epd data from pandas dataframe
    
    As the step data from before October 22, 2021, is of different size as later data, there are a few patchwork solution to work around this but only use one function to handle both cases.
    Do not attempt to use date from before and after this date in one simulation!!!
    '''
    energies_32 = [['0.0057 - 0.0090 MeV'], ['0.0061 - 0.0091 MeV'], ['0.0065 - 0.0094 MeV'], ['0.0070 - 0.0098 MeV'], ['0.0075 - 0.0102 MeV'], ['0.0088 - 0.0114 MeV'], ['0.0082 - 0.0108 MeV'],
                   ['0.0095 - 0.0121 MeV'], ['0.0103 - 0.0129 MeV'], ['0.0111 - 0.0137 MeV'], ['0.0120 - 0.0146 MeV'], ['0.0130 - 0.0157 MeV'], ['0.0141 - 0.0168 MeV'], ['0.0152 - 0.0180 MeV'],
                   ['0.0166 - 0.0193 MeV'], ['0.0179 - 0.0206 MeV'], ['0.0193 - 0.0221 MeV'], ['0.0209 - 0.0237 MeV'], ['0.0226 - 0.0254 MeV'], ['0.0245 - 0.0274 MeV'], ['0.0265 - 0.0295 MeV'],
                   ['0.0287 - 0.0317 MeV'], ['0.0310 - 0.0341 MeV'], ['0.0335 - 0.0366 MeV'], ['0.0362 - 0.0394 MeV'], ['0.0394 - 0.0425 MeV'], ['0.0425 - 0.0459 MeV'], ['0.0459 - 0.0498 MeV'],
                   ['0.0498 - 0.0539 MeV'], ['0.0539 - 0.0583 MeV'], ['0.0583 - 0.0629 MeV'], ['0.0629 - 0.0680 MeV']]
    energies_48 = [['0.0057 - 0.0090 MeV'], ['0.0060 - 0.0091 MeV'], ['0.0062 - 0.0092 MeV'], ['0.0065 - 0.0094 MeV'], ['0.0069 - 0.0096 MeV'], ['0.0071 - 0.0098 MeV'], ['0.0074 - 0.0101 MeV'],
                   ['0.0078 - 0.0105 MeV'], ['0.0083 - 0.0109 MeV'], ['0.0086 - 0.0112 MeV'], ['0.0097 - 0.0128 MeV'], ['0.0115 - 0.0141 MeV'], ['0.0122 - 0.0148 MeV'], ['0.0127 - 0.0153 MeV'],
                   ['0.0135 - 0.0163 MeV'], ['0.0143 - 0.0171 MeV'], ['0.0149 - 0.0177 MeV'], ['0.0159 - 0.0186 MeV'], ['0.0169 - 0.0195 MeV'], ['0.0176 - 0.0202 MeV'], ['0.0186 - 0.0213 MeV'],
                   ['0.0198 - 0.0224 MeV'], ['0.0209 - 0.0237 MeV'], ['0.0223 - 0.0248 MeV'], ['0.0231 - 0.0257 MeV'], ['0.0245 - 0.0274 MeV'], ['0.0262 - 0.0288 MeV'], ['0.0272 - 0.0298 MeV'],
                   ['0.0287 - 0.0317 MeV'], ['0.0306 - 0.0332 MeV'], ['0.0318 - 0.0344 MeV'], ['0.0335 - 0.0366 MeV'], ['0.0358 - 0.0384 MeV'], ['0.0377 - 0.0411 MeV'], ['0.0404 - 0.0431 MeV'],
                   ['0.0420 - 0.0447 MeV'], ['0.0440 - 0.0478 MeV'], ['0.0473 - 0.0502 MeV'], ['0.0494 - 0.0522 MeV'], ['0.0518 - 0.0560 MeV'], ['0.0556 - 0.0586 MeV'], ['0.0579 - 0.0609 MeV'],
                   ['0.0605 - 0.0655 MeV'], ['0.0651 - 0.0683 MeV'], ['0.0680 - 0.0738 MeV'], ['0.0736 - 0.0771 MeV'], ['0.0767 - 0.0802 MeV'], ['0.0799 - 0.0865 MeV']]
    
    first_EPD_can = True
    first_con_tool = True
    first_con = True
    first_EPD = True
    first_flare = True
    panels = 4 # How many rows our graphic gets
    
    step_long = False # checking if we have a long step Dataframe
    
    if len(df.columns) > 40:
        step_long = True
        panels = 5
    
    '''
    # used to plot only fraction of data
    df = df['2022-01-29 18:00:00':'2022-01-30 06:00:00']
    df_mean = df_mean['2021-04-19 18:00:00':'2021-04-20 04:00:00']
    df_std = df_std['2021-04-19 18:00:00':'2021-04-20 04:00:00']
    '''
    
    plt.clf()
    
    plt.rcParams["figure.figsize"] = (20, 9)
    
    fig, axs = plt.subplots(panels, sharex = False)
    plt.subplots_adjust(hspace = 0)
    
    if (step_long):
        offset = [0, offset[0], offset[15], offset[31], offset[47]]
    else:
        offset = [0, offset[0], offset[15], offset[31]]
    
    # Selecting and renaming the columns
    if (step_long):
        df_temp = df[['Electron_Avg_Flux_0', 'Electron_Avg_Flux_0', 'Electron_Avg_Flux_15', 'Electron_Avg_Flux_31', 'Electron_Avg_Flux_47']]
        df_temp.columns = ['_Flare', 'STEP Channel 0', 'STEP Channel 15', 'STEP Channel 31', 'STEP Channel 47']
    else:
        df_temp = df[['Electron_Avg_Flux_0', 'Electron_Avg_Flux_0', 'Electron_Avg_Flux_15', 'Electron_Avg_Flux_31']]
        df_temp.columns = ['_Flare', 'STEP Channel 0', 'STEP Channel 15', 'STEP Channel 31']
        
    df_temp.loc[:, '_Flare'] = np.nan # no data will be plotted but the datetime x-axis remains
    
    cols = ['0', '15', '31', '47']

    df_temp[['_Flare']].plot(color = '#000000', ax = axs[0])
    
    # Plotting the step data
    for i in range(panels - 1):
        df_temp[['STEP Channel ' + cols[i]]].plot(logy = True, color = '#000000', ax = axs[i + 1])
    
    # overwriting df_temp with std
    if (step_long):
        df_temp = df_std[['Mean+' + str(sigma_factor) + 'Sigma_Flux_0', 'Mean+' + str(sigma_factor) + 'Sigma_Flux_15', 'Mean+' + str(sigma_factor) + 'Sigma_Flux_31', 'Mean+' + str(sigma_factor) + 'Sigma_Flux_47']]
        df_temp.columns = ['Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 0) ' + str(energies_48[0]),
                           'Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 15) ' + str(energies_48[15]),
                           'Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 31) ' + str(energies_48[31]),
                           'Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 47) ' + str(energies_48[47])]
    else:
        df_temp = df_std[['Mean+' + str(sigma_factor) + 'Sigma_Flux_1', 'Mean+' + str(sigma_factor) + 'Sigma_Flux_15', 'Mean+' + str(sigma_factor) + 'Sigma_Flux_31']]
        df_temp.columns = ['Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 0)' + str(energies_32[0]),
                           'Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 15)' + str(energies_32[15]),
                           'Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 31)' + str(energies_32[31])]

    # compute mean + x * Sigma and plot it.
    df_temp *= sigma_factor
    
    for i in range(panels - 1):
        df_temp.loc[:, df_temp[[df_temp.columns[i]]].columns[0]] += df_mean[['Mean_Flux_' + cols[i]]][df_mean[['Mean_Flux_' + cols[i]]].columns[0]]
        df_temp[[df_temp.columns[i]]].plot(color = 'g', ax = axs[i + 1])
        
    plt.setp(axs[0], yticks=[])
        
    for i in all_flare_utc:
        if first_flare:
            axs[0].axvline(i, color = '#000000', label = 'flare')
            first_flare = False
        else:
            axs[0].axvline(i, color = '#000000')

    # plot mag con tool connected flares
    for flare_utc in connected_flares_peak_utc:
        if first_con_tool:
            axs[0].axvline(flare_utc, color = 'orange', label = 'candidate (connectivity tool)')
            first_con_tool = False
        else:
            axs[0].axvline(flare_utc, color = 'orange')
    
    # plot epd connected flares
    for flare_utc in epd_connected_flares_peak_utc:
        for j in range(1, panels):
            if first_EPD_can and j == 1:
                axs[j].axvline(flare_utc, color = 'b', label = 'temporal coincidence with electron event')
                first_EPD_can = False
            else:
                axs[j].axvline(flare_utc, color = 'b')
        
    for i in misc.intersection(epd_connected_flares_peak_utc, connected_flares_peak_utc):
        for j in range(1, panels):
            if first_con and j == 1:
                axs[j].axvline(i, color = 'r', label = 'connected flare-electron event')
                first_con = False
            else:
                axs[j].axvline(i, color = 'r')
    
    # plotting the timespans where we detect an event in the epd data
    for i in events_epd_utc:
        for j in range(1, panels):
            bin_offset = int(offset[j]) * config.TIME_RESOLUTION
            if first_EPD and j == 0:
                axs[j].axvspan(i[0] + datetime.timedelta(0, bin_offset), i[1] + datetime.timedelta(0, bin_offset), color = 'b', alpha = 0.2, label = 'electron event')
                first_EPD = False
            else:
                axs[j].axvspan(i[0] + datetime.timedelta(0, bin_offset), i[1] + datetime.timedelta(0, bin_offset), color = 'b', alpha = 0.2)
    
    axs[0].xaxis.tick_top()
    
    # plot legend of graphs
    for i in range(panels):
        axs[i].legend()
        if i != 0:
            axs[i].secondary_yaxis('right')
        if i != 0 and i != panels - 1:
            axs[i].get_xaxis().set_visible(False)
    
    # save graphs as one plot to add axis labels
    fig.add_subplot(111, frameon = False)
    
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    
    # add axis labels
    plt.ylabel('electron intensity [' + r"$(cm^2 \ s \ sr \ MeV)^{-1}$" + ']', fontsize = 20)
    plt.xlabel('time', fontsize = 20)
    
    return plt


def create_step(df_step: pd.DataFrame, flare_range: pd.DataFrame, connected_flares: pd.DataFrame):
    # For the first months a different number of energy channels is used. This detects if you are within that time.
    length = 32
    if ('Integral_Avg_Flux_47' in df_step.columns):
        length = 48

    df_step_electron, running_mean, running_std = _cleanup_sensor(df_step, length)

    # Using the precomputed parker spiral distance
    parker_dist_series = pd.read_pickle(f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance.pkl")['Parker_Spiral_Distance']

    df_offset_step, offset = _calculate_delays(flare_range, length, parker_dist_series, df_step_electron)

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

    epd_connected_flares_peak_utc = _find_electron_events_flare(flare_range, length, parker_dist_series, events)

    return _plot_step_data(df_step_electron, 
                     running_mean, 
                     running_std, 
                     sigma_factor, 
                     offset, connected_flares["peak_UTC"].to_list(),
                     epd_connected_flares_peak_utc, events, flare_range['peak_UTC'])
    