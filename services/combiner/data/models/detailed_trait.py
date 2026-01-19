from dataclasses import dataclass


@dataclass
class DetailedTrait:
    src: bytes
    is_full_size: bool