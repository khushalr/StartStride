from commuteiq.decision import recommend
import pytest

VALID = {"current_eta_minutes": 6, "next_eta_minutes": 9, "walking_minutes": 4,
         "same_vehicle": True, "next_stop_served": True, "accessible_walk": True}

def test_walk_when_prediction_fresh_and_same_vehicle():
    d = recommend(**VALID)
    assert d.action == "WALK"
    assert d.margin_minutes == 3
    assert d.expected_steps == 440

@pytest.mark.parametrize("overrides", [
    {"feed_age_seconds": 200},
    {"same_vehicle": False},
    {"next_stop_served": False},
    {"accessible_walk": False},
    {"wants_steps": False},
    {"current_eta_minutes": None},
    {"next_eta_minutes": None},
    {"current_eta_minutes": 3},
    {"next_eta_minutes": 6},
])
def test_conservative_wait(overrides):
    values = dict(VALID)
    values.update(overrides)
    assert recommend(**values).action == "WAIT"

def test_unverified_conditions_fail_closed_by_default():
    assert recommend(6, 9, 4).action == "WAIT"

@pytest.mark.parametrize("bad", [-1, float("nan"), float("inf")])
def test_bad_walk_time(bad):
    with pytest.raises(ValueError):
        recommend(6, 9, bad)
