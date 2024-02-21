import pytest
from audio_app import AudioApp

def test_initialization():
    app = AudioApp()
    assert app.audio_sample is None
    assert app.play_control is not None
    assert app.key_to_slice_map is not None

