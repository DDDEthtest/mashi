from dataclasses import dataclass

@dataclass
class MashupError:
    error_msg: str
    data: dict | None = None