from backend.audio.state import RecordingState


def test_initial_state_is_idle():
    state = RecordingState()
    assert state.status == "idle"
    assert state.current_app == ""
    assert state.current_call_id is None
    assert state.duration_sec == 0


def test_update_changes_fields():
    state = RecordingState()
    state.update(status="recording", current_app="Teams.exe", current_call_id=1)
    assert state.status == "recording"
    assert state.current_app == "Teams.exe"
    assert state.current_call_id == 1


def test_to_ws_dict_returns_correct_keys():
    state = RecordingState()
    state.update(status="recording", current_app="Teams.exe", duration_sec=30)
    d = state.to_ws_dict()
    assert d == {
        "type": "recording_status",
        "status": "recording",
        "app": "Teams.exe",
        "duration_sec": 30,
    }


def test_reset_clears_recording_fields():
    state = RecordingState()
    state.update(status="recording", current_app="zoom.exe", current_call_id=5, duration_sec=90)
    state.reset()
    assert state.status == "idle"
    assert state.current_app == ""
    assert state.current_call_id is None
    assert state.duration_sec == 0
