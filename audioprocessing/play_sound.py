from pydub.generators import Sine
from pydub.playback import play

def play_sound():
    sine = Sine(500).to_audio_segment(duration=1000)
    play(sine)

play_sound()