import pandas as pd
import numpy as np
import datetime
import matplotlib as mpl
import matplotlib.pyplot as plt

import stix_handler
import connectivity_tool
import plots
import epd_handler
import misc_handler
import math

dpi = 300
mpl.rc("savefig", dpi = dpi)

# work with data and search for events within the following timespan
start_date = "2023-01-01"
end_date = "2023-01-31"

# read STIX flare list and extract coordinates of the origin
stix_flares = stix_handler.read_list()

# get range of flares that are within the defined timeframe
flare_start_id, flare_end_id = stix_handler.flares_range(start_date, end_date, stix_flares['peak_UTC'])

connected_flares_all = [0, 1, 2, 3, 4, 5, 40, 41, 42, 43, 44, 45, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 76, 96, 97,
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

connected_flares_utc = []

for i in connected_flares_all:
    if (i >= flare_start_id) and (i <= flare_end_id):
        connected_flares_utc.append(stix_flares['peak_UTC'][i])

# --------------------------------------- EPD ---------------------------------------

sensor = 'step' # ['het', 'ept', 'step']

# columns of step data
# ['DELTA_EPOCH', 'Integral_Avg_Flux_0-47', 'Integral_Avg_Uncertainty_0-47', 'Magnet_Avg_Flux_0-47', 'Magnet_Avg_Uncertainty_0-47', 'QUALITY_BITMASK', 'QUALITY_FLAG', 'SMALL_PIXELS_FLAG']
df_step = epd_handler.load_pickles(sensor, start_date, end_date)

# remove flag columns as currently not used
drop_columns = ['DELTA_EPOCH', 'QUALITY_BITMASK', 'QUALITY_FLAG']
if ('SMALL_PIXELS_FLAG' in df_step.columns):
    drop_columns.append('SMALL_PIXELS_FLAG')

length = 32
if ('Integral_Avg_Flux_47' in df_step.columns):
    length = 48

drop_magnet = []
drop_integral = []
electron_cols = []
for i in range(length):
    drop_columns.append('Integral_Avg_Uncertainty_' + str(i))
    drop_columns.append('Magnet_Avg_Uncertainty_' + str(i))
    drop_integral.append('Integral_Avg_Flux_' + str(i))
    drop_magnet.append('Magnet_Avg_Flux_' + str(i))
    electron_cols.append('Electron_Avg_Flux_' + str(i))
    
df_step_data = df_step.drop(drop_columns, axis = 1)

# compute electron counts (integral - magnet ~> all - ions)
df_step_electron = pd.DataFrame(columns = electron_cols, index = df_step.index)
df_integral = df_step_data.drop(drop_magnet, axis = 1)
df_magnet = df_step_data.drop(drop_integral, axis = 1)
for i in range(length):
    integral_col = df_integral.columns[i]
    magnet_col = df_magnet.columns[i]
    df_step_electron[electron_cols[i]] = pd.Series(df_integral[integral_col].to_numpy() - df_magnet[magnet_col].to_numpy(), index = df_step_electron.index)

#TODO: Differentiate between 32 & 48 energy channels
    # This is needed as the energy ranges are different

# compute running averade and standard deviation
running_mean, running_std = epd_handler.running_average(df_step_electron)

# compute expected delay of arriving particles
dt = misc_handler.step_delay(start_date, length)

if length == 32:
    dt_min = dt[31]
else:
    dt_min = dt[47]

offset = []
for i in range(length):
    offset.append(math.floor((dt[i] - dt_min) / 300))

df_offset_step = df_step_electron.copy()
count = 0

for i in df_offset_step.columns:
    for j in df_offset_step.index:
        idx = df_offset_step.index.get_loc(j)
        
        if(idx + offset[count] >= len(df_offset_step.index)):
            df_offset_step[i][j] = np.nan
        else:
            df_offset_step[i][j] = df_offset_step[i][df_offset_step.index[idx + offset[count]]]
            
    count += 1

# try to find events in data
sigma_factor = 3.5
events = epd_handler.find_event(df_offset_step, running_mean, running_std, sigma_factor)

# rename columns for output/figures
col_names_mean = []
col_names_std = []
for col in running_mean.columns:
    col_names_mean.append("Mean" + col[12:])
    col_names_std.append("Mean+" + str(sigma_factor) + "Sigma" + col[12:])
    
running_mean.columns = col_names_mean
running_std.columns = col_names_std

epd_connected_flares_peak_utc = []

if flare_end_id != -1:
    # find flares that peak during epd event
    delayed_utc = []
    delayed_utc_start = []
    # delayed_utc_ions = []
    indirect_factor = 1.5
    for i in range(flare_start_id, flare_end_id + 1):
        utc = stix_flares['peak_UTC'][i]
        timestamp = pd.Timestamp(utc[0:10] + " " + utc[11:19])
        
        dt = misc_handler.step_delay(utc, length)
        
        delay = []
        for j in range(length):
            delay_direct = timestamp + datetime.timedelta(0, math.floor(dt[j]))
            delay_indirect = timestamp + datetime.timedelta(0, math.floor(dt[j] * indirect_factor))
            
            delay.append([delay_direct, delay_indirect])
        
        delayed_utc.append(delay)
        
        utc_start = stix_flares['start_UTC'][i]
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
                    epd_connected_flares.append(flare_start_id + count)
                    temp = True
                    break
            if temp:
                break
        count += 1
        
    for i in epd_connected_flares:
        epd_connected_flares_peak_utc.append(stix_flares['peak_UTC'][i])

plots.plot_step_data(df_step_electron, running_mean, running_std, sigma_factor, offset, 'test/test.jpg', connected_flares_utc, epd_connected_flares_peak_utc, events)

print(len(events))