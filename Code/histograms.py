import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

# set resolution of plot
dpi = 300
mpl.rc("savefig", dpi = dpi)

bins = np.arange(0, 12, 0.5)
data_detected = [6.25, 6.25, 6.25, 6.25, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75,
                7.25, 7.25, 7.25, 7.25, 7.25, 7.25, 7.75, 7.75, 8.25, 8.75, 6.75]
data_all = [6.25, 6.25, 6.25, 6.25, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75,
            7.25, 7.25, 7.25, 7.25, 7.25, 7.75, 7.75, 8.25, 8.75, 7.25, 6.25, 7.25, 6.75]
data_correct = [6.25, 6.25, 6.25, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75, 6.75,
                7.25, 7.25, 7.25, 7.25, 7.25, 7.75, 7.75, 8.25, 8.75]

plt.clf()
    
plt.xlim(0, bins[-1] + bins[1] - bins[0]) # This should set the upper and lower limit to the range where all flares are in

plt.xlabel('Magnitude of event')
plt.ylabel('Number of events')

plt.hist(data_all, bins, label = "Missed events")
plt.hist(data_detected, bins, label = "False positives")
plt.hist(data_correct, bins, label = "Correct events")

plt.legend(loc='upper left') 

plt.savefig("Images/Hist/magnitude_detected_events.jpg", bbox_inches = 'tight')