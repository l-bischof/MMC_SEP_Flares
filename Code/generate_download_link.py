'''
Take template link:
http://connect-tool.irap.omp.eu/api/SOLO/ADAPT/PARKER/SCTIME/yyyy-mm-dd/hhmmss
and replace date and time with the according utc timestamp
'''
import stix_handler

flare_id = 6398 # index of flare in STIX list
stix_flares = stix_handler.read_list()

utc = stix_handler.closest_timestamp(stix_flares, flare_id)

url = 'http://connect-tool.irap.omp.eu/api/SOLO/ADAPT/PARKER/SCTIME/' + utc[0:4] + '-' + utc[5:7] + '-' + utc[8:10] + '/' + utc[11:13] + '0000'

print("To download connectivity tool data for flare id: " + str(flare_id) + " use the following link:\n")
print(url)