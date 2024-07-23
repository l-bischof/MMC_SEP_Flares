import pandas as pd

import stix_handler
import misc_handler

# read STIX flare list and extract coordinates of the origin
stix_flares = stix_handler.read_list()

df = pd.DataFrame(index = range(len(stix_flares)), columns = ['Parker_Spiral_Distance'])

dest = "SolarMACH/parker_spiral_distance.pkl"

for i in stix_flares.index:
    timestamp = stix_flares['peak_UTC'][i]
    df['Parker_Spiral_Distance'][i] = misc_handler.parker_spiral_distance(timestamp)

df.to_pickle(dest)