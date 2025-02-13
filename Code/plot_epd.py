import plots
import epd_handler
import config

# timespan to plot
start_date = config.START_DATE
end_date = config.END_DATE

sensor = 'ept' # ['het', 'ept', 'step']
viewing = 'omni' # ['sun', 'asun', 'north', 'south', 'omni']

# enter flare ids if they shoulb be shown
connected_flares_peak_utc = []

# load data from compressed EPD dataset
# epd_handler.load_pickles() loads dataframe of timespan defined (including end_date)
df_ion = epd_handler.load_pickles(sensor, viewing, start_date, end_date, 'ion')
df_electron = epd_handler.load_pickles(sensor, viewing, start_date, end_date, 'electron')

# Define timespan for background estimation
back_start_date = "2023-01-24"
back_end_date = "2023-01-24"

back_ion = epd_handler.background(epd_handler.load_pickles(sensor, viewing, back_start_date, back_end_date, 'ion'))
back_electron = epd_handler.background(epd_handler.load_pickles(sensor, viewing, back_start_date, back_end_date, 'electron'))

# try to find events in data
events = epd_handler.find_event(df_ion, back_ion)

plots.plot_epd_data(df_ion[['Ion_Flux_1']], back_ion, 1, 'ion', f'{config.OUTPUT_DIR}/Images/Ion_Flux_1.jpg', connected_flares_peak_utc)
plots.plot_epd_data(df_ion[['Ion_Flux_10']], back_ion, 10, 'ion', f'{config.OUTPUT_DIR}/Images/Ion_Flux_10.jpg', connected_flares_peak_utc)
plots.plot_epd_data(df_ion[['Ion_Flux_32']], back_ion, 32, 'ion', f'{config.OUTPUT_DIR}/Images/Ion_Flux_32.jpg', connected_flares_peak_utc)

plots.plot_epd_data(df_electron[['Electron_Flux_1']], back_electron, 1, 'electron', f'{config.OUTPUT_DIR}/Images/Electron_Flux_1.jpg', connected_flares_peak_utc)
plots.plot_epd_data(df_electron[['Electron_Flux_10']], back_electron, 10, 'electron', f'{config.OUTPUT_DIR}/Images/Electron_Flux_10.jpg', connected_flares_peak_utc)