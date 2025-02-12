'''
Collection of miscellanious functions that are used in this project

Includes following functions:
    get_epd_bins()
    parker_spiral_distance()
    compute_delay()
    sum_time()
    add_delay()
    next_date()
    previous_date()
    next_utc()
'''

import math
from solarmach import SolarMACH, print_body_list, get_sw_speed
import datetime
import pandas as pd
import numpy as np

import epd_handler

def get_epd_bins(type):
    '''
    list of energy ranges of ion/electron bins
    
    parameters:
    type: string of particle type [ion, electron]
    '''
    if type == 'ion':
        return [['0.0495 - 0.0574 MeV'], ['0.0520 - 0.0602 MeV'], ['0.0552 - 0.0627 MeV'], ['0.0578 - 0.0651 MeV'], ['0.0608 - 0.0678 MeV'], ['0.0645 - 0.0718 MeV'], ['0.0689 - 0.0758 MeV'], ['0.0729 - 0.0798 MeV'],
                ['0.0768 - 0.0834 MeV'], ['0.0809 - 0.0870 MeV'], ['0.0870 - 0.0913 MeV'], ['0.0913 - 0.0974 MeV'], ['0.0974 - 0.1034 MeV'], ['0.1034 - 0.1096 MeV'], ['0.1096 - 0.1173 MeV'], ['0.1173 - 0.1246 MeV'],
                ['0.1246 - 0.1333 MeV'], ['0.1333 - 0.1419 MeV'], ['0.1419 - 0.1514 MeV'], ['0.1514 - 0.1628 MeV'], ['0.1628 - 0.1744 MeV'], ['0.1744 - 0.1879 MeV'], ['0.1879 - 0.2033 MeV'], ['0.2033 - 0.2189 MeV'],
                ['0.2189 - 0.2364 MeV'], ['0.2364 - 0.2549 MeV'], ['0.2549 - 0.2744 MeV'], ['0.2744 - 0.2980 MeV'], ['0.2980 - 0.3216 MeV'], ['0.3216 - 0.3494 MeV'], ['0.3494 - 0.3810 MeV'], ['0.3810 - 0.4117 MeV'],
                ['0.4117 - 0.4472 MeV'], ['0.4472 - 0.4850 MeV'], ['0.4850 - 0.5255 MeV'], ['0.5255 - 0.5734 MeV'], ['0.5734 - 0.6216 MeV'], ['0.6216 - 0.6767 MeV'], ['0.6767 - 0.7401 MeV'], ['0.7401 - 0.8037 MeV'],
                ['0.8037 - 0.8752 MeV'], ['0.8752 - 0.9500 MeV'], ['0.9500 - 1.0342 MeV'], ['1.0342 - 1.1294 MeV'], ['1.1294 - 1.2258 MeV'], ['1.2258 - 1.3376 MeV'], ['1.3376 - 1.4641 MeV'], ['1.4641 - 1.5934 MeV'],
                ['1.5934 - 1.7372 MeV'], ['1.7372 - 1.8867 MeV'], ['1.8867 - 2.0537 MeV'], ['2.0537 - 2.2479 MeV'], ['2.2479 - 2.4375 MeV'], ['2.4375 - 2.6602 MeV'], ['2.6602 - 2.9209 MeV'], ['2.9209 - 3.1725 MeV'],
                ['3.1725 - 3.4609 MeV'], ['3.4609 - 3.7620 MeV'], ['3.7620 - 4.0993 MeV'], ['4.0993 - 4.4821 MeV'], ['4.4821 - 4.8701 MeV'], ['4.8701 - 5.3147 MeV'], ['5.3147 - 5.8322 MeV'], ['5.8322 - 6.1316 MeV']]
    
    if type == 'electron':
        return [['0.0312 - 0.0354 MeV'], ['0.0334 - 0.0374 MeV'], ['0.0356 - 0.0396 MeV'], ['0.0382 - 0.0420 MeV'], ['0.0408 - 0.0439 MeV'], ['0.0439 - 0.0467 MeV'], ['0.0467 - 0.0505 MeV'],
                ['0.0505 - 0.0542 MeV'], ['0.0542 - 0.0588 MeV'], ['0.0588 - 0.0635 MeV'], ['0.0635 - 0.0682 MeV'], ['0.0682 - 0.0739 MeV'], ['0.0739 - 0.0798 MeV'], ['0.0798 - 0.0866 MeV'],
                ['0.0866 - 0.0942 MeV'], ['0.0942 - 0.1021 MeV'], ['0.1021 - 0.1107 MeV'], ['0.1107 - 0.1207 MeV'], ['0.1207 - 0.1314 MeV'], ['0.1314 - 0.1432 MeV'], ['0.1432 - 0.1552 MeV'],
                ['0.1552 - 0.1690 MeV'], ['0.1690 - 0.1849 MeV'], ['0.1849 - 0.2004 MeV'], ['0.2004 - 0.2182 MeV'], ['0.2182 - 0.2379 MeV'], ['0.2379 - 0.2590 MeV'], ['0.2590 - 0.2826 MeV'],
                ['0.2826 - 0.3067 MeV'], ['0.3067 - 0.3356 MeV'], ['0.3356 - 0.3669 MeV'], ['0.3669 - 0.3993 MeV'], ['0.3993 - 0.4352 MeV'], ['0.4353 - 0.4742 MeV']]
        
    return 'Invalid particle type'

def parker_spiral_distance(timestamp):
    '''
    Approximating the distance the particles have to travel until reaching SOLO
    This is done using data from the SolarMACH tool
    
    Parameters:
    utc: string of time
    '''
    utc = str(timestamp)[0:10] + ' ' + str(timestamp)[11:19]
    body_list = ['Solar Orbiter']
    df = SolarMACH(utc, body_list).coord_table
    
    mag_footpoint_lon = df['Magnetic footpoint longitude (Carrington)'][0]
    heliocentric_dist = df['Heliocentric distance (AU)'][0]
    sw_speed = df['Vsw'][0]
    solo_lon = df['Carrington longitude (°)'][0]
    solo_lat = df['Carrington latitude (°)'][0]
    
    r = 150e9 * heliocentric_dist
    theta = ((mag_footpoint_lon - solo_lon) % 360) * math.pi / 180
    
    return r / (2 * theta) * (theta * math.sqrt(1 + theta**2) + math.log(theta + math.sqrt(1 + theta**2)))

def mag_footpoint_lonitude(timestamp):
    utc = str(timestamp)[0:10] + ' ' + str(timestamp)[11:19]    
    body_list = ['Solar Orbiter']
    df = SolarMACH(utc, body_list).coord_table
    
    return df['Magnetic footpoint longitude (Carrington)'][0]
    
def add_delay(particle_type, id, timestamp, indirect_factor, solo_dist):
    '''
    Adds time delay of arriving particles accurately to the second to given timestamp.
    This precision is not actually needed (minutes would be accurate enough)
    
    parameters:
    bin:            int number of energy bin from epd
    id:             int flare id
    particle_type:  string of type of particle ['ion', 'electron']
    utc:            string of peak_UTC of flare
    
    # TODO: maybe vectorize computations
    '''
    
    # load file with list of Parker Spiral distances at the time of each flare
    dist = pd.read_pickle("SolarMACH/parker_spiral_distance.pkl")['Parker_Spiral_Distance'][id]
         
    n_bins = 0
    if particle_type == 'ion':
        n_bins = 64
    if particle_type == 'electron':
        n_bins = 34
        
    v = epd_handler.compute_particle_speed(n_bins, particle_type)
    
    delayed_timestamp = []
    for i in range(n_bins):
        dt = dist / v[i] - solo_dist * 150e9 / 299792458
        delay_direct = timestamp + datetime.timedelta(0, math.floor(dt))
        delay_indirect = timestamp + datetime.timedelta(0, math.floor(dt * indirect_factor))
        
        delayed_timestamp.append([delay_direct, delay_indirect])
    
    return delayed_timestamp

def next_date(current_date):
    '''
    Computes next date depending on current date. This takes into account that months do not all have the same amount of days and includes leap years.
    
    parameters:
    current_date: string of current date (yyyy-mm-dd)
    '''
    current = datetime.datetime.strptime(current_date, "%Y-%m-%d").date()
    current += datetime.timedelta(days=1)
    
    return str(current)

def previous_date(current_date):
    '''
    Computes previous date depending on current date. This takes into account that months do not all have the same amount of days and includes leap years.
    
    parameters:
    current_date: string of current date (yyyy-mm-dd)
    '''
    current = datetime.datetime.strptime(current_date, "%Y-%m-%d").date()
    current -= datetime.timedelta(days=1)
    
    return str(current)
    
def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def utc_to_datetime(utc):
    return datetime.datetime.strptime(utc[2:10] + " " + utc[11:19], "%y-%m-%d %H:%M:%S")

def step_delay(date, length):
    energies_32 = [0.0090, 0.0091, 0.0094, 0.0098, 0.0102, 0.0108, 0.0114, 0.0121, 0.0129, 0.0137, 0.0146, 0.0157, 0.0168, 0.0180, 0.0193, 0.0206,
                0.0221, 0.0237, 0.0254, 0.0274, 0.0295, 0.0317, 0.0341, 0.0366, 0.0394, 0.0425, 0.0459, 0.0498, 0.0539, 0.0583, 0.0629, 0.0680]
    energies_48 = [0.0090, 0.0091, 0.0092, 0.0094, 0.0096, 0.0098, 0.0101, 0.0105, 0.0109, 0.0112, 0.0128, 0.0141, 0.0148, 0.0153, 0.0163, 0.0171,
                0.0177, 0.0186, 0.0195, 0.0202, 0.0213, 0.0224, 0.0237, 0.0248, 0.0257, 0.0274, 0.0288, 0.0298, 0.0317, 0.0332, 0.0344, 0.0366,
                0.0384, 0.0411, 0.0431, 0.0447, 0.0478, 0.0502, 0.0522, 0.0560, 0.0586, 0.0609, 0.0655, 0.0683, 0.0738, 0.0771, 0.0802, 0.0865]

    dist = parker_spiral_distance(datetime.datetime.strptime(date[2:10] + " 00:00:00", "%y-%m-%d %H:%M:%S"))

    c = 299792458 # [m/s] speed of light
    m = 9.1093837015e-31
        
    KE = np.empty(length)

    if length == 32:
        for i in range(length):
            KE[i] = energies_32[i] * 1.60218e-13 # get energy from bins in [MeV] and convert to Joules [J]
    else:
        for i in range(length):
            KE[i] = energies_48[i] * 1.60218e-13 # get energy from bins in [MeV] and convert to Joules [J]

    v = np.sqrt(1 - (1 / (KE / (m * c**2) + 1)**2)) * c  # relativistic formula for kinetic energy

    dt = []
    for i in range(length):
        dt.append(dist / v[i])
    
    return dt


def parse_date_list(utc_times: list[str]):
    return [datetime.datetime.fromisoformat(utc_time) for utc_time in utc_times]