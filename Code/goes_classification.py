import math
import matplotlib.pyplot as plt
import matplotlib as mpl
from collections import Counter
import pandas as pd
import numpy as np

import stix_handler
import plots

# set resolution of plot
dpi = 300
mpl.rc("savefig", dpi = dpi)

# read STIX flare list and extract coordinates of the origin
stix_flares = stix_handler.read_list()

def compute_goes_flux(scaled_counts):
    # f = 10**(-7.376+0.622 log10(X0))
    goes_flux = 10**(-7.376 + 0.622 * math.log10(scaled_counts))
    
    return goes_flux # estimate

def get_goes_classification(flux):
    
    if (flux < 10**-7):
        classification = "A"
    elif (flux < 10**-6):
        classification = "B" + str(math.floor(flux / 10**-7))
    elif (flux < 10**-5):
        classification = "C" + str(math.floor(flux / 10**-6))
    elif (flux < 10**-4):
        classification = "M" + str(math.floor(flux / 10**-5))
    else:
        classification = "X" + str(math.floor(flux / 10**-4))
    
    return classification

def histogram_variable(data, filename = 'Images/Hist/histogram.jpg', xlabel = '', data_all = []):
    '''
    Function to make a histogram. Primarily used to generate a histogram of how far from the flares origin the possible connection points are.
    
    parameters:
    data:       vector with data that should be plotted in the histogram
    filename:   string of location and name the histogram should be saved at
    '''
    if data == []:
        return
    
    plt.clf()
        
    plt.xlabel(xlabel)
    plt.ylabel('Flares')
    
    if data_all == []:
        variable_counts = dict(sorted(Counter(data).items()))
    else:
        counts_all = dict(sorted(Counter(data_all).items()))
        variable_counts = dict(sorted(Counter(data).items()))
        variable_counts = {key: variable_counts[key] if key in variable_counts.keys() else 0 for key in counts_all.keys()}
        m = max(variable_counts.values())
        m_all = max(counts_all.values())
        counts_all = {a: b / m_all * m for a, b in counts_all.items()}
        df_all = pd.DataFrame.from_dict(counts_all, columns = ['expected distribution'], orient='index')
        
        std = []
        for i in df_all['expected distribution']:
            std.append(math.sqrt(i))
        
        ax = df_all.plot(kind = 'bar', yerr = std, align='edge', width = .4, color = 'orange')
    
    df = pd.DataFrame.from_dict(variable_counts, columns = ['estimated GOES classification'], orient='index')
    
    if data_all == []:
        df.plot(kind = 'bar')
    else:
        df.plot(kind = 'bar', align='edge', width = -.4, ax = ax)
            
    plt.xlim(plt.xlim()[0] - .4, plt.xlim()[1] + .4)
    plt.ylim(0, plt.ylim()[1])
    
    plt.plot(0, 0, color = 'black', label = "poisson error")
    
    handles, labels = plt.gca().get_legend_handles_labels()
    if data_all == []:
        order = [0, 1]
    else:
        order = [2, 1, 0]
    plt.legend([handles[idx] for idx in order],[labels[idx] for idx in order])
    
    plt.savefig(filename, bbox_inches = 'tight')
    
    return

goes_classification = []
vis_earth = []
not_vis_earth = []

for i in range(len(stix_flares)):
    counts = stix_flares['4-10 keV'][i] - stix_flares['bkg 4-10 keV'][i]
    
    if stix_flares['att_in'][i]:
        # print("For flare: " + str(i) + " the attenuator was in place.")
        
        classification = "Attenuator (M3+)"
    
    else:
        dist = stix_flares['solo_position_AU_distance'][i]
        scale = dist**2
        
        goes_flux = compute_goes_flux(counts * scale / 4) # STIX list has counts over 4s in it
        
        classification = get_goes_classification(goes_flux)
        
        if (stix_flares['visible_from_earth'][i]):
            vis_earth.append(classification)
        else:
            not_vis_earth.append(classification)
    
    goes_classification.append(classification)

histogram_variable(goes_classification, "Images/Hist/all_flare_classes.jpg", "estimated GOES class")

histogram_variable(vis_earth, "Images/Hist/all_flare_visible_earth.jpg", "estimated GOES class")
histogram_variable(not_vis_earth, "Images/Hist/all_flare_not_visible_earth.jpg", "estimated GOES class")

con_flare_ids = [0, 1, 2, 3, 4, 5, 40, 41, 42, 43, 44, 45, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 76, 96, 97,
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

con_flares_epd_ids = [27, 44, 56, 58, 59, 62, 63, 64, 65, 67, 70, 71, 72, 73, 74, 86, 119, 120, 121, 126, 127, 128, 129, 131, 198, 205, 206, 207, 216, 220, 320, 332, 363, 364, 432, 433, 437, 441, 446, 461, 462, 465, 
467, 473, 491, 545, 571, 602, 635, 636, 648, 649, 652, 653, 717, 719, 720, 721, 729, 736, 738, 755, 756, 760, 761, 764, 790, 791, 807, 815, 825, 826, 838, 869, 870, 871, 905, 909, 910, 920, 924, 
925, 928, 943, 946, 950, 951, 952, 953, 954, 955, 957, 958, 965, 979, 1001, 1002, 1004, 1005, 1028, 1031, 1180, 1183, 1184, 1277, 1282, 1284, 1310, 1311, 1381, 1390, 1396, 1397, 1403, 1407, 1408, 1409, 1416, 1419, 1426, 1427, 1429, 1433, 1437, 1441, 1448, 1454, 1465, 1468, 1481, 1482, 1549, 1551, 1554, 1610, 1619, 1620, 1621, 1622, 1624, 1635, 1637, 1638, 1642, 1643, 1644, 1645, 1671, 1673, 1693, 1694, 1695, 1713, 1718, 1719, 1720, 1721, 1723, 1724, 1725, 1728, 1729, 1736, 1737, 1739, 1740, 1741, 1865, 1876, 1887, 1888, 1926, 1927, 1928, 1935, 1942, 1943, 1944, 1945, 1951, 1952, 1954, 1955, 1956, 1957,
1958, 1960, 1964, 1965, 1969, 1970, 1978, 1979, 1997, 1998, 2008, 2018, 2034, 2038, 2053, 2059, 2064, 2071, 2097, 2136, 2137, 2150, 2151, 2157, 2169, 2170, 2183, 2198, 2209, 2245, 2254, 2278, 2281, 2295, 2297, 2300, 2302, 2333, 2337, 2341, 2344, 2345, 2346, 2347, 2348, 2349, 2350, 2354, 2355, 2356, 2357, 2358, 2361, 2363, 2364, 2372, 2381, 2400, 2486, 2497, 2498, 2620, 2650, 2651, 2662, 2665, 2666, 2668, 2669, 2708, 2709, 2711, 2716, 2717, 2718, 2729, 2730, 2748, 2749, 2750, 2751, 2752, 2756, 2757, 2758, 2759, 2760, 2762, 2765, 2766, 2771, 2772, 2773, 2775, 2776, 2777, 2778, 2779,
2780, 2781, 2782, 2783, 2786, 2787, 2789, 2790, 2791, 2793, 2794, 2806, 2807, 2808, 2809, 2810, 2811, 2815, 2817, 2818, 2834, 2845, 2846, 2848, 2849, 2850, 2858, 2879, 2891, 2898, 2902, 2911, 2933, 2935, 2936, 2955, 2956, 2959, 2960, 2961, 2962, 2963, 2965, 2966, 2969, 2971, 2972, 2982, 2984, 3015, 3019, 3025, 3031, 3032, 3033, 3371, 3434, 3509, 3578, 3628, 3629, 3630, 3631, 3632, 3633, 3635, 3772, 3779, 3858, 3863, 3899, 3902, 4021, 4025, 4026, 4031, 4032, 4033, 4038, 4041, 4044, 4045, 4048, 4050, 4051, 4058, 4059, 4074, 4091, 4187, 4241, 4248, 4318, 4322, 4333, 4444, 4450, 4451, 4457, 4458, 4460, 4462,
4468, 4477, 4510, 4520, 4524, 4527, 4532, 4533, 4539, 4542, 4544, 4545, 4547, 4548, 4549, 4550, 4551, 4560, 4642, 4701, 4710, 4751, 4755, 4756, 4757, 4758, 4759, 4761, 4762, 4764, 4765, 4766, 4767, 4768, 4770, 4774, 4775, 4785, 4786, 4787, 4790, 4805, 4806, 4890, 4891, 4895, 4896, 4897, 4908, 4909, 4910, 4912, 4913, 4917, 4972, 4984, 4986, 4988, 4994, 4995, 4996, 4997, 5005, 5010, 5012, 5015, 5016, 5018, 5030, 5031, 5035, 5036, 5042, 5043, 5057, 5073, 5104, 5111, 5126, 5132, 5134, 5135, 5136, 5137, 5147, 5148, 5149, 5151, 5152, 5164, 5165, 5177, 5178, 5186, 5189, 5190, 5204, 5208, 5209, 5211, 5215, 5216,
5228, 5229, 5267, 5281, 5282, 5283, 5284, 5287, 5288, 5289, 5290, 5291, 5294, 5295, 5300, 5371, 5373, 5376, 5377, 5379, 5391, 5392, 5393, 5405, 5406, 5410, 5412, 5413, 5415, 5416, 5418, 5419,
5430, 5431, 5438, 5439, 5442, 5446, 5486, 5491, 5493, 5496, 5510, 5511, 5528, 5536, 5548, 5585, 5587, 5588, 5589, 5590, 5600, 5601, 5663, 5664, 5700, 5701, 5712, 5714, 5741, 5777, 5792, 5805, 5807, 5823, 5824, 5828, 5831, 5834, 5835, 5836, 5841, 5844, 5845, 5846, 5901, 5908, 5946, 5960, 6075, 6141, 6256, 6265, 6275, 6276, 6277, 6278, 6320, 6426]

both_con_ids = [44, 56, 58, 59, 62, 63, 64, 65, 67, 70, 71, 72, 73, 320, 332, 437, 571, 602, 636, 717, 720, 721, 736, 790, 807, 909, 920, 943, 1310, 1381, 1390, 1396, 1403, 1408, 1409, 1419, 
1426, 1427, 1437, 1448, 1551, 1610, 1624, 1635, 1637, 1642, 1643, 1644, 1926, 1927, 1928, 1951, 1955, 2137, 2254, 2300, 2333, 2337, 2341, 2346, 2347, 2348, 2350, 2358, 2363, 2364, 2372,
2381, 2486, 2668, 2858, 2879, 2955, 2956, 2971, 3033, 3371, 3509, 3772, 3779, 3899, 4032, 4074, 4248, 4457, 4462, 4524, 4539, 4542, 4545, 4547, 4549, 4550, 4896, 4909, 4910, 4912, 4913,
4988, 4994, 4995, 5010, 5015, 5031, 5036, 5043, 5057, 5177, 5412, 5413, 5415, 5416, 5486, 5491, 5493, 5496, 5510, 5587, 5741, 5946, 5960, 6426]

con_flare_class = []
for i in con_flare_ids:
    counts = stix_flares['4-10 keV'][i] - stix_flares['bkg 4-10 keV'][i]
    
    if stix_flares['att_in'][i]:
        # print("For flare: " + str(i) + " the attenuator was in place.")
        
        classification = "Attenuator (M3+)"
    
    else:
        dist = stix_flares['solo_position_AU_distance'][i]
        scale = dist**2
        
        goes_flux = compute_goes_flux(counts * scale / 4) # STIX list has counts over 4s in it
        
        classification = get_goes_classification(goes_flux)
    
    con_flare_class.append(classification)
    
epd_flare_class = []
for i in con_flares_epd_ids:
    counts = stix_flares['4-10 keV'][i] - stix_flares['bkg 4-10 keV'][i]
    
    if stix_flares['att_in'][i]:
        # print("For flare: " + str(i) + " the attenuator was in place.")
        
        classification =  "Attenuator (M3+)"
    
    else:
        dist = stix_flares['solo_position_AU_distance'][i]
        scale = dist**2
        
        goes_flux = compute_goes_flux(counts * scale / 4) # STIX list has counts over 4s in it
        
        classification = get_goes_classification(goes_flux)
    
    epd_flare_class.append(classification)
    
both_flare_class = []
for i in both_con_ids:
    counts = stix_flares['4-10 keV'][i] - stix_flares['bkg 4-10 keV'][i]
    
    if stix_flares['att_in'][i]:
        # print("For flare: " + str(i) + " the attenuator was in place.")
        
        classification =  "Attenuator (M3+)"
    
    else:
        dist = stix_flares['solo_position_AU_distance'][i]
        scale = dist**2
        
        goes_flux = compute_goes_flux(counts * scale / 4) # STIX list has counts over 4s in it
        
        classification = get_goes_classification(goes_flux)
    
    both_flare_class.append(classification)
    
histogram_variable(con_flare_class, "Images/Hist/con_flare_classes.jpg", "estimated GOES class", goes_classification)
histogram_variable(epd_flare_class, "Images/Hist/epd_flare_classes.jpg", "estimated GOES class", goes_classification)
histogram_variable(both_flare_class, "Images/Hist/both_flare_classes.jpg", "estimated GOES class", goes_classification)

# compare to candidates
# histogram_variable(both_flare_class, "Images/Hist/comp_can_con.jpg", "estimated GOES class", con_flare_class)

# 2-d plot
est_flux = []
dist_all = []

for i in range(len(stix_flares)):
    counts = stix_flares['4-10 keV'][i] - stix_flares['bkg 4-10 keV'][i]
    
    if not stix_flares['att_in'][i]:
        dist = stix_flares['solo_position_AU_distance'][i]
        scale = dist**2
        
        est_flux.append(compute_goes_flux(counts * scale / 4)) # STIX list has counts over 4s in it
        dist_all.append(dist)

plots.histogram_2d(est_flux, dist_all, [np.logspace(np.log10(10**-7), np.log10(10**-3.5)), np.arange(0.25, 1.1, 0.05)], "Images/Hist/2d_test")

def histogram_variable_2(data1, data2, filename = 'Images/Hist/histogram.jpg'):
    '''
    Function to make a histogram. Primarily used to generate a histogram of how far from the flares origin the possible connection points are.
    
    parameters:
    data:       vector with data that should be plotted in the histogram
    filename:   string of location and name the histogram should be saved at
    '''
    if data1 == []:
        return
    
    plt.clf()
    
    variable_counts1 = dict(sorted(Counter(data1).items()))
    variable_counts2 = dict(sorted(Counter(data2).items()))
    df = pd.DataFrame.from_dict({'Connected': variable_counts1, 'Connected & EPD event' : variable_counts2})
    # df.plot.bar()
    df.plot.bar(logy = True)
    
    plt.savefig(filename, bbox_inches = 'tight')
    
    return

def histogram_variable_3(data1, data2, data3, filename = 'Images/Hist/histogram.jpg'):
    '''
    Function to make a histogram. Primarily used to generate a histogram of how far from the flares origin the possible connection points are.
    
    parameters:
    data:       vector with data that should be plotted in the histogram
    filename:   string of location and name the histogram should be saved at
    '''
    if data1 == []:
        return
    
    plt.clf()
    
    variable_counts1 = dict(sorted(Counter(data1).items()))
    variable_counts2 = dict(sorted(Counter(data2).items()))
    variable_counts3 = dict(sorted(Counter(data3).items()))
    df = pd.DataFrame.from_dict({'Connected events' : variable_counts1, 'EPD events': variable_counts2, 'Connected & EPD events' : variable_counts3})
    # df.plot.bar()
    df.plot.bar(logy = True)
    
    plt.savefig(filename, bbox_inches = 'tight')
    
    return

overlap = [44, 45, 56, 57, 58, 67, 68, 70, 71, 72, 73, 437, 636, 720, 721, 766, 909, 1381, 1401, 1403, 1404, 1405, 1408, 1412, 1610, 1637, 1926, 1927, 1951, 2346, 2347, 2348, 2350, 2955, 2956, 2971,
           3033, 3371, 3555, 4248, 4529, 4534, 4542, 4549, 5412, 5413, 5414, 5416, 5420, 5493, 5587, 6426, 69, 1440, 1928, 4550, 765, 943, 4988, 62, 63, 64, 1409, 1624, 2300, 2358]

overlap_flare_class = []
for i in overlap:
    counts = stix_flares['4-10 keV'][i] - stix_flares['bkg 4-10 keV'][i]
    
    if stix_flares['att_in'][i]:
        # print("For flare: " + str(i) + " the attenuator was in place.")
        
        classification =  "Attenuator (M3+)"
    
    else:
        dist = stix_flares['solo_position_AU_distance'][i]
        scale = dist**2
        
        goes_flux = compute_goes_flux(counts * scale / 4) # STIX list has counts over 4s in it
        
        classification = get_goes_classification(goes_flux)
    
    overlap_flare_class.append(classification)
    
histogram_variable(overlap_flare_class, "Images/Hist/overlap_flare_classes.jpg", "estimated GOES class")

histogram_variable_2(con_flare_class, overlap_flare_class, "Images/Hist/overlap_flare_classes_2.jpg")

histogram_variable_3(con_flare_class, epd_flare_class, overlap_flare_class, "Images/Hist/overlap_flare_classes_3.jpg")

con_flare_class = []
for i in con_flare_ids:
    counts = stix_flares['4-10 keV'][i] - stix_flares['bkg 4-10 keV'][i]
    
    if stix_flares['att_in'][i]:
        # print("For flare: " + str(i) + " the attenuator was in place.")
        
        classification = "Attenuator (M3+)"
        
        # print(i, "Att", counts)
    
    else:
        dist = stix_flares['solo_position_AU_distance'][i]
        scale = dist**2
        
        goes_flux = compute_goes_flux(counts * scale / 4) # STIX list has counts over 4s in it
        
        classification = get_goes_classification(goes_flux)
        
        # if classification in ["M8"]:
            # print(i, classification)
    
    con_flare_class.append(classification)