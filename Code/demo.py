from solarmach import SolarMACH
import math


def modified_parker_spiral_distance(time, sw_v):
    '''
    Approximating the distance the particles have to travel until reaching SOLO
    This is done using data from the SolarMACH tool
    
    Parameters:
    utc: string of time
    '''

    body_list = ['Solar Orbiter']
    df = SolarMACH(time, body_list, default_vsw=sw_v).coord_table
    
    mag_footpoint_lon = df['Magnetic footpoint longitude (Carrington)'][0]
    heliocentric_dist = df['Heliocentric distance (AU)'][0]
    solo_lon = df['Carrington longitude (°)'][0]
    
    r = 150e9 * heliocentric_dist
    theta = ((mag_footpoint_lon - solo_lon) % 360) * math.pi / 180
    
    return r / (2 * theta) * (theta * math.sqrt(1 + theta**2) + math.log(theta + math.sqrt(1 + theta**2)))


body_list = ['Solar Orbiter']
df1 = SolarMACH('2022-10-28 15:15:00', body_list).coord_table
df2 = SolarMACH('2022-10-28 15:15:00', body_list, default_vsw=800).coord_table

print('Heliocentric distance (AU)')
print(df1['Heliocentric distance (AU)'])
print(df2['Heliocentric distance (AU)'])    

print("Carrington longitude")
print(df1['Carrington longitude (°)'])
print(df2['Carrington longitude (°)'])

print("!!! Magnetic footpoint longitude (Carrington) !!!")
print(df1['Magnetic footpoint longitude (Carrington)'])
print(df2['Magnetic footpoint longitude (Carrington)'])

print("--- DIFF ---")
r1 = modified_parker_spiral_distance('2022-10-28 15:15:00', 400)
r2 = modified_parker_spiral_distance('2022-10-28 15:15:00', 800)
print(r1)
print(r2)