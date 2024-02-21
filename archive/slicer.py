# Implementation of sound file slicer

import threading
from pydub import AudioSegment
import pygame
from pynput.keyboard import Key, Listener

class AudioSample:
    def __init__(self, file_path):
        self.file_path = file_path
        self.audio_data = self.load()
        self.slices = []

    def load(self):
        return AudioSegment.from_file(self.file_path)

    def create_slices(self, num_slices):
        slice_duration = len(self.audio_data) // num_slices
        for i in range(num_slices):
            start = i * slice_duration
            end = start + slice_duration
            self.slices.append((start, end, self.audio_data[start:end]))

    def adjust_slice(self, slice_index, start_adjust=None, end_adjust=None, pitch_shift=None):
        if 0 <= slice_index < len(self.slices):
            old_start, old_end, _ = self.slices[slice_index]

            # Adjust start and end times
            new_start = old_start + start_adjust if start_adjust is not None else old_start
            new_end = old_end + end_adjust if end_adjust is not None else old_end

            # Ensure new start and end are within audio bounds
            new_start = max(0, min(new_start, len(self.audio_data)))
            new_end = max(new_start, min(new_end, len(self.audio_data)))

            slice_audio = self.audio_data[new_start:new_end]

            if pitch_shift is not None:
                # Change pitch
                slice_audio = self.change_pitch(slice_audio, pitch_shift)

            self.slices[slice_index] = (new_start, new_end, slice_audio)

    def change_pitch(self, audio_segment, pitch_shift):
        # Adjust pitch while attempting to preserve quality
        new_frame_rate = int(audio_segment.frame_rate * (2 ** (pitch_shift / 12.0)))
        shifted_audio = audio_segment._spawn(audio_segment.raw_data, overrides={'frame_rate': new_frame_rate})
        return shifted_audio.set_frame_rate(audio_segment.frame_rate)

    
    
class PlayControl:
    def __init__(self):
        pygame.mixer.init()
        self.current_playback = None
        self.playback_lock = threading.Lock()

    def play(self, audio_sample, slice_index):
        with self.playback_lock:
            if self.current_playback:
                self.current_playback.stop()
            _, _, slice_audio = audio_sample.slices[slice_index]  # Use the adjusted slice audio
            raw_audio_data = slice_audio.raw_data
            sound = pygame.mixer.Sound(buffer=raw_audio_data)
            self.current_playback = sound.play()

    def stop_current_playback(self):
        with self.playback_lock:
            if self.current_playback:
                self.current_playback.stop()
                self.current_playback = None



def main():
    audio_sample = AudioSample("sample.mp3")
    audio_sample.create_slices(9)


    keys = "asdfghjkl"
    key_to_slice_map = {key: i for i, key in enumerate(keys)}
    play_control = PlayControl()

    def on_press(key):
        try:
            if key.char in key_to_slice_map:
                slice_index = key_to_slice_map[key.char]
                play_control.play(audio_sample, slice_index)
        except AttributeError:
            if key == Key.esc:
                play_control.stop_current_playback()
                return False

    with Listener(on_press=on_press) as listener:
        listener.join()



if __name__ == "__main__":
    main()
