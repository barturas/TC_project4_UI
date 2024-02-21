import pygame
import threading

class PlayControl:
    """
    A class to control the playback of audio slices using pygame mixer.
    
    Attributes:
        current_playback (pygame.mixer.Sound): The current playback sound object.
        playback_lock (threading.Lock): A lock to ensure thread-safe control of the playback.
    """
    
    def __init__(self):
        """The constructor for PlayControl class."""
        pygame.mixer.init()
        self.current_playback = None
        self.playback_lock = threading.Lock()

    def play(self, audio_sample, slice_index):
        """
        Play a specific slice from an audio sample.
        
        Parameters:
            audio_sample (AudioSample): The audio sample containing the slice.
            slice_index (int): The index of the slice to play.
        """
        with self.playback_lock:
            if self.current_playback:
                self.current_playback.stop()

            slice_info = audio_sample.slices[slice_index]
            start, end, pitch_shift = slice_info['start'], slice_info['end'], slice_info['pitch_shift']
            
            # Extract the slice audio using the timecodes
            slice_audio = audio_sample.audio_data[start:end]

            # Apply pitch shift if needed
            if pitch_shift != 0:
                slice_audio = self.change_pitch(slice_audio, pitch_shift)

            raw_audio_data = slice_audio.raw_data
            sound = pygame.mixer.Sound(buffer=raw_audio_data)
            self.current_playback = sound.play()

    def change_pitch(self, audio_segment, pitch_shift):
        """
        Change the pitch of a given audio segment.
        
        Parameters:
            audio_segment (AudioSegment): The audio segment to change pitch of.
            pitch_shift (int): The amount to shift the pitch.
        
        Returns:
            AudioSegment: The pitch-shifted audio segment.
        """
        # Adjust pitch while attempting to preserve quality
        new_frame_rate = int(audio_segment.frame_rate * (2 ** (pitch_shift / 12.0)))
        shifted_audio = audio_segment._spawn(audio_segment.raw_data, overrides={'frame_rate': new_frame_rate})
        return shifted_audio.set_frame_rate(audio_segment.frame_rate)