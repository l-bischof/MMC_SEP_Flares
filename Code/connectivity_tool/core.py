'''
manually download data from connectivity tool with:
http://connect-tool.irap.omp.eu/api/SOLO/ADAPT/PARKER/SCTIME/yyyy-mm-dd/hhmmss

where the timestamp can only be [000000, 060000, 120000, 180000] as the measurements are done 4 times per day.
'''
from .downloader import download_files

import pandas as pd
import os
import math
import numpy as np
from datetime import datetime, timedelta
import functools

import config
import stix
import plots
from .goes import compute_goes_flux, get_goes_classification

@functools.cache
def read_data(utc):
    '''
    reads data from connectivity tool database
    
    if files are not already downloaded, it will automatically do that
        -> this will open a new browser window
    '''
    timestamp = utc[0:4] + utc[5:7] + utc[8:13] + '0000'
    filename = f'{config.CACHE_DIR}/connectivity_tool_downloads/SOLO_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_' + timestamp + '_fileconnectivity.ascii'
    
    if not os.path.isfile(filename):
        start_date = datetime.fromisoformat(utc)
        try:
            download_files(start_date, start_date+timedelta(hours=6)) # as only next file is needed in this case
        except Exception as e:
            print(f"Download of {timestamp} failed:", repr(e))
        
    # generate empty dataframe with columns: [i, density(%), R(m), CRLT(degrees), CRLN(degrees), DIST(m), HPLT(degrees), HPLN(degrees)]
    df = pd.DataFrame({"SSW/FSW/M" : pd.Series(dtype = 'string'), # Mesurement / Slow / Fast
                       "density" : pd.Series(dtype = 'float'),  # Probability
                       "R" : pd.Series(dtype = 'float'),        # Distance of Sun (~700'000)
                       "CRLT" : pd.Series(dtype = 'float'),     # Carrington Latitude
                       "CRLN" : pd.Series(dtype = 'float'),     # Carrington Longitude
                       "DIST" : pd.Series(dtype = 'float'),     # S/C distance
                       "HPLT" : pd.Series(dtype = 'float'),     
                       "HPLN" : pd.Series(dtype = 'float')})
    
    if not os.path.isfile(filename):
        return df
    

    with open(filename, 'r') as connectivity_file:
        raw_data = connectivity_file.readlines()
    

    data = {
        "SSW/FSW/M" : [],
        "density" : [],
        "R" : [],
        "CRLT" : [],
        "CRLN" : [],
        "DIST" : [],
        "HPLT" : [],
        "HPLN" : []
    }

    for line in raw_data[20:]:
        line = line.strip()
        columns = line.split()

        data["SSW/FSW/M"].append(str(columns[0]))
        data["density"].append(float(columns[2]))
        data["R"].append(float(columns[3]))
        data["CRLT"].append(float(columns[4]))
        data["CRLN"].append(float(columns[5]))
        data["DIST"].append(float(columns[6]))
        data["HPLT"].append(float(columns[7]))
        data["HPLN"].append(float(columns[8]))

    return pd.DataFrame(data=data)


def find_center(groups, data):
    '''
    Find the weighted midpoint of each group.
    
    parameters:
    groups:     array with group indices
    data:       pandas dataframe
    '''
    coords = pd.DataFrame({"CRLN" : pd.Series(dtype = 'float'),
                           "CRLT" : pd.Series(dtype = 'float'),
                           "density" : pd.Series(dtype = 'float')})
    for i in groups:
        lon = 0
        lat = 0
        density = 0
        for j in i:
            lon += data['CRLN'][j] * data['density'][j]
            lat += data['CRLT'][j] * data['density'][j]
            density += data['density'][j]
            
        lon /= density
        lat /= density
        
        new_row = pd.DataFrame({"CRLN" : [lon], "CRLT" : [lat], "density" : [density]})
        
        coords = pd.concat([coords, new_row], ignore_index = True)
    
    return coords


def find_connected_flares(stix_flares, flare_start_id, flare_end_id, delta, opt_output, plot_non_connected):
    '''
    Function to find connected flares according to the magnetic connectivity tool.
    
    parameters:
    stix_flares:        Dataframe containing STIX flares information
    flare_start_id:     id in stix list of first flare in timeframe
    flare_end_id:       id in stix list of last flare in timeframe
    epsilon:            radius of connection points that will be grouped (degrees)
    delta:              radius of connection points that get accepted (degrees)
    opt_output:         bool if additional output should be plotted
    plot_non_connected: bool if non connected flares should generate a plot
    '''
    connected_flares = []
    flare_distances = []
    connected_flare_distances = []
    probability = []
    probability_all = []
    probability_att = []
    probability_no_att = []
    probability_M5plus = []
    probability_att_con = []

    # cycle through specified range of flares [start, end]
    for flare_id in range(flare_start_id, flare_end_id + 1):
        if (flare_end_id - flare_start_id) != 0:
            print('MCT progress:    ' + str(math.floor((flare_id - flare_start_id) / (flare_end_id - flare_start_id) * 10000) / 100) + ' %')
        
        # get coordinates of flare
        flare_lon = stix_flares['hgc_lon'][flare_id]
        flare_lat = stix_flares['hgc_lat'][flare_id]
        
        # compute estimated GOES flux & class
        counts = stix_flares['4-10 keV'][flare_id] - stix_flares['bkg 4-10 keV'][flare_id]
        
        # S/C distance
        dist = stix_flares['solo_position_AU_distance'][flare_id]
        scale = dist**2
        
        # STIX list combines 4s -> Goes flux is per second
        goes_flux = compute_goes_flux(counts * scale / 4) # STIX list has counts over 4s in it
        
        if not stix_flares['att_in'][flare_id]:
            classification = get_goes_classification(goes_flux)
        else:
            att_flux = goes_flux
            goes_flux = 10**-3.5

        if opt_output:
            print("flare location (lon, lat) = " + str(flare_lon) + ", " + str(flare_lat) + "\n")

        # get the closest timestamp that correlates to the times where the connectivity tool computes its data
        # [00:00, 06:00, 12:00, 18:00] in utc format respectively
        closest_timestamp = stix.closest_timestamp(stix_flares['peak_UTC'][flare_id])

        # get connectivity tool data from downloaded files
        con_tool_data = read_data(closest_timestamp)

        if opt_output:
            print("Connection tool data:")
            print(con_tool_data.drop(['R', 'DIST', 'HPLT', 'HPLN'], axis = 1))
        
        connected = False
        min_dist = 360
        con_id = -1
        
        flare_min_dist = 0
        con_flare_min_dist = 0

        # currently iterating over all possible connection points and compare with every one of them
        # TODO: find actual connection point and compare with it
        total_density = [0, 0, 0]
        for i in con_tool_data.index:
            lon = con_tool_data['CRLN'][i]
            lat = con_tool_data['CRLT'][i]
        
            # account for wrap around cases
            lon_dist = min(abs(lon - flare_lon), abs(lon - flare_lon + 360), abs(lon - flare_lon - 360))
            
            dist = math.sqrt(lon_dist ** 2 + (lat - flare_lat) ** 2)
            
            if (dist < min_dist):
                flare_min_dist = dist
                min_dist = dist
                if (dist ** 2 - delta ** 2 <= 0):   
                    con_id = i
                    connected = True
                    con_flare_min_dist = dist
                                       
                    if (opt_output):
                        print("Distance of flare origin to magnetically connected point with id:  " + str(i) + "  is: " + str(dist))
            
            if (dist < delta):
                if (con_tool_data['SSW/FSW/M'][con_id] == 'SSW'):
                    total_density[0] += con_tool_data['density'][con_id]
                if (con_tool_data['SSW/FSW/M'][con_id] == 'FSW'):
                    total_density[1] += con_tool_data['density'][con_id]
                if (con_tool_data['SSW/FSW/M'][con_id] == 'M'):
                    total_density[2] += con_tool_data['density'][con_id]              
                    
        probability_all.append([flare_id, max(total_density), goes_flux])
        if stix_flares['att_in'][flare_id]:
            probability_att.append([flare_id, max(total_density), att_flux])
        if (max(total_density) != 0):
            probability.append([flare_id, max(total_density), goes_flux])
            if stix_flares['att_in'][flare_id]:
                probability_att_con.append([flare_id, max(total_density), att_flux])
            else:
                probability_no_att.append([flare_id, max(total_density), goes_flux])
                if classification in ['M5', 'M6', 'M7', 'M8', 'M9']:
                    probability_M5plus.append([flare_id, max(total_density), goes_flux])
                
        if connected:
            connected_flare_distances.append(con_flare_min_dist)
        flare_distances.append(flare_min_dist)
        
        if opt_output:
            print("\n---------------------------------------------------------------------------------------------------------------------------------------------")
            if connected:
                print("The flare " + str(flare_id) +  " is magnetically connected to the Solar Orbiter.")
                print("It occured on the: " + str(stix_flares['peak_UTC'][flare_id])[:10] + " at: " + str(stix_flares['peak_UTC'][flare_id])[11:])
                print("Closest connected point with id: " + str(con_id) + " is a distance of: " + str(min_dist) + " degrees away.")
                # print("The approximate center of the magnetic connection with id: " + str(center_id) + " is a distance of: " + str(center_dist) + \
                #    " degrees away\nand is the true magnetically connected point with a probability of: " + str(center_data['density'][center_id]) + "%")
                
            else:
                print("The flare " + str(flare_id) +  " is NOT magnetically connected to the Solar Orbiter.")  

        if os.path.isfile(f"{config.CACHE_DIR}/connectivity_tool_downloads/SOLO_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_" + closest_timestamp[0:4] + closest_timestamp[5:7] + closest_timestamp[8:13] + "0000_finallegendmag.png"):   
            # Output of results
            if connected:
                plots.plot(flare_id, closest_timestamp, [flare_lon, flare_lat], connected, p = [con_tool_data['CRLN'][con_id], con_tool_data['CRLT'][con_id]])
                
                # add connected flare to list
                connected_flares.append(flare_id)
                
            else:
                if plot_non_connected:
                    plots.plot(flare_id, closest_timestamp, [flare_lon, flare_lat], connected)
                
    plots.histogram(flare_distances, range(0, 180, 5), f"{config.OUTPUT_DIR}/Images/Hist/all_flares_distance.jpg")
    plots.histogram(connected_flare_distances, np.arange(0, math.ceil(delta), 0.2), f"{config.OUTPUT_DIR}/Images/Hist/con_tool_flares_distance.jpg")
    
    # 2-d plot
    if len(probability) != 0:
        plots.histogram_2d_density([item[2] for item in probability], [item[1] for item in probability],
                                   [np.logspace(np.log10(min([item[2] for item in probability])), np.log10(max([item[2] for item in probability]))), np.arange(0, 105, 5)], f"{config.OUTPUT_DIR}/Images/Hist/2d_density")

    # 2-d plot all
    if len(probability_all) != 0:
        plots.histogram_2d_density([item[2] for item in probability_all], [item[1] for item in probability_all],
                                   [np.logspace(np.log10(min([item[2] for item in probability_all])), np.log10(max([item[2] for item in probability_all]))), np.arange(0, 105, 5)], f"{config.OUTPUT_DIR}/Images/Hist/2d_density_all")
    
    # 2-d plot
    if len(probability_att) != 0:
        plots.histogram_2d_density([item[2] for item in probability_att], [item[1] for item in probability_att],
                                   [np.logspace(np.log10(min([item[2] for item in probability_att])), np.log10(max([item[2] for item in probability_att]))), np.arange(0, 105, 5)], f"{config.OUTPUT_DIR}/Images/Hist/2d_density_att")
    
    # 2-d plot
    if len(probability_no_att) != 0:
        plots.histogram_2d_density([item[2] for item in probability_no_att], [item[1] for item in probability_no_att],
                                   [np.logspace(np.log10(min([item[2] for item in probability_no_att])), np.log10(max([item[2] for item in probability_no_att]))), np.arange(0, 105, 5)], f"{config.OUTPUT_DIR}/Images/Hist/2d_density_no_att")
    
    # 2-d plot
    if len(probability_att_con) != 0:
        plots.histogram_2d_density([item[2] for item in probability_att_con], [item[1] for item in probability_att_con],
                                   [np.logspace(np.log10(min([item[2] for item in probability_att_con])), np.log10(max([item[2] for item in probability_att_con]))), np.arange(0, 105, 5)], f"{config.OUTPUT_DIR}/Images/Hist/2d_density_att_con")
    
    return connected_flares, flare_distances