"""Educational model: no traffic, fuel, weather, safety cars or race prediction."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Compound:
    name: str
    offset: float
    degradation: float


COMPOUNDS = {c.name: c for c in (
    Compound("SOFT", -0.6, 0.09),
    Compound("MEDIUM", 0.0, 0.055),
    Compound("HARD", 0.45, 0.03),
)}


def stint_time(laps: int, compound: str, base: float = 84.0, multiplier: float = 1.0) -> float:
    if laps < 0 or base <= 0 or multiplier < 0:
        raise ValueError("Invalid stint inputs")
    c = COMPOUNDS[compound]
    return laps * (base + c.offset) + c.degradation * multiplier * laps * (laps - 1) / 2


def simulate(race_laps=53, stop_lap=24, first="MEDIUM", second="HARD", pit_loss=22.0,
             base=84.0, multiplier=1.0):
    if race_laps < 2 or not 1 <= stop_lap < race_laps or pit_loss < 0:
        raise ValueError("Stop must occur before the final lap; pit loss cannot be negative")
    if first == second:
        raise ValueError("Dry-race scenario requires two distinct compounds")
    return (stint_time(stop_lap, first, base, multiplier)
            + stint_time(race_laps - stop_lap, second, base, multiplier) + pit_loss)


def optimal_stop(**kwargs):
    n = kwargs.get("race_laps", 53)
    return min(range(1, n), key=lambda lap: simulate(stop_lap=lap, **kwargs))
