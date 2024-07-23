'''
manually download data from connectivity tool with:
http://connect-tool.irap.omp.eu/api/SOLO/ADAPT/PARKER/SCTIME/yyyy-mm-dd/hhmmss

where the timestamp can only be [000000, 060000, 120000, 180000] as the measurements are done 4 times per day.
'''

import pandas as pd
import zipfile
import time
import webbrowser
import os
import math
import numpy as np

import misc_handler
import stix_handler
import plots
import goes_classification

def get_download_link(utc):
    '''
    returns download link for given timestep as a string
    '''
    return 'http://connect-tool.irap.omp.eu/api/SOLO/ADAPT/PARKER/SCTIME/' + utc[0:4] + '-' + utc[5:7] + '-' + utc[8:10] + '/' + utc[11:13] + '0000'

def read_data(utc):
    '''
    reads data from connectivity tool database
    
    if files are not already downloaded, it will automatically do that
        -> this will open a new browser window
    '''
    timestamp = utc[0:4] + utc[5:7] + utc[8:13] + '0000'
    filename = 'connectivity_tool_downloads/SOLO_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_' + timestamp + '_fileconnectivity.ascii'
    
    if not os.path.isfile(filename):
        utc_start = utc[0:4] + '-' + utc[5:7] + '-' + utc[8:10] + '/' + utc[11:13] + '0000'
        download_files(utc_start, misc_handler.next_utc(utc_start)) # as only next file is needed in this case
    
    raw_data = open(filename, 'r')
    
    # generate empty dataframe with columns: [i, density(%), R(m), CRLT(degrees), CRLN(degrees), DIST(m), HPLT(degrees), HPLN(degrees)]
    df = pd.DataFrame({"SSW/FSW/M" : pd.Series(dtype = 'string'),
                       "density" : pd.Series(dtype = 'float'),
                       "R" : pd.Series(dtype = 'float'),
                       "CRLT" : pd.Series(dtype = 'float'),
                       "CRLN" : pd.Series(dtype = 'float'),
                       "DIST" : pd.Series(dtype = 'float'),
                       "HPLT" : pd.Series(dtype = 'float'),
                       "HPLN" : pd.Series(dtype = 'float')})
    
    i = 1
    for line in raw_data:
        if (i >= 21):
            line = line.strip()
            columns = line.split()
            new_row = pd.DataFrame({"SSW/FSW/M" : [str(columns[0])],
                                    "density" : [float(columns[2])],
                                    "R" : [float(columns[3])],
                                    "CRLT" : [float(columns[4])],
                                    "CRLN" : [float(columns[5])],
                                    "DIST" : [float(columns[6])],
                                    "HPLT" : [float(columns[7])],
                                    "HPLN" : [float(columns[8])]})
            
            df = pd.concat([df, new_row], ignore_index = True)
        i += 1

    return df

def separation(data, epsilon):
    '''
    Separate possible connection points into groups with at most epsilon degrees of distance between each other
    
    parameters:
    data:       pandas dataframe with information on flares
    epsilon:    value (in degrees) of distance for separation
    '''
    groups = []
    temp = 0
    
    for type in data['SSW/FSW/M'].unique():
        # split data according to type
        data_type = data[data['SSW/FSW/M'] == type]
        
        to_add = list(range(temp, temp + len(data_type.index)))
        temp += len(data_type.index)
        
        new_group = []
        
        while(len(to_add) != 0):
            for i in to_add:
                new_element_added = False
                # First element of the group has to be in a new group
                if(len(new_group) == 0):
                    new_group = [i]
                    to_add.remove(i)
                else:
                    for j in new_group:
                        # account for wrap around cases
                        lon_dist = min(abs(data_type['CRLN'][j] - data_type['CRLN'][i]), abs(data_type['CRLN'][j] - data_type['CRLN'][i] + 360), abs(data_type['CRLN'][j] - data_type['CRLN'][i] - 360))
                        
                        if (lon_dist ** 2 + (data_type['CRLT'][j] - data_type['CRLT'][i]) ** 2 - epsilon ** 2 <= 0):
                            new_group.append(i)
                            to_add.remove(i)
                            new_element_added = True
                            break
                if (new_element_added):
                    break
            if (new_element_added):
                continue
            
            # append group when every element is checked with current group
            groups.append(new_group)
            new_group = []
        
        # add last group when every element is added 
        if len(new_group) != 0:
            groups.append(new_group)
            
    return groups

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

def download_files(utc, end_date, download_all = False):
    '''
    Automatically download connectivity tool data and unzip the downloaded folders. Then copy the needed files into correct directory and delete unnecessary files.

    !!! As this script opens a new tab for each download, one should not download more than a month of data at a time !!!

    TODO: Add way to close opened tabs after successful download
    '''

    download_dir = '/mnt/c/Users/Fabian Kistler/Downloads'
    directory_to_extract_to = 'connectivity_tool_downloads'

    while utc != end_date:
        folder_name = 'SOLO_PARKER_PFSS_SCTIME_ADAPT_SCIENCE_' + utc[0:4] + utc[5:7] + utc[8:10] + 'T' + utc[11:13] + '0000'
        path = 'connectivity_tool_downloads/' + folder_name + '_fileconnectivity.ascii'
        if not os.path.isfile(path) or download_all:
            URL = get_download_link(utc)
            webbrowser.open(URL) # Open download link to start automated download of zip folder
            
            path = download_dir + '/' + folder_name + '.zip'
            
            while not os.path.isfile(path):
                time.sleep(1) # give the download some time...
            
            with zipfile.ZipFile(path, 'r') as zip_ref:
                zip_ref.extractall(directory_to_extract_to)
                
            for ending in ['_backgroundwl.png', '_filear.json', '_fileevent.ascii', '_filefieldline.ascii', '_filehcs.ascii', '_fileparam.yml', '_finallegendwl.png', '_filefp.ascii',
                           '_finalnolegendmag.png', '_finalnolegendwl.png', '_layerar.png', '_layercme.png', '_layerconnectivity.png', '_layercoronalhole.png', '_layerflare.png',
                           '_layerframe.png', '_layerhcs.png', '_layersubpoint.png', '_layerxflare.png', '_finalnolegendeuv171.png', '_finalnolegendeuv193.png', '_finalnolegendeuv304.png',
                           '_finallegendeuv171.png', '_finallegendeuv193.png', '_finallegendeuv304.png', '_backgroundeui174.png', '_backgroundeui304.png']:
                path_files = 'connectivity_tool_downloads/' + folder_name + ending
                if os.path.isfile(path_files):
                    os.remove(path_files)

            if os.path.isfile(path):
                os.remove(path)
            
        utc = misc_handler.next_utc(utc)
    
    return

def find_connected_flares(stix_flares, flare_start_id, flare_end_id, epsilon, delta, opt_output, plot_non_connected):
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
        # get coordinates of flare
        flare_lon = stix_flares['hgc_lon'][flare_id]
        flare_lat = stix_flares['hgc_lat'][flare_id]
        
        # compute estimated GOES flux & class
        counts = stix_flares['4-10 keV'][flare_id] - stix_flares['bkg 4-10 keV'][flare_id]
        
        dist = stix_flares['solo_position_AU_distance'][flare_id]
        scale = dist**2
        
        goes_flux = goes_classification.compute_goes_flux(counts * scale / 4) # STIX list has counts over 4s in it
        
        if not stix_flares['att_in'][flare_id]:
            classification = goes_classification.get_goes_classification(goes_flux)
        else:
            att_flux = goes_flux
            goes_flux = 10**-3.5

        if opt_output:
            print("flare location (lon, lat) = " + str(flare_lon) + ", " + str(flare_lat) + "\n")

        # get the closest timestamp that correlates to the times where the connectivity tool computes its data
        # [00:00, 06:00, 12:00, 18:00] in utc format respectively
        closest_timestamp = stix_handler.closest_timestamp(stix_flares['peak_UTC'][flare_id])

        # get connectivity tool data from downloaded files
        con_tool_data = read_data(closest_timestamp)

        if opt_output:
            print("Connection tool data:")
            print(con_tool_data.drop(['R', 'DIST', 'HPLT', 'HPLN'], axis = 1))

        '''
        # build groups and compute its center with a defined metric
        # TODO: define metric that accuratly represents possibly connected points/regions
        groups = separation(con_tool_data.drop(['density', 'R', 'DIST', 'HPLT', 'HPLN'], axis = 1), epsilon)
        center_data = find_center(groups, con_tool_data.drop(['SSW/FSW/M', 'R', 'DIST', 'HPLT', 'HPLN'], axis = 1))

        if opt_output:
            print(center_data)
        '''
        
        connected = False
        min_dist = 360
        con_id = -1

        center_dist = 360
        center_id = -1
        
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
        
        '''
        # same check with connection groups
        # with good metric this may be mre accurate then checking each point separately
            if i in center_data.index:
                lon = center_data['CRLN'][i]
                lat = center_data['CRLT'][i]
                
                # account for wrap around cases
                lon_dist = min(abs(lon - flare_lon), abs(lon - flare_lon + 360), abs(lon - flare_lon - 360))
                dist = math.sqrt(lon_dist ** 2 + (lat - flare_lat) ** 2)
                if (dist < center_dist):
                    center_dist = dist
                    center_id = i
                if (opt_output):
                    print("Distance of flare origin to center point with id:  " + str(i) + "  is: " + str(dist))
        '''
                
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

        # Output of results
        if connected:
            plots.plot(flare_id, closest_timestamp, [flare_lon, flare_lat], connected, p = [con_tool_data['CRLN'][con_id], con_tool_data['CRLT'][con_id]])
            
            # add connected flare to list
            connected_flares.append(flare_id)
        else:
            if plot_non_connected:
                plots.plot(flare_id, closest_timestamp, [flare_lon, flare_lat], connected)
                
    plots.histogram(flare_distances, range(0, 180, 5), "Images/Hist/all_flares_distance.jpg")
    plots.histogram(connected_flare_distances, np.arange(0, math.ceil(delta), 0.2), "Images/Hist/con_tool_flares_distance.jpg")
    
    # 2-d plot
    if len(probability) != 0:
        plots.histogram_2d_density([item[2] for item in probability], [item[1] for item in probability],
                                   [np.logspace(np.log10(min([item[2] for item in probability])), np.log10(max([item[2] for item in probability]))), np.arange(0, 105, 5)], "Images/Hist/2d_density")

    # 2-d plot all
    if len(probability_all) != 0:
        plots.histogram_2d_density([item[2] for item in probability_all], [item[1] for item in probability_all],
                                   [np.logspace(np.log10(min([item[2] for item in probability_all])), np.log10(max([item[2] for item in probability_all]))), np.arange(0, 105, 5)], "Images/Hist/2d_density_all")
    
    # 2-d plot
    if len(probability_att) != 0:
        plots.histogram_2d_density([item[2] for item in probability_att], [item[1] for item in probability_att],
                                   [np.logspace(np.log10(min([item[2] for item in probability_att])), np.log10(max([item[2] for item in probability_att]))), np.arange(0, 105, 5)], "Images/Hist/2d_density_att")
    
    # 2-d plot
    if len(probability_no_att) != 0:
        plots.histogram_2d_density([item[2] for item in probability_no_att], [item[1] for item in probability_no_att],
                                   [np.logspace(np.log10(min([item[2] for item in probability_no_att])), np.log10(max([item[2] for item in probability_no_att]))), np.arange(0, 105, 5)], "Images/Hist/2d_density_no_att")
    
    # 2-d plot
    if len(probability_att_con) != 0:
        plots.histogram_2d_density([item[2] for item in probability_att_con], [item[1] for item in probability_att_con],
                                   [np.logspace(np.log10(min([item[2] for item in probability_att_con])), np.log10(max([item[2] for item in probability_att_con]))), np.arange(0, 105, 5)], "Images/Hist/2d_density_att_con")
    
    '''
    # 2-d plot
    if len(probability_M5plus) != 0:
        plots.histogram_2d_density([item[2] for item in probability_M5plus], [item[1] for item in probability_M5plus],
                                   [np.logspace(np.log10(min([item[2] for item in probability_M5plus])), np.log10(max([item[2] for item in probability_M5plus]))), np.arange(0, 105, 5)], "Images/Hist/2d_density_M5plus")
    '''
    return connected_flares, flare_distances