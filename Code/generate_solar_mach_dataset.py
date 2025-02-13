import pandas as pd

import stix_handler
import misc_handler
import config

# read STIX flare list and extract coordinates of the origin
stix_flares = stix_handler.read_list()

df = pd.DataFrame(index = range(len(stix_flares)), columns = ['Parker_Spiral_Distance'])

dest = f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance.pkl"

dest_temp = f"{config.CACHE_DIR}/SolarMACH/parker_spiral_distance_temp.pkl"
start = 0 # change this variable you want to append new data without doing everything again e.g. in case of a crash in the process

if start != 0:
    df = pd.read_pickle(dest_temp)

for i in stix_flares.index[start:]:
    if i % 100 == 0:
        df.to_pickle(dest_temp)
        
        print("--------------------------------------------------------------")
        print("Done until", i)
        print("--------------------------------------------------------------")
    
    timestamp = stix_flares['peak_UTC'][i]
    print("working on", timestamp[0:10], timestamp[11:16])
    df['Parker_Spiral_Distance'][i] = misc_handler.parker_spiral_distance(timestamp)

df.to_pickle(dest)