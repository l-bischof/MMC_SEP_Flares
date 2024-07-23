import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from collections import Counter
import pandas as pd
import datetime

import misc_handler

# set resolution of plot
dpi = 300
mpl.rc("savefig", dpi = dpi)

# scale points to fit on existing plot
def scale_point(p):
    x = 2.5 * p[0]
    y = 2.77 * (-p[1] + 90)
    
    return [x + 83, y + 53]

def plot(flare_id, utc, flare_loc, plot_p, p = [-1, 0]):
    '''
    Import connectivity tool image and plot connection point of flare onto it
    
    Parameters:
        int flare_id:       Id of flare, used for file name of resultion image
        string utc:         specifies which timestamp is the closest to the flare
        array flare_loc:    longitude and latitude of the flare
        bool plot_p:        True -> Flare might be connected -> plot closest connection point as well
        array p:            longitude and latitude of closest possible connection point
    '''
    fig, ax = plt.subplots()
    plt.clf()
    
    timestamp = utc[0:4] + utc[5:7] + utc[8:13] + '0000'
        
    # scale points to exact location on existing plot
    p = scale_point(p)
    flare_loc = scale_point(flare_loc)
    
    img = plt.imread("connectivity_tool_downloads/SOLO_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_" + timestamp + "_finallegendmag.png")
    plt.imshow(img)
    plt.axis('off')
    plt.plot(flare_loc[0], flare_loc[1], "oc", markersize = 3, label = 'Flare origin')  # og:shorthand for green circle
    
    # only print nearest connected point if flare is connected
    if (plot_p):
        plt.plot(p[0], p[1], "r^", markersize = 3, label = 'Closest potential connection point')
    
    plt.legend(prop = {'size': 3})
        
    fig.savefig("Images/flare_connections/con_point_" + str(flare_id) + ".jpg", bbox_inches = 'tight')
    
    plt.close()
    
    return

def plot_epd_data(df, df_mean, df_std, sigma_factor, filename = "Images/epd_data.jpg", connected_flares_peak_utc = [], epd_connected_flares_peak_utc = [], events_epd_utc = []):
    '''
    plots epd data from pandas dataframe
    '''
    energies = [['0.0312 - 0.0354 MeV'], ['0.0334 - 0.0374 MeV'], ['0.0356 - 0.0396 MeV'], ['0.0382 - 0.0420 MeV'], ['0.0408 - 0.0439 MeV'], ['0.0439 - 0.0467 MeV'], ['0.0467 - 0.0505 MeV'],
                ['0.0505 - 0.0542 MeV'], ['0.0542 - 0.0588 MeV'], ['0.0588 - 0.0635 MeV'], ['0.0635 - 0.0682 MeV'], ['0.0682 - 0.0739 MeV'], ['0.0739 - 0.0798 MeV'], ['0.0798 - 0.0866 MeV'],
                ['0.0866 - 0.0942 MeV'], ['0.0942 - 0.1021 MeV'], ['0.1021 - 0.1107 MeV'], ['0.1107 - 0.1207 MeV'], ['0.1207 - 0.1314 MeV'], ['0.1314 - 0.1432 MeV'], ['0.1432 - 0.1552 MeV'],
                ['0.1552 - 0.1690 MeV'], ['0.1690 - 0.1849 MeV'], ['0.1849 - 0.2004 MeV'], ['0.2004 - 0.2182 MeV'], ['0.2182 - 0.2379 MeV'], ['0.2379 - 0.2590 MeV'], ['0.2590 - 0.2826 MeV'],
                ['0.2826 - 0.3067 MeV'], ['0.3067 - 0.3356 MeV'], ['0.3356 - 0.3669 MeV'], ['0.3669 - 0.3993 MeV'], ['0.3993 - 0.4352 MeV'], ['0.4353 - 0.4742 MeV']]
    
    first_EPD_can = True
    first_con_tool = True
    first_con = True
    first_EPD = True
    
    plt.clf()
    
    plt.rcParams["figure.figsize"] = (20, 9)
    
    fig = plt.figure()
    
    axs = fig.add_gridspec(3, hspace = 0).subplots(sharex = True)
    
    df_temp = df[['Electron_Flux_1', 'Electron_Flux_10', 'Electron_Flux_32']]
    df_temp.columns = ['EPT Channel 1', 'EPT Channel 10', 'EPT Channel 32']

    df_temp[['EPT Channel 1']].plot(logy = True, color = '#000000', ax = axs[0])
    df_temp[['EPT Channel 10']].plot(logy = True, color = '#000000', ax = axs[1])
    df_temp[['EPT Channel 32']].plot(logy = True, color = '#000000', ax = axs[2])

    # compute mean + x * Sigma and plot it.
    df_std *= sigma_factor
    df_std.loc[:, df_std[['Mean+' + str(sigma_factor) + 'Sigma_Flux_1']].columns[0]] += df_mean[['Mean_Flux_1']][df_mean[['Mean_Flux_1']].columns[0]]
    df_std.loc[:, df_std[['Mean+' + str(sigma_factor) + 'Sigma_Flux_10']].columns[0]] += df_mean[['Mean_Flux_10']][df_mean[['Mean_Flux_10']].columns[0]]
    df_std.loc[:, df_std[['Mean+' + str(sigma_factor) + 'Sigma_Flux_32']].columns[0]] += df_mean[['Mean_Flux_32']][df_mean[['Mean_Flux_32']].columns[0]]
    
    df_temp = df_std[['Mean+' + str(sigma_factor) + 'Sigma_Flux_1', 'Mean+' + str(sigma_factor) + 'Sigma_Flux_10', 'Mean+' + str(sigma_factor) + 'Sigma_Flux_32']]
    df_temp.columns = ['Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 1)' + str(energies[1]),
                       'Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 10)' + str(energies[10]),
                       'Mean + ' + str(sigma_factor) + r"$\sigma$" + ' (Channel 32)' + str(energies[32])]
    
    df_temp[[df_temp.columns[0]]].plot(color = 'g', ax = axs[0])
    df_temp[[df_temp.columns[1]]].plot(color = 'g', ax = axs[1])
    df_temp[[df_temp.columns[2]]].plot(color = 'g', ax = axs[2])
    
    # plot mag con tool connected flares
    for flare_utc in connected_flares_peak_utc:
        for j in range(3):
            if first_con_tool and j == 2:
                axs[j].axvline(flare_utc, color = 'orange', label = 'candidate (connectivity tool)')
                first_con_tool = False
            else:
                axs[j].axvline(flare_utc, color = 'orange')
        # plt.axvline(delayed_utc, color = 'g')
        # plt.axvspan(delayed_utc, delayed_utc_indirect, color='g', alpha = 0.15)
    
    # plot epd connected flares
    for flare_utc in epd_connected_flares_peak_utc:
        for j in range(3):
            if first_EPD_can and j == 2:
                axs[j].axvline(flare_utc, color = 'b', label = 'temporal coincidence with electron event')
                first_EPD_can = False
            else:
                axs[j].axvline(flare_utc, color = 'b')
        
    for i in misc_handler.intersection(epd_connected_flares_peak_utc, connected_flares_peak_utc):
        for j in range(3):
            if first_con and j == 2:
                axs[j].axvline(i, color = 'r', label = 'connected flare-electron event')
                first_con = False
            else:
                axs[j].axvline(i, color = 'r')
    
    # plotting the timespans where we detect an event in the epd data
    for i in events_epd_utc:
        for j in range(3):
            if first_EPD and j == 2:
                axs[j].axvspan(i[0], i[1], color = 'b', alpha = 0.2, label = 'electron event')
                first_EPD = False
            else:
                axs[j].axvspan(i[0], i[1], color = 'b', alpha = 0.2)
     
    # plot legend of graphs  
    plt.legend()
    
    # save graphs as one plot to add axis labels
    fig.add_subplot(111, frameon = False)
    
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    
    # add axis labels
    plt.ylabel('electron intensity [' + r"$(cm^2 \ s \ sr \ MeV)^{-1}$" + ']', fontsize = 20)
    plt.xlabel('time', fontsize = 20)
    
    plt.savefig(filename, bbox_inches = 'tight')
    
    return

def plot_step_data(df, df_mean, df_std, sigma_factor, offset, filename = "Images/epd_data.jpg", connected_flares_peak_utc = [], epd_connected_flares_peak_utc = [], events_epd_utc = []):
    '''
    plots epd data from pandas dataframe
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
    panels = 3
    
    step_long = False
    
    if len(df.columns) > 40:
        step_long = True
        panels = 4
    
    plt.clf()
    
    plt.rcParams["figure.figsize"] = (20, 9)
    
    fig = plt.figure()
    
    if (step_long):
        axs = fig.add_gridspec(4, hspace = 0).subplots(sharex = True)
        offset = [offset[0], offset[15], offset[31], offset[47]]
    else:
        axs = fig.add_gridspec(3, hspace = 0).subplots(sharex = True)
        offset = [offset[0], offset[15], offset[31]]
        
    if (step_long):
        df_temp = df[['Electron_Avg_Flux_0', 'Electron_Avg_Flux_15', 'Electron_Avg_Flux_31', 'Electron_Avg_Flux_47']]
        df_temp.columns = ['STEP Channel 0', 'STEP Channel 15', 'STEP Channel 31', 'STEP Channel 47']
    else:
        df_temp = df[['Electron_Avg_Flux_0', 'Electron_Avg_Flux_15', 'Electron_Avg_Flux_31']]
        df_temp.columns = ['STEP Channel 0', 'STEP Channel 15', 'STEP Channel 31']

    df_temp[['STEP Channel 0']].plot(logy = True, color = '#000000', ax = axs[0])
    df_temp[['STEP Channel 15']].plot(logy = True, color = '#000000', ax = axs[1])
    df_temp[['STEP Channel 31']].plot(logy = True, color = '#000000', ax = axs[2])
    if (step_long):
        df_temp[['STEP Channel 47']].plot(logy = True, color = '#000000', ax = axs[3])
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
    df_temp.loc[:, df_temp[[df_temp.columns[0]]].columns[0]] += df_mean[['Mean_Flux_0']][df_mean[['Mean_Flux_0']].columns[0]]
    df_temp.loc[:, df_temp[[df_temp.columns[1]]].columns[0]] += df_mean[['Mean_Flux_15']][df_mean[['Mean_Flux_15']].columns[0]]
    df_temp.loc[:, df_temp[[df_temp.columns[2]]].columns[0]] += df_mean[['Mean_Flux_31']][df_mean[['Mean_Flux_31']].columns[0]]
    
    df_temp[[df_temp.columns[0]]].plot(color = 'g', ax = axs[0])
    df_temp[[df_temp.columns[1]]].plot(color = 'g', ax = axs[1])
    df_temp[[df_temp.columns[2]]].plot(color = 'g', ax = axs[2])
    
    if (step_long):
        df_temp.loc[:, df_temp[[df_temp.columns[3]]].columns[0]] += df_mean[['Mean_Flux_47']][df_mean[['Mean_Flux_47']].columns[0]]
        df_temp[[df_temp.columns[3]]].plot(color = 'g', ax = axs[3])
    
    # plot mag con tool connected flares
    i = 0
    for flare_utc in connected_flares_peak_utc:
        for j in range(panels):
            if first_con_tool and j == 0:
                axs[j].axvline(flare_utc, color = 'orange', label = 'candidate (connectivity tool)')
                first_con_tool = False
            else:
                axs[j].axvline(flare_utc, color = 'orange')
        i += 1
        # plt.axvline(delayed_utc, color = 'g')
        # plt.axvspan(delayed_utc, delayed_utc_indirect, color='g', alpha = 0.15)
    
    # plot epd connected flares
    for flare_utc in epd_connected_flares_peak_utc:
        for j in range(panels):
            if first_EPD_can and j == 0:
                axs[j].axvline(flare_utc, color = 'b', label = 'temporal coincidence with electron event')
                first_EPD_can = False
            else:
                axs[j].axvline(flare_utc, color = 'b')
        
    for i in misc_handler.intersection(epd_connected_flares_peak_utc, connected_flares_peak_utc):
        for j in range(panels):
            if first_con and j == 0:
                axs[j].axvline(i, color = 'r', label = 'connected flare-electron event')
                first_con = False
            else:
                axs[j].axvline(i, color = 'r')
    
    # plotting the timespans where we detect an event in the epd data
    for i in events_epd_utc:
        for j in range(panels):
            if first_EPD and j == 0:
                axs[j].axvspan(i[0] + datetime.timedelta(0, offset[j] * 300), i[1] + datetime.timedelta(0, offset[j] * 300), color = 'b', alpha = 0.2, label = 'electron event')
                first_EPD = False
            else:
                axs[j].axvspan(i[0] + datetime.timedelta(0, offset[j] * 300), i[1] + datetime.timedelta(0, offset[j] * 300), color = 'b', alpha = 0.2)
     
    # plot legend of graphs  
    plt.legend()
    
    # save graphs as one plot to add axis labels
    fig.add_subplot(111, frameon = False)
    
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    
    # add axis labels
    plt.ylabel('electron intensity [' + r"$(cm^2 \ s \ sr \ MeV)^{-1}$" + ']', fontsize = 20)
    plt.xlabel('time', fontsize = 20)
    
    plt.savefig(filename, bbox_inches = 'tight')
    
    return

def histogram(data, bins, filename = 'Images/Hist/histogram.jpg', xlabel = ''):
    '''
    Function to make a histogram. Primarily used to generate a histogram of how far from the flares origin the possible connection points are.
    
    parameters:
    data:       vector with data that should be plotted in the histogram
    filename:   string of location and name the histogram should be saved at
    '''
    plt.clf()
    
    plt.xlim(0, bins[-1] + bins[1] - bins[0]) # This should set the upper and lower limit to the range where all flares are in
    
    plt.xlabel(xlabel)
    plt.ylabel('Flares')
    
    # counts, bins = np.histogram(data)
    plt.hist(data, bins)
    
    plt.savefig(filename, bbox_inches = 'tight')
    
    return

def histogram_2d(xdata, ydata, bins, filename = 'Images/Hist/histogram.jpg'):
    plt.clf()

    hist = np.histogram2d(xdata, ydata, bins = (bins[0], bins[1]))
    Hist = hist[0].reshape(len(bins[0]) - 1, len(bins[1]) - 1)
        
    fig, ax = plt.subplots(1, 1)
    ax.set_title("")
    
    my_cmap = plt.get_cmap("jet", 1024*16)
    my_cmap.set_under('w')
    
    Cont1 = ax.pcolormesh(bins[0], bins[1], Hist.T, cmap = my_cmap, norm = mpl.colors.LogNorm(vmin = 1,vmax = max(np.ravel(hist[0]))))
    
    cb1 = fig.colorbar(Cont1)
    cb1.set_label(r"$\rm{number \ of \ cases}$")	
    ax.set_xlabel(r"$\rm{estimated \ GOES \ flux} \rm{\ [W \ m^{-2}]}$")
    ax.set_ylabel(r"$\rm{orbiter \ distance \ to \ sun} \rm{\ [AU]}$")
    
    plt.xscale('log')
    
    plt.savefig(filename, bbox_inches = 'tight')
    
def histogram_2d_density(xdata, ydata, bins, filename = 'Images/Hist/histogram.jpg'):
    plt.clf()

    hist = np.histogram2d(xdata, ydata, bins = (bins[0], bins[1]))
    Hist = hist[0].reshape(len(bins[0]) - 1, len(bins[1]) - 1)
        
    fig, ax = plt.subplots(1, 1)
    ax.set_title("")
    
    my_cmap = plt.get_cmap("jet", 1024*16)
    my_cmap.set_under('w')
    
    Cont1 = ax.pcolormesh(bins[0], bins[1], Hist.T, cmap = my_cmap, norm = mpl.colors.LogNorm(vmin = 1,vmax = max(np.ravel(hist[0]))))
    
    # cb1 = fig.colorbar(Cont1)
    # cb1.set_label(r"$\rm{number \ of \ cases}$")	
    ax.set_xlabel(r"$\rm{estimated \ GOES \ flux} \rm{\ [W \ m^-2]}$")
    ax.set_ylabel(r"$\rm{Estimated \ probability \ of \ connection} \rm{\ [\%]}$")
    
    plt.xscale('log')
    
    # plt.savefig(filename, bbox_inches = 'tight')
    
def histogram_2d_density_norm(xdata, ydata, bins, filename = 'Images/Hist/histogram.jpg'):
    plt.clf()

    hist = np.histogram2d(xdata, ydata, bins = (bins[0], bins[1]))
    
    # normalize sum of columns
    
    Hist = hist[0].reshape(len(bins[0]) - 1, len(bins[1]) - 1)
        
    fig, ax = plt.subplots(1, 1)
    ax.set_title("")
    
    my_cmap = plt.get_cmap("jet", 1024*16)
    my_cmap.set_under('w')
    
    Cont1 = ax.pcolormesh(bins[0], bins[1], Hist.T, cmap = my_cmap, norm = mpl.colors.LogNorm(vmin = 1,vmax = max(np.ravel(hist[0]))))
    
    cb1 = fig.colorbar(Cont1)
    cb1.set_label(r"$\rm{number \ of \ cases}$")	
    ax.set_xlabel(r"$\rm{estimated \ GOES \ flux} \rm{\ [W \ m^-2]}$")
    ax.set_ylabel(r"$\rm{Estimated \ probability \ of \ connection} \rm{\ [\%]}$")
    
    plt.xscale('log')
    
    plt.savefig(filename, bbox_inches = 'tight')