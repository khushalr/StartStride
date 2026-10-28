"""Pure, explainable wait-versus-walk recommendation engine.

Arrival predictions at CURRENT and NEXT stops must refer to the same vehicle/trip.
All inputs are minutes from the same observation timestamp. This is not a live-data client.
"""
from dataclasses import dataclass
from math import isfinite

@dataclass(frozen=True)
class Decision:
    action: str
    reason: str
    walking_minutes: float
    buffer_minutes: float
    expected_steps: int
    margin_minutes: float | None

def recommend(
    current_eta_minutes: float | None,
    next_eta_minutes: float | None,
    walking_minutes: float,
    *,
    wants_steps: bool = True,
    safety_buffer_minutes: float = 2.0,
    steps_per_minute: int = 110,
    same_vehicle: bool = True,
    feed_age_seconds: float = 0,
    max_feed_age_seconds: float = 90,
    next_stop_served: bool = True,
    accessible_walk: bool = True,
) -> Decision:
    """Only recommend walking when the same vehicle is predicted at both stops.

    This conservative rule is not a promise that a rider will catch the vehicle:
    it ignores unforeseeable congestion, signals, and walking interruptions.
    """
    for name, value in (("walking_minutes", walking_minutes), ("safety_buffer_minutes", safety_buffer_minutes),
                        ("feed_age_seconds", feed_age_seconds), ("max_feed_age_seconds", max_feed_age_seconds)):
        if not isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and nonnegative")
    if not isinstance(steps_per_minute, int) or steps_per_minute < 0:
        raise ValueError("steps_per_minute must be a nonnegative integer")
    steps = round(walking_minutes * steps_per_minute)
    base = dict(walking_minutes=walking_minutes, buffer_minutes=safety_buffer_minutes, expected_steps=steps)
    if not accessible_walk:
        return Decision("WAIT", "Walking route not confirmed accessible.", margin_minutes=None, **base)
    if not next_stop_served:
        return Decision("WAIT", "The target streetcar does not serve the next stop.", margin_minutes=None, **base)
    if feed_age_seconds > max_feed_age_seconds:
        return Decision("WAIT", "Real-time predictions are stale.", margin_minutes=None, **base)
    if not same_vehicle:
        return Decision("WAIT", "Predictions cannot be matched to the same vehicle.", margin_minutes=None, **base)
    if current_eta_minutes is None or next_eta_minutes is None:
        return Decision("WAIT", "A required arrival prediction is missing.", margin_minutes=None, **base)
    if any(not isfinite(x) or x < 0 for x in (current_eta_minutes, next_eta_minutes)):
        raise ValueError("ETAs must be finite and nonnegative")
    margin = next_eta_minutes - walking_minutes - safety_buffer_minutes
    if not wants_steps:
        return Decision("WAIT", "User prefers not to walk.", margin_minutes=margin, **base)
    if current_eta_minutes <= walking_minutes:
        return Decision("WAIT", "Streetcar may arrive at the current stop before the walk finishes.", margin_minutes=margin, **base)
    if margin <= 0:
        return Decision("WAIT", "Insufficient buffer to reach the next stop.", margin_minutes=margin, **base)
    return Decision("WALK", "Walking is feasible based on matched, fresh predictions; arrival not guaranteed.",
                    margin_minutes=margin, **base)
