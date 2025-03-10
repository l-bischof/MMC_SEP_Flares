import pandas as pd
import numpy as np
import misc
import config
from classes import Config


def cleanup_sensor(df_step: pd.DataFrame):
    length = 32
    if ('Integral_Avg_Flux_47' in df_step.columns):
        length = 48
    df_step_electron = pd.DataFrame(columns = [], index = df_step.index)
    zipped_columns = [(f'Electron_Avg_Flux_{i}', f"Integral_Avg_Flux_{i}", f"Magnet_Avg_Flux_{i}") for i in range(length)]

    for electron_col, integral_col, magnet_col in zipped_columns:
        df_step_electron[electron_col] = df_step[integral_col] - df_step[magnet_col]

    return df_step_electron


def shift_sensor(df_step_electron, flare_range: pd.DataFrame, length, parker_dist_series, _config: Config):
    if len(flare_range) > 0:
        first_index = flare_range.index[0]
        delay_frame = misc.step_delay(str(_config.start_date), length, parker_dist=parker_dist_series[first_index])
    else:
        delay_frame = misc.step_delay(str(_config.start_date), length)

    # The highest index contains the fastest electrons
    dt_min = delay_frame[-1]

    # Correcting the timedelta between the Electrons
    offset = ((delay_frame - dt_min) // config.TIME_RESOLUTION).astype(np.int64)
    df_offset_step = df_step_electron.copy()

    for i, column in enumerate(df_offset_step.columns):
        df_offset_step[column] = df_offset_step[column].shift(-offset[i])
    
    return df_offset_step, offset
