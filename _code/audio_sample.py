from pydub import AudioSegment

class AudioSample:
    """
    A class to represent an audio sample and its slices for editing.
    
    Attributes:
        file_path (str): The path to the audio file.
        audio_data (AudioSegment): The audio segment loaded from the file.
        slices (list): A list of dictionaries containing slice information.
    """
    
    def __init__(self, file_path):
        """
        The constructor for AudioSample class.
        
        Parameters:
            file_path (str): The path to the audio file.
        """
        self.file_path = file_path
        self.audio_data = self.load()
        self.slices = []

    def load(self):
        """Load the audio file into an AudioSegment object."""
        return AudioSegment.from_file(self.file_path)

    def create_slices(self, num_slices):
        """
        Create equal-length audio slices from the audio data.
        
        Parameters:
            num_slices (int): The number of slices to create.
        """
        slice_duration = len(self.audio_data) // num_slices
        for i in range(num_slices):
            start = i * slice_duration
            end = start + slice_duration
            self.slices.append({'start': start, 'end': end, 'pitch_shift': 0})

    def adjust_slice(self, slice_index, start_adjust=None, end_adjust=None, pitch_shift=None):
        """
        Adjust the specified slice with new start, end, and pitch shift values.
        
        Parameters:
            slice_index (int): The index of the slice to adjust.
            start_adjust (int): The amount to adjust the start time in milliseconds.
            end_adjust (int): The amount to adjust the end time in milliseconds.
            pitch_shift (int): The amount to adjust the pitch.
        """
        if 0 <= slice_index < len(self.slices):
            slice_info = self.slices[slice_index]
            # Calculate new start and end times based on the adjustments
            new_start = slice_info['start'] + (start_adjust if start_adjust is not None else 0)
            new_end = slice_info['end'] + (end_adjust if end_adjust is not None else 0)

            # Ensure the new start and end are within the bounds of the original audio
            if new_start < 0 or new_start > len(self.audio_data):
                raise ValueError("Start Adjust is out of range. Must be between 0 and {} ms.".format(len(self.audio_data)))

            if new_end < 0 or new_end > len(self.audio_data):
                raise ValueError("End Adjust is out of range. Must be between 0 and {} ms.".format(len(self.audio_data)))

            if new_start > new_end:
                raise ValueError("Start Adjust must be less than or equal to End Adjust.")

            # Update pitch shift as a delta and limit it to the range of -24 to 24
            if pitch_shift is not None:
                new_pitch_shift = slice_info['pitch_shift'] + pitch_shift
                
                # Raise a ValueError if pitch shift is out of range
                if new_pitch_shift < -24 or new_pitch_shift > 24:
                    raise ValueError("Pitch Shift must be between -24 and 24.")
                
                slice_info['pitch_shift'] = new_pitch_shift
            
            # Update the start and end times after validation
            slice_info['start'] = new_start
            slice_info['end'] = new_end


        