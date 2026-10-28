from commuteiq.decision import recommend
import pytest

def test_walk_when_prediction_is_fresh_and_same_vehicle():
    d = recommend(6, 9, 4)
    assert d.action == "WALK"
    assert d.margin_minutes == 3
    assert d.expected_steps == 440

@pytest.mark.parametrize("kwargs", [
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
def test_conservative_wait(kwargs):
    args = {"current_eta_minutes": 7, "next_eta_minutes": 9, "walking_minutes": 4}
    args.update(kwargs)
    assert recommend(**args).action == "WAIT"

def test_bad_input():
    with pytest.raises(ValueError):
        recommend(6, 9, -1)
