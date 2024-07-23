'''
This script allows for the comparison a flare in the STIX flare list with the magnetically connected points
computed by the magnetic connectivity tool (url: http://connect-tool.irap.omp.eu/)

It determines if the flares origin is within delta (to be chosen by the user) degrees of a magnetically
connected point on the sun's surface.

TODO: take into account start and end time of the flare, not just peak (which is the current state)

TODO: improve metric to classify possible connection points and account for their likelyhood

TODO: check correctness of calculations and formulation of output

If time allows:
TODO: take into account shape of AR when looking for a connection with the tool

!!! For new users it will be necessary to change some file paths and make new directories to allow the automation of downloads to work !!!
!!! This script will open browser tabs to download the magnetic connectivity tool data automatically. Google Chrome is recommended     !!!
'''

import pandas as pd
import numpy as np
import datetime

import stix_handler
import connectivity_tool
import plots
import epd_handler
import misc_handler

# --------------------------------- Input parameters ---------------------------------

# choose if additional output is requested
opt_output = False
# choose if plots for non-connected flares should be made
plot_non_connected = True
# show all events
show_all = False

# work with data and search for events within the following timespan
start_date = "2023-01-01"
end_date = "2023-01-31"

# --------------------------------------- STIX ---------------------------------------

delta = 10      # radius of connection points that get accepted (degrees)
epsilon = 10    # radius of connection points that will be grouped (degrees)

# read STIX flare list and extract coordinates of the origin
stix_flares = stix_handler.read_list()

# get range of flares that are within the defined timeframe
flare_start_id, flare_end_id = stix_handler.flares_range(start_date, end_date, stix_flares['peak_UTC'])
all_flares = range(flare_start_id, flare_end_id + 1)

# connected_flares, flare_distances = connectivity_tool.find_connected_flares(stix_flares, flare_start_id, flare_end_id, epsilon, delta, opt_output, plot_non_connected)

connected_flares = [0, 1, 2, 3, 4, 5, 40, 41, 42, 43, 44, 45, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 76, 96, 97,
    139, 172, 200, 208, 209, 246, 253, 254, 255, 256, 258, 259, 260, 263, 264, 266, 267, 268, 270, 298, 299, 300, 301, 306, 307, 308, 309, 311, 312, 313, 314, 315, 316, 317, 318,
    320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 334, 349, 350, 367, 368, 378, 422, 429, 431, 434, 435, 436, 437, 438, 439, 440, 482, 523, 524, 527, 528, 529,
    530, 531, 533, 540, 552, 553, 555, 556, 557, 558, 559, 560, 561, 562, 563, 565, 566, 567, 568, 569, 570, 571, 572, 573, 574, 585, 586, 588, 589, 600, 601, 602, 605, 607, 609,
    610, 612, 629, 636, 715, 716, 717, 718, 720, 721, 722, 723, 724, 726, 727, 728, 731, 733, 734, 736, 737, 739, 744, 765, 766, 768, 785, 786, 788, 789, 790, 792, 793, 803, 806,
    807, 810, 811, 818, 827, 828, 829, 830, 909, 915, 918, 920, 943, 1029, 1124, 1302, 1307, 1308, 1310, 1313, 1314, 1316, 1317, 1318, 1320, 1322, 1323, 1324, 1325, 1326, 1327, 1328,
    1329, 1330, 1331, 1332, 1333, 1334, 1335, 1337, 1338, 1339, 1340, 1341, 1343, 1345, 1346, 1347, 1348, 1349, 1350, 1351, 1352, 1353, 1354, 1355, 1356, 1357, 1358, 1359, 1360, 1362,
    1366, 1369, 1370, 1379, 1380, 1381, 1383, 1384, 1387, 1388, 1390, 1391, 1392, 1393, 1395, 1396, 1398, 1399, 1400, 1401, 1402, 1403, 1404, 1405, 1408, 1409, 1412, 1415, 1417, 1418,
    1419, 1420, 1422, 1424, 1425, 1426, 1427, 1428, 1430, 1432, 1434, 1435, 1436, 1437, 1438, 1439, 1440, 1442, 1444, 1445, 1446, 1447, 1448, 1450, 1457, 1463, 1521, 1550, 1551, 1555,
    1564, 1610, 1613, 1615, 1624, 1626, 1627, 1628, 1630, 1632, 1633, 1634, 1635, 1636, 1637, 1639, 1641, 1642, 1643, 1644, 1654, 1656, 1660, 1668, 1815, 1821, 1830, 1831, 1847, 1848,
    1850, 1857, 1861, 1874, 1875, 1883, 1889, 1894, 1901, 1911, 1912, 1926, 1927, 1928, 1929, 1946, 1948, 1951, 1955, 2027, 2042, 2073, 2130, 2132, 2133, 2137, 2159, 2163, 2175, 2177,
    2223, 2230, 2231, 2232, 2233, 2241, 2253, 2254, 2255, 2285, 2286, 2288, 2300, 2309, 2310, 2311, 2312, 2313, 2314, 2315, 2316, 2317, 2318, 2319, 2320, 2321, 2322, 2323, 2324, 2325,
    2327, 2328, 2329, 2331, 2332, 2333, 2335, 2336, 2337, 2338, 2339, 2340, 2341, 2346, 2347, 2348, 2350, 2351, 2352, 2353, 2358, 2359, 2360, 2363, 2364, 2367, 2369, 2372, 2381, 2402,
    2404, 2473, 2474, 2475, 2476, 2479, 2481, 2482, 2484, 2485, 2486, 2487, 2488, 2489, 2490, 2491, 2492, 2493, 2494, 2501, 2531, 2532, 2533, 2606, 2610, 2628, 2632, 2641, 2644, 2654,
    2659, 2668, 2774, 2852, 2853, 2854, 2855, 2856, 2857, 2858, 2859, 2860, 2861, 2862, 2864, 2865, 2866, 2867, 2868, 2869, 2871, 2872, 2874, 2877, 2878, 2879, 2880, 2882, 2885, 2888,
    2889, 2890, 2897, 2919, 2920, 2928, 2941, 2943, 2954, 2955, 2956, 2971, 2979, 2983, 3026, 3027, 3033, 3035, 3037, 3038, 3039, 3040, 3041, 3042, 3043, 3044, 3045, 3047, 3053, 3054,
    3058, 3063, 3073, 3078, 3083, 3084, 3085, 3088, 3091, 3098, 3101, 3102, 3103, 3106, 3109, 3114, 3117, 3118, 3124, 3125, 3127, 3128, 3129, 3130, 3131, 3132, 3133, 3134, 3135, 3137,
    3138, 3140, 3143, 3145, 3148, 3149, 3154, 3158, 3159, 3164, 3165, 3167, 3168, 3170, 3171, 3172, 3173, 3175, 3176, 3178, 3179, 3180, 3184, 3185, 3189, 3200, 3201, 3207, 3209, 3212,
    3213, 3220, 3224, 3227, 3228, 3229, 3235, 3244, 3246, 3247, 3249, 3251, 3258, 3259, 3260, 3261, 3262, 3263, 3264, 3265, 3266, 3267, 3283, 3285, 3286, 3292, 3300, 3305, 3310, 3315,
    3321, 3322, 3326, 3327, 3331, 3332, 3334, 3335, 3336, 3337, 3339, 3348, 3349, 3350, 3351, 3352, 3353, 3355, 3358, 3359, 3363, 3365, 3371, 3375, 3376, 3377, 3378, 3379, 3384, 3389,
    3392, 3393, 3395, 3407, 3408, 3410, 3422, 3439, 3460, 3461, 3467, 3473, 3475, 3476, 3479, 3481, 3485, 3497, 3498, 3504, 3507, 3509, 3512, 3513, 3514, 3517, 3518, 3522, 3525, 3526,
    3527, 3528, 3529, 3530, 3531, 3533, 3535, 3536, 3538, 3539, 3540, 3541, 3542, 3543, 3544, 3546, 3547, 3548, 3549, 3550, 3551, 3552, 3553, 3554, 3555, 3556, 3557, 3558, 3560, 3561,
    3562, 3563, 3564, 3565, 3754, 3757, 3758, 3760, 3762, 3764, 3766, 3767, 3768, 3769, 3770, 3771, 3772, 3773, 3774, 3775, 3776, 3777, 3778, 3779, 3780, 3781, 3784, 3785, 3786, 3787,
    3788, 3789, 3790, 3792, 3793, 3794, 3797, 3798, 3811, 3873, 3881, 3893, 3894, 3899, 3900, 3911, 3916, 3917, 3919, 3921, 4007, 4011, 4012, 4016, 4017, 4018, 4020, 4032, 4034, 4035,
    4074, 4077, 4093, 4096, 4097, 4098, 4099, 4100, 4101, 4102, 4103, 4131, 4144, 4145, 4152, 4158, 4159, 4165, 4166, 4167, 4168, 4170, 4172, 4173, 4175, 4178, 4179, 4180, 4217, 4222,
    4226, 4248, 4277, 4287, 4288, 4289, 4290, 4291, 4295, 4315, 4328, 4329, 4330, 4332, 4340, 4341, 4343, 4344, 4345, 4346, 4347, 4348, 4349, 4350, 4352, 4353, 4354, 4355, 4356, 4357,
    4359, 4360, 4361, 4362, 4364, 4365, 4366, 4367, 4369, 4370, 4372, 4373, 4375, 4376, 4377, 4378, 4379, 4386, 4390, 4396, 4397, 4399, 4401, 4402, 4403, 4404, 4405, 4406, 4407, 4408,
    4409, 4410, 4412, 4413, 4414, 4415, 4416, 4417, 4418, 4419, 4420, 4421, 4422, 4423, 4435, 4436, 4437, 4438, 4439, 4440, 4441, 4442, 4443, 4448, 4452, 4453, 4457, 4462, 4476, 4479,
    4483, 4488, 4492, 4494, 4522, 4524, 4529, 4530, 4531, 4534, 4536, 4537, 4539, 4540, 4541, 4542, 4545, 4546, 4547, 4549, 4550, 4553, 4554, 4561, 4562, 4608, 4616, 4649, 4682, 4703,
    4706, 4707, 4822, 4837, 4843, 4844, 4864, 4896, 4898, 4900, 4903, 4904, 4905, 4906, 4909, 4910, 4912, 4913, 4925, 4929, 4930, 4931, 4932, 4933, 4934, 4935, 4937, 4938, 4939, 4941,
    4942, 4943, 4944, 4945, 4948, 4950, 4951, 4952, 4953, 4956, 4958, 4961, 4962, 4968, 4969, 4970, 4973, 4977, 4980, 4981, 4985, 4988, 4994, 4995, 4998, 5001, 5003, 5006, 5008, 5009,
    5010, 5011, 5014, 5015, 5017, 5021, 5022, 5024, 5031, 5036, 5043, 5044, 5046, 5047, 5049, 5050, 5051, 5052, 5053, 5054, 5055, 5056, 5057, 5081, 5082, 5087, 5116, 5121, 5122, 5124,
    5177, 5179, 5181, 5320, 5349, 5352, 5363, 5365, 5372, 5386, 5387, 5402, 5407, 5409, 5412, 5413, 5414, 5415, 5416, 5420, 5432, 5434, 5435, 5436, 5441, 5444, 5447, 5461, 5476, 5479,
    5483, 5485, 5486, 5488, 5489, 5491, 5492, 5493, 5496, 5498, 5499, 5503, 5506, 5510, 5514, 5517, 5518, 5519, 5520, 5584, 5587, 5695, 5734, 5735, 5738, 5741, 5759, 5766, 5776, 5785,
    5786, 5790, 5795, 5796, 5798, 5802, 5803, 5850, 5857, 5860, 5862, 5863, 5873, 5876, 5879, 5886, 5887, 5904, 5909, 5912, 5918, 5920, 5925, 5928, 5932, 5933, 5935, 5936, 5938, 5939,
    5940, 5942, 5943, 5945, 5946, 5947, 5948, 5950, 5951, 5952, 5953, 5954, 5955, 5956, 5960, 5967, 5981, 6012, 6231, 6239, 6240, 6242, 6293, 6296, 6300, 6302, 6305, 6306, 6307, 6308,
    6309, 6310, 6314, 6324, 6327, 6415, 6426]

if (show_all):
    connected_flares = all_flares

print("Connected flares in magentic connectivity tool: ", connected_flares)
print(len(connected_flares))
# get timestamps of connected flares
connected_flares_peak_utc = []
for i in connected_flares:
    connected_flares_peak_utc.append(stix_flares['peak_UTC'][i])

# --------------------------------------- EPD ---------------------------------------

sensor = 'ept' # ['het', 'ept', 'step']
viewing = 'sun' # ['sun', 'asun', 'north', 'south', 'omni']

# load data from compressed EPD dataset
# epd_handler.load_pickles() loads dataframe of timespan defined (including end_date)
# df_ion = epd_handler.load_pickles(sensor, viewing, start_date, end_date, 'ion')
df_electron = epd_handler.load_pickles(sensor, start_date, end_date, 'electron', viewing)

# compute running averade and standard deviation
# ion_running_mean, ion_running_std = epd_handler.running_average(df_ion)
electron_running_mean, electron_running_std = epd_handler.running_average(df_electron)

# try to find events in data
sigma_factor = 2.5
events_electrons = epd_handler.find_event(df_electron, electron_running_mean, electron_running_std, sigma_factor)
# events_ions = epd_handler.find_event(df_ion, ion_running_mean, ion_running_std, sigma_factor)

if(opt_output):
    print(events_electrons)
    # print(events_ions)

epd_connected_flares_electron_peak_utc = []
# epd_connected_flares_ion_peak_utc = []

if flare_end_id != -1:
    # find flares that peak during epd event
    delayed_utc_electrons = []
    delayed_utc_electrons_start = []
    # delayed_utc_ions = []
    indirect_factor = 1.5
    for i in range(flare_start_id, flare_end_id + 1):
        utc = stix_flares['peak_UTC'][i]
        timestamp = pd.Timestamp(utc[0:10] + " " + utc[11:19])
        
        delayed_utc_electrons.append(misc_handler.add_delay('electron', i, timestamp, indirect_factor, stix_flares['solo_position_AU_distance'][i]))
        # delayed_utc_ions.append(misc_handler.add_delay('ion', i, timestamp, indirect_factor))
        
        utc_start = stix_flares['start_UTC'][i]
        timestamp = pd.Timestamp(utc_start[0:10] + " " + utc_start[11:19])
        
        delayed_utc_electrons_start.append(misc_handler.add_delay('electron', i, timestamp, indirect_factor, stix_flares['solo_position_AU_distance'][i]))
        
    for i in range(len(delayed_utc_electrons)):
        for j in range(34):
            delayed_utc_electrons[i][j][0] = delayed_utc_electrons_start[i][j][0]
        
    epd_connected_flares_electrons = []
    # epd_flare_distances_electrons = []
    count = 0
    for i in delayed_utc_electrons:
        temp = False
        for bin in range(34):
            for j in events_electrons:
                if i[bin][0] < j[0] and j[0] < i[bin][1]:
                    epd_connected_flares_electrons.append(flare_start_id + count)
                    # epd_flare_distances_electrons.append(flare_distances[count])
                    temp = True
                    break
            if temp:
                break
        count += 1
    '''
    epd_connected_flares_ions = []
    epd_flare_distances_ions = []
    count = 0
    for i in delayed_utc_ions:
        temp = False
        for bin in range(64):
            for j in events_ions:
                if (j[0] < i[bin][0] and j[1] > i[bin][0]) or (j[0] < i[bin][1] and j[1] > i[bin][1]):
                    epd_connected_flares_ions.append(flare_start_id + count)
                    epd_flare_distances_ions.append(flare_distances[count])
                    temp = True
                    break
            if temp:
                break
        count += 1
    '''
    # plots.histogram(epd_flare_distances_electrons, range(0, 180, 5), "Images/Hist/epd_flares_distance_electrons.jpg", 'Distance to closest passible connection point [degrees]')
    # plots.histogram(epd_flare_distances_ions, range(0, 180, 5), "Images/Hist/epd_flares_distance_ions.jpg", 'Distance to closest passible connection point [degrees]')
        
    print("Connected flares in EPD (electrons): ", epd_connected_flares_electrons)
    print(len(epd_connected_flares_electrons))
    '''
    all_epd_flares = [26, 27, 44, 57, 59, 62, 63, 64, 65, 67, 70, 71, 72, 73, 74, 119, 120, 121, 126, 127, 128, 129, 131, 198, 204, 205, 207, 216, 219, 220, 225, 304, 320, 328, 332, 334, 363, 364, 416, 430, 433, 437, 441, 446, 459, 461, 462, 467, 473, 545, 571, 602, 606, 628, 635, 636, 645, 648, 649, 652, 653, 717, 719, 720, 721, 728, 729, 731, 736, 737, 738, 739, 740, 745, 755, 760, 761, 764, 765, 767, 785, 790, 791, 807, 815, 825, 838, 868, 869, 871, 905, 909, 910, 920, 924, 925, 926, 927, 943, 946, 949, 950, 951, 954, 955, 957, 958, 965, 979, 1001, 1002, 1005, 1028, 1031, 1183, 1184, 1276, 1277, 1282, 
1284, 1318, 1376, 1381, 1390, 1391, 1396, 1397, 1398, 1400, 1403, 1407, 1408, 1409, 1419, 1426, 1427, 1429, 1433, 1437, 1441, 1442, 1448, 1454, 1468, 1481, 1482, 1549, 1551, 1554, 1610, 1611, 1619, 1620, 1621, 1624, 1635, 1637, 1641, 1642, 1644, 1671, 1673, 1692, 1693, 1694, 1695, 1712, 1717, 1718, 1719, 1720, 1721, 1722, 1723, 1724, 1728, 1729, 1732, 1736, 1737, 1739, 1741, 1865, 1876, 1887, 1888, 1922, 1926, 1927, 1928, 1935, 1941, 1942, 1943, 1944, 1951, 1954, 1955, 1956, 1957, 1958, 1960, 1965, 1969, 1970, 1978, 1979, 1997, 1998, 1999, 2008, 2018, 2030, 2033, 2034, 2036, 2037, 2038, 2053, 2059, 2061, 2071, 2097, 2136, 2137, 2146, 2150, 2151, 2156, 2157, 2169, 2170, 2183, 2198, 2205, 2208, 2209, 2245, 2254, 2281, 2295, 2296, 2297, 2299, 2300, 2302, 2307, 2332, 2337, 2341, 2344, 2345, 2346, 2347, 2348, 2349, 2350, 2351, 2353, 2354, 2355, 2356, 2358, 2361, 2362, 2363, 2364, 2367, 2372, 2381, 2400, 2486, 2497, 2498, 2619, 2649, 2650, 2662, 2664, 2665, 2666, 2667, 2668, 2707, 2708, 2711, 2716, 2717, 2728, 2729, 2730, 2748, 2749, 2750, 2751, 2756, 2757, 2758, 2759, 2761, 2762, 2765, 2766, 2769, 2771, 2772, 2773, 2775, 2777, 2778, 2779, 2780, 2781, 2782, 2783, 2784, 
2786, 2787, 2788, 2789, 2790, 2791, 2793, 2806, 2807, 2808, 2809, 2811, 2813, 2815, 2817, 2818, 2819, 2833, 2834, 2845, 2848, 2849, 2858, 2859, 2868, 2879, 2890, 2898, 2902, 2910, 2911, 2932, 2933, 2935, 2954, 2955, 2956, 2959, 2960, 2962, 2963, 2965, 2966, 2969, 2971, 2972, 2978, 2982, 2984, 3019, 3024, 3025, 3031, 3032, 3033, 3371, 3434, 3509, 3541, 3555, 3578, 3628, 3630, 3631, 3632, 3633, 3635, 3696, 3772, 3775, 3779, 3858, 3863, 3899, 3902, 3910, 4021, 4025, 4026, 4031, 4033, 4037, 4038, 4041, 4044, 4045, 4048, 4050, 4051, 4057, 4058, 4059, 4074, 4091, 4187, 4241, 4248, 4318, 4322, 4332, 4333, 4444, 4450, 4451, 4457, 4458, 4460, 4467, 4468, 4477, 4520, 4524, 4527, 4532, 4533, 4539, 4542, 4544, 4545, 4546, 4547, 4548, 4549, 4550, 4551, 4560, 4642, 4701, 4710, 4751, 4754, 4755, 4756, 4757, 4758, 4759, 4761, 4762, 4764, 4765, 4766, 4767, 4768, 4769, 4770, 4772, 4774, 4785, 4786, 4787, 4790, 4805, 4890, 4894, 4895, 4908, 4909, 4911, 4912, 4913, 4925, 4971, 4972, 4984, 4986, 4988, 4994, 4995, 4996, 5005, 5010, 5012, 5013, 5015, 5031, 5035, 5036, 5043, 5057, 5073, 5104, 5111, 5126, 5132, 5134, 5135, 5136, 5137, 5147, 5151, 5152, 5162, 5164, 5165, 5177, 5178, 5186, 
5189, 5190, 5193, 5203, 5204, 5210, 5211, 5215, 5228, 5229, 5267, 5281, 5282, 5283, 5284, 5287, 5288, 5289, 5290, 5291, 5294, 5300, 5371, 5373, 5376, 5377, 5378, 5390, 5405, 5406, 5408, 5409, 5410, 5412, 5413, 5415, 5416, 5418, 5419, 5430, 5431, 5437, 5438, 5442, 5446, 5486, 5491, 5493, 5496, 5510, 5511, 5528, 5536, 5547, 5548, 5585, 5587, 5590, 5600, 5601, 5641, 5663, 5664, 5701, 5712, 5714, 5741, 5777, 5792, 5803, 5805, 5807, 5823, 5827, 5828, 5831, 5834, 5835, 5840, 5841, 5844, 5846, 5888, 5897, 5901, 5908, 5946, 5960, 6015, 6064, 6075, 6141, 6164, 6256, 6265, 6275, 6276, 6277, 6278, 6320, 6426]
    
    epd_connected_flares_electrons = []
    
    for i in all_epd_flares:
        if flare_start_id <= i and flare_end_id >= i:
            epd_connected_flares_electrons.append(i)
    '''
    # print("Connected flares in EPD (ions): ", epd_connected_flares_ions)
    # print(len(epd_connected_flares_ions))

    # get timestamps of connected flares
    for i in epd_connected_flares_electrons:
        epd_connected_flares_electron_peak_utc.append(stix_flares['peak_UTC'][i])
        
    #for i in epd_connected_flares_ions:
    #    epd_connected_flares_ion_peak_utc.append(stix_flares['peak_UTC'][i])

# rename columns for output/figures
col_names_mean = []
col_names_std = []
for col in electron_running_mean.columns:
    col_names_mean.append("Mean" + col[8:])
    col_names_std.append("Mean+" + str(sigma_factor) + "Sigma" + col[8:])
    
electron_running_mean.columns = col_names_mean
electron_running_std.columns = col_names_std

plots.plot_epd_data(df_electron, electron_running_mean, electron_running_std, sigma_factor, 'Images/Electron.jpg', connected_flares_peak_utc,
                    epd_connected_flares_electron_peak_utc, events_electrons)

print(len(events_electrons))

# Add count of events per interval
# Print total number of intervals (for statistics)

epd_connected_flares_electrons = [27, 44, 45, 56, 57, 58, 59, 62, 63, 64, 65, 67, 68, 70, 71, 72, 73, 74, 119, 120, 121, 122, 126, 127, 128, 129, 131, 195, 198, 204, 205, 206, 207, 215, 216, 219, 220, 225, 303, 304, 305, 320, 328,
        332, 334, 363, 364, 437, 441, 444, 446, 461, 462, 465, 473, 474, 628, 635, 636, 648, 649, 652, 653, 717, 719, 720, 721, 722, 723, 731, 732, 736, 737, 739, 740, 747, 755, 757, 760, 761, 764, 765, 766,
        780, 785, 807, 815, 835, 836, 838, 868, 869, 870, 872, 875, 909, 910, 920, 924, 925, 926, 927, 928, 943, 946, 949, 950, 951, 952, 953, 954, 957, 958, 959, 961, 964, 965, 979, 980, 1001, 1002, 1004,
        1005, 1028, 1031, 1084, 1179, 1180, 1183, 1284, 1310, 1311, 1312, 1318, 1381, 1389, 1391, 1396, 1397, 1398, 1400, 1401, 1403, 1404, 1405, 1406, 1407, 1408, 1412, 1413, 1416, 1419, 1427, 1429, 1433,
        1437, 1440, 1441, 1442, 1443, 1449, 1454, 1455, 1462, 1468, 1481, 1482, 1549, 1550, 1551, 1552, 1553, 1554, 1610, 1611, 1613, 1620, 1621, 1622, 1623, 1624, 1637, 1638, 1641, 1642, 1644, 1671, 1673,
        1692, 1693, 1694, 1695, 1717, 1718, 1719, 1722, 1723, 1724, 1725, 1726, 1727, 1728, 1729, 1731, 1732, 1733, 1734, 1736, 1737, 1738, 1739, 1740, 1741, 1876, 1887, 1888, 1889, 1922, 1923, 1926, 1927,
        1928, 1935, 1941, 1942, 1943, 1944, 1950, 1951, 1952, 1954, 1955, 1956, 1957, 1958, 1959, 1960, 1965, 1967, 1969, 1970, 1978, 1998, 2008, 2018, 2019, 2030, 2033, 2034, 2036, 2038, 2050, 2053, 2059,
        2061, 2063, 2071, 2136, 2137, 2146, 2150, 2151, 2156, 2157, 2169, 2170, 2173, 2198, 2205, 2208, 2209, 2220, 2254, 2279, 2295, 2296, 2297, 2299, 2300, 2302, 2304, 2332, 2333, 2337, 2338, 2345, 2346,
        2347, 2348, 2349, 2350, 2351, 2354, 2355, 2356, 2357, 2358, 2361, 2363, 2368, 2369, 2371, 2372, 2497, 2498, 2619, 2641, 2642, 2649, 2650, 2651, 2652, 2662, 2663, 2664, 2665, 2666, 2667, 2668, 2669,
        2696, 2698, 2711, 2712, 2713, 2716, 2717, 2718, 2719, 2728, 2729, 2747, 2749, 2750, 2751, 2752, 2754, 2755, 2756, 2757, 2758, 2759, 2760, 2761, 2762, 2763, 2766, 2767, 2768, 2769, 2770, 2771, 2772,
        2773, 2775, 2776, 2777, 2778, 2779, 2780, 2781, 2782, 2783, 2784, 2786, 2787, 2788, 2789, 2790, 2791, 2792, 2793, 2794, 2795, 2796, 2806, 2807, 2808, 2809, 2810, 2811, 2812, 2813, 2815, 2817, 2818,
        2819, 2845, 2846, 2847, 2849, 2850, 2858, 2868, 2872, 2875, 2879, 2891, 2898, 2902, 2911, 2932, 2933, 2935, 2954, 2955, 2956, 2957, 2958, 2959, 2960, 2961, 2963, 2965, 2966, 2970, 2971, 2972, 2978,
        2984, 2996, 3019, 3024, 3032, 3033, 3062, 3140, 3325, 3371, 3509, 3510, 3541, 3555, 3578, 3626, 3627, 3628, 3629, 3630, 3631, 3632, 3633, 3634, 3635, 3772, 3779, 3899, 3900, 3902, 3919, 4021, 4025,
        4026, 4031, 4033, 4037, 4038, 4041, 4044, 4045, 4048, 4049, 4050, 4051, 4057, 4058, 4059, 4060, 4074, 4091, 4096, 4124, 4187, 4248, 4318, 4322, 4332, 4333, 4444, 4450, 4451, 4457, 4458, 4459, 4460,
        4467, 4468, 4469, 4477, 4493, 4524, 4527, 4529, 4532, 4533, 4539, 4542, 4543, 4544, 4545, 4546, 4547, 4548, 4549, 4550, 4560, 4641, 4642, 4726, 4727, 4744, 4745, 4751, 4754, 4755, 4756, 4757, 4758,
        4759, 4760, 4761, 4762, 4764, 4765, 4766, 4767, 4768, 4770, 4772, 4774, 4775, 4785, 4786, 4787, 4790, 4890, 4891, 4894, 4895, 4896, 4897, 4908, 4909, 4911, 4912, 4913, 4917, 4984, 4988, 4994, 4995,
        4996, 4997, 5005, 5010, 5013, 5015, 5016, 5031, 5035, 5043, 5073, 5104, 5105, 5106, 5132, 5133, 5134, 5135, 5136, 5147, 5148, 5150, 5151, 5152, 5162, 5164, 5165, 5166, 5167, 5168, 5169, 5177, 5178,
        5179, 5180, 5185, 5186, 5192, 5193, 5194, 5203, 5204, 5208, 5209, 5211, 5215, 5227, 5228, 5229, 5267, 5279, 5280, 5281, 5282, 5283, 5284, 5285, 5287, 5288, 5289, 5290, 5291, 5293, 5294, 5295, 5296,
        5300, 5371, 5372, 5373, 5376, 5377, 5378, 5379, 5388, 5389, 5390, 5391, 5394, 5395, 5403, 5404, 5405, 5406, 5408, 5412, 5413, 5414, 5415, 5416, 5418, 5419, 5420, 5431, 5438, 5439, 5442, 5446, 5486,
        5491, 5493, 5494, 5496, 5497, 5510, 5511, 5528, 5529, 5536, 5547, 5548, 5549, 5550, 5551, 5558, 5570, 5571, 5587, 5588, 5589, 5600, 5601, 5602, 5701, 5712, 5714, 5777, 5792, 5800, 5803, 5806, 5807,
        5810, 5817, 5823, 5824, 5828, 5830, 5834, 5835, 5836, 5837, 5841, 5842, 5844, 5845, 5846, 5852, 5888, 5894, 5897, 5901, 5902, 5908, 5960, 6015, 6030, 6048, 6053, 6064, 6065, 6141, 6142, 6143, 6144,
        6256, 6275, 6276, 6277, 6278, 6426]
'''
# 6 (* x) - hour accuracy
x = 28 # number of 6-hour timeframes to take as one
count = 0
date = datetime.datetime.strptime(start_date + " 00:00:00", "%Y-%m-%d %H:%M:%S") - datetime.timedelta(0, x * 3 * 3600)
stat_good = 0
stat_bad = 0
done = False
good_timeframes = []
while date != datetime.datetime.strptime(misc_handler.next_date(end_date) + " 00:00:00", "%Y-%m-%d %H:%M:%S") + datetime.timedelta(0, x * 3 * 3600) and not done:
    good_constellation = False
    bad_constellation = False
    good_count = 0
    bad_count = 0
    while misc_handler.utc_to_datetime(stix_flares['peak_UTC'][connected_flares[count]]) >= date and misc_handler.utc_to_datetime(stix_flares['peak_UTC'][connected_flares[count]]) < date + datetime.timedelta(0, x * 6 * 3600) and not done:
        if connected_flares[count] in epd_connected_flares_electrons:
            good_constellation = True
            good_count += 1
        elif not good_constellation:
            bad_constellation = True
            bad_count += 1
        count += 1
        if count >= len(connected_flares):
            done = True
            count -= 1 # so not to get out of bound errors...
        
    if good_constellation:
        stat_good += 1
        good_timeframes.append([date.strftime("%Y-%m-%d %H:%M:%S"), str(good_count / (good_count + bad_count) * 100) + "%", str(good_count) + "/" + str(good_count + bad_count)])
    if bad_constellation:
        stat_bad += 1
    date += datetime.timedelta(0, x * 6 * 3600)
    
print("Accuracy of " + str(x * 6) + "-hour intervals is: " + str(stat_good / (stat_good + stat_bad) * 100) + "%")
print(good_timeframes)
'''
'''
lst = []

count = 0
for i in [epd_connected_flares_electrons]:    
    mag_footpoint_lon = misc_handler.mag_footpoint_lonitude(stix_flares['peak_UTC'][i])
        
    if min(abs(mag_footpoint_lon - stix_flares['hgc_lon'][i]), abs(mag_footpoint_lon - stix_flares['hgc_lon'][i] + 360), abs(mag_footpoint_lon - stix_flares['hgc_lon'][i] - 360)) <= delta:
        count += 1
        lst.append(i)
        
# print("Accuracy of +/-", delta, "degrees:", count / len(epd_connected_flares_electrons) * 100, "%")

print(lst)

con_flares = [44, 56, 58, 59, 62, 63, 64, 65, 67, 70, 71, 72, 73, 320, 332, 437, 571, 602, 636, 717, 720, 721, 736, 790, 807, 909, 920, 943, 1310, 1381, 1390, 1396, 1403, 1408, 1409, 1419, 
1426, 1427, 1437, 1448, 1551, 1610, 1624, 1635, 1637, 1642, 1643, 1644, 1926, 1927, 1928, 1951, 1955, 2137, 2254, 2300, 2333, 2337, 2341, 2346, 2347, 2348, 2350, 2358, 2363, 2364, 2372,
2381, 2486, 2668, 2858, 2879, 2955, 2956, 2971, 3033, 3371, 3509, 3772, 3779, 3899, 4032, 4074, 4248, 4457, 4462, 4524, 4539, 4542, 4545, 4547, 4549, 4550, 4896, 4909, 4910, 4912, 4913,
4988, 4994, 4995, 5010, 5015, 5031, 5036, 5043, 5057, 5177, 5412, 5413, 5415, 5416, 5486, 5491, 5493, 5496, 5510, 5587, 5741, 5946, 5960, 6426]

for i in con_flares:
    print(stix_flares['peak_UTC'][i])
'''