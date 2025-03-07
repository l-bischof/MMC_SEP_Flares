from dataclasses import dataclass

@dataclass
class Config:
    window_length: int
    step_sigma: float
    ept_sigma: float
    delta_flares: float
    indirect_factor: float = 1.5