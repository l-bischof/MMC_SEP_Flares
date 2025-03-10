from dataclasses import dataclass
import datetime

@dataclass
class Config:
    window_length: int
    start_date: datetime.date
    end_date: datetime.date
    step_sigma: float
    ept_sigma: float
    delta_flares: float
    indirect_factor: float = 1.5