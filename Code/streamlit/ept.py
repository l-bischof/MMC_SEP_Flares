import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import misc
from classes import Config
import epd
import streamlit as st



def plot_epd_data(df, df_mean, df_std, sigma_factor, connected_flares_peak_utc = [], epd_connected_flares_peak_utc = [], events_epd_utc = [], all_flare_utc = []):
    '''
    plots epd data from pandas dataframe
    '''

    connected_flares_peak_utc = misc.parse_date_list(connected_flares_peak_utc)
    epd_connected_flares_peak_utc = misc.parse_date_list(epd_connected_flares_peak_utc)
    all_flare_utc = misc.parse_date_list(all_flare_utc)

    energies = [['0.0312 - 0.0354 MeV'], ['0.0334 - 0.0374 MeV'], ['0.0356 - 0.0396 MeV'], ['0.0382 - 0.0420 MeV'], ['0.0408 - 0.0439 MeV'], ['0.0439 - 0.0467 MeV'], ['0.0467 - 0.0505 MeV'],
                ['0.0505 - 0.0542 MeV'], ['0.0542 - 0.0588 MeV'], ['0.0588 - 0.0635 MeV'], ['0.0635 - 0.0682 MeV'], ['0.0682 - 0.0739 MeV'], ['0.0739 - 0.0798 MeV'], ['0.0798 - 0.0866 MeV'],
                ['0.0866 - 0.0942 MeV'], ['0.0942 - 0.1021 MeV'], ['0.1021 - 0.1107 MeV'], ['0.1107 - 0.1207 MeV'], ['0.1207 - 0.1314 MeV'], ['0.1314 - 0.1432 MeV'], ['0.1432 - 0.1552 MeV'],
                ['0.1552 - 0.1690 MeV'], ['0.1690 - 0.1849 MeV'], ['0.1849 - 0.2004 MeV'], ['0.2004 - 0.2182 MeV'], ['0.2182 - 0.2379 MeV'], ['0.2379 - 0.2590 MeV'], ['0.2590 - 0.2826 MeV'],
                ['0.2826 - 0.3067 MeV'], ['0.3067 - 0.3356 MeV'], ['0.3356 - 0.3669 MeV'], ['0.3669 - 0.3993 MeV'], ['0.3993 - 0.4352 MeV'], ['0.4353 - 0.4742 MeV']]
    
    first_EPD_can = True
    first_con_tool = True
    first_con = True
    first_EPD = True
    first_flare = True
    
    plt.clf()
    
    plt.rcParams["figure.figsize"] = (20, 9)
    
    fig, axs = plt.subplots(5, sharex = False)
    plt.subplots_adjust(hspace = 0)
    
    df_temp = df[['Electron_Flux_1', 'Electron_Flux_1', 'Electron_Flux_10', 'Electron_Flux_20','Electron_Flux_32']]
    df_temp.columns = ['_Flare', 'EPT Channel 1', 'EPT Channel 10', 'EPT Channel 20', 'EPT Channel 32']
    df_temp.loc[:, '_Flare'] = np.nan # no data will be plotted but the datetime x-axis remains
    
    cols = ['1', '10', '20', '32']

    df_temp[['_Flare']].plot(color = '#000000', ax = axs[0])
    
    for i in range(4):   
        df_temp[['EPT Channel ' + cols[i]]].plot(logy = True, color = '#000000', ax = axs[i + 1])

    # compute mean + x * Sigma and plot it.
    df_std *= sigma_factor
    for i in cols:
        df_std.loc[:, df_std[['Mean+' + str(sigma_factor) + 'Sigma_Flux_' + i]].columns[0]] += df_mean[['Mean_Flux_' + i]][df_mean[['Mean_Flux_' + i]].columns[0]]
    
    df_temp = df_std[['Mean+' + str(sigma_factor) + 'Sigma_Flux_1', 'Mean+' + str(sigma_factor) + 'Sigma_Flux_10', 'Mean+' + str(sigma_factor) + 'Sigma_Flux_20', 'Mean+' + str(sigma_factor) + 'Sigma_Flux_32']]
    df_temp.columns = ['Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 1)' + str(energies[1]),
                       'Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 10)' + str(energies[10]),
                       'Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 20)' + str(energies[20]),
                       'Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 32)' + str(energies[32])]
    
    for i in range(4):
        df_temp[[df_temp.columns[i]]].plot(color = 'g', ax = axs[i + 1])
    
    plt.setp(axs[0], yticks=[])
    
    for i in all_flare_utc:
        if first_flare:
            axs[0].axvline(i, color = '#000000', label = 'flare (STIX)')
            first_flare = False
        else:
            axs[0].axvline(i, color = '#000000')
    
    # plot mag con tool connected flares
    for flare_utc in connected_flares_peak_utc:
        if first_con_tool:
            axs[0].axvline(flare_utc, color = 'orange', label = 'candidate (MCT)')
            first_con_tool = False
        else:
            axs[0].axvline(flare_utc, color = 'orange')
    
    # plot epd connected flares
    for flare_utc in epd_connected_flares_peak_utc:
        for j in range(4):
            if first_EPD_can and j == 3:
                axs[j + 1].axvline(flare_utc, color = 'b', label = 'temporal coincidence with electron event')
                first_EPD_can = False
            else:
                axs[j + 1].axvline(flare_utc, color = 'b')
        
    for i in misc.intersection(epd_connected_flares_peak_utc, connected_flares_peak_utc):
        for j in range(4):
            if first_con and j == 3:
                axs[j + 1].axvline(i, color = 'r', label = 'connected flare-electron event')
                first_con = False
            else:
                axs[j + 1].axvline(i, color = 'r')
               
    # plotting the timespans where we detect an event in the epd data
    for i in events_epd_utc:
        for j in range(4):
            if first_EPD and j == 3:
                axs[j + 1].axvspan(i[0], i[1], color = 'b', alpha = 0.2, label = 'electron event')
                first_EPD = False
            else:
                axs[j + 1].axvspan(i[0], i[1], color = 'b', alpha = 0.2)
     
    # plot legend of graphs
    for i in range(5):
        axs[i].legend()
        if i != 0:
            axs[i].secondary_yaxis('right')
            axs[i].set_ylim(axs[i].get_ylim()[0], None)
            
    axs[0].xaxis.tick_top()
    axs[0].set_xlim(*axs[3].get_xlim())
    axs[1].get_xaxis().set_visible(False)
    axs[2].get_xaxis().set_visible(False)
    axs[3].get_xaxis().set_visible(False)
    
    axs[4].legend(loc = 'lower right')
    
    # save graphs as one plot to add axis labels
    fig.add_subplot(111, frameon = False)
    
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    
    # add axis labels
    plt.ylabel('electron intensity [' + r"$(cm^2 \ s \ sr \ MeV)^{-1}$" + ']', fontsize = 20)
    plt.xlabel('time', fontsize = 20)
    
    return plt


def create_ept(df_ept: pd.DataFrame, flare_range: pd.DataFrame, connected_flares: pd.DataFrame, _config: Config):
    # compute running averade and standard deviation
    running_mean, running_std = epd.running_average(df_ept, _config.window_length)

    print("Running averages computed...")

    # try to find events in data
    sigma_factor = _config.ept_sigma
    events = epd.find_event(df_ept, running_mean, running_std, sigma_factor)

    print("Events found...")

    # find flares that peak during epd event
    delayed_utc = []
    delayed_utc_start = []
    indirect_factor = 1.5
    for i in flare_range.index:
        utc = flare_range['peak_UTC'][i]
        timestamp = pd.Timestamp(utc[0:10] + " " + utc[11:19])
        
        # Timestamp of the flare peak
        delayed_utc.append(misc.add_delay('electron', i, timestamp, indirect_factor, flare_range['solo_position_AU_distance'][i]))
        
        # Timestamp of the flare start
        utc_start = flare_range['start_UTC'][i]
        timestamp = pd.Timestamp(utc_start[0:10] + " " + utc_start[11:19])
        
        delayed_utc_start.append(misc.add_delay('electron', i, timestamp, indirect_factor, flare_range['solo_position_AU_distance'][i]))
        
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
                    epd_connected_flares.append(flare_range.index[0] + count)
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
        epd_connected_flares_peak_utc.append(flare_range['peak_UTC'][i])

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

    return plot_epd_data(df_ept, running_mean, running_std, sigma_factor, connected_flares["peak_UTC"].to_list(),
                        epd_connected_flares_peak_utc, events, flare_range['peak_UTC'])