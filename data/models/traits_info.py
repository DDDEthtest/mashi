from dataclasses import dataclass


@dataclass
class TraitsInfo:
    frames: int
    frame_t: float
    total_t: float
    is_animated: bool