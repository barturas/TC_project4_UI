import sys
import shutil
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
from pydub import AudioSegment
import pygame
import threading

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
        print(self.slices)

    def adjust_slice(self, slice_index, start_adjust=None, end_adjust=None, pitch_shift=None):
        if 0 <= slice_index < len(self.slices):
            old_start, old_end, current_audio = self.slices[slice_index]

            # Calculate new start and end times based on the adjustments
            new_start = old_start + (start_adjust if start_adjust is not None else 0)
            new_end = old_end + (end_adjust if end_adjust is not None else 0)

            # Ensure the new start and end are within the bounds of the original audio
            new_start = max(0, min(new_start, len(self.audio_data)))
            new_end = max(new_start, min(new_end, len(self.audio_data)))

            # Extract the slice audio using the new start and end times
            slice_audio = self.audio_data[new_start:new_end]

            # Apply pitch shift if provided
            if pitch_shift is not None:
                slice_audio = self.change_pitch(slice_audio, pitch_shift)

            # Update the slice record with the new slice data
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

class AudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.audio_sample = None
        self.play_control = PlayControl()
        self.initUI()
        self.key_to_slice_map = {key: i for i, key in enumerate("asdfghjkl")}

    def initUI(self):
        layout = QVBoxLayout()

        # Button for file upload
        upload_button = QPushButton('Upload Audio File', self)
        upload_button.clicked.connect(self.upload_file)
        layout.addWidget(upload_button)

        # Create layout for slice adjustments
        self.slice_index_input = QLineEdit(self)
        self.start_adjust_input = QLineEdit(self)
        self.end_adjust_input = QLineEdit(self)
        self.pitch_shift_input = QLineEdit(self)
        self.adjust_button = QPushButton('Adjust Slice', self)
        self.adjust_button.clicked.connect(self.adjust_slice)
        self.slice_index_input.setFocusPolicy(Qt.ClickFocus)  # Only focus when clicked


        # Disable inputs and button initially
        self.slice_index_input.setEnabled(False)
        self.start_adjust_input.setEnabled(False)
        self.end_adjust_input.setEnabled(False)
        self.pitch_shift_input.setEnabled(False)
        self.adjust_button.setEnabled(False)

        # Layout for inputs
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('Slice Index:'))
        hbox.addWidget(self.slice_index_input)
        hbox.addWidget(QLabel('Start Adjust:'))
        hbox.addWidget(self.start_adjust_input)
        hbox.addWidget(QLabel('End Adjust:'))
        hbox.addWidget(self.end_adjust_input)
        hbox.addWidget(QLabel('Pitch Shift:'))
        hbox.addWidget(self.pitch_shift_input)
        hbox.addWidget(self.adjust_button)

        layout.addLayout(hbox)
        self.setLayout(layout)
        self.setWindowTitle('Audio Sample Slicer')
        self.show()

    def enable_all_inputs(self):
        self.slice_index_input.setEnabled(True)
        self.start_adjust_input.setEnabled(True)
        self.end_adjust_input.setEnabled(True)
        self.pitch_shift_input.setEnabled(True)
        self.adjust_button.setEnabled(True)

    def disable_all_inputs(self):
        self.slice_index_input.setEnabled(False)
        self.start_adjust_input.setEnabled(False)
        self.end_adjust_input.setEnabled(False)
        self.pitch_shift_input.setEnabled(False)
        self.adjust_button.setEnabled(False)
    
    
    
    
    def load_audio_sample(self, file_path):

        num_slices = 9  # Default to 9 slices if input is invalid

        self.audio_sample = AudioSample(file_path)
        self.audio_sample.create_slices(num_slices)

        # Enable inputs and button once an audio sample is loaded
        self.enable_all_inputs()


    def adjust_slice(self):
        try:
            slice_index = int(self.slice_index_input.text())

            # Get the adjust values or None if the fields are empty
            start_adjust = int(self.start_adjust_input.text()) if self.start_adjust_input.text() else None
            end_adjust = int(self.end_adjust_input.text()) if self.end_adjust_input.text() else None
            pitch_shift = int(self.pitch_shift_input.text()) if self.pitch_shift_input.text() else None

            # Apply adjustments
            self.audio_sample.adjust_slice(slice_index, start_adjust, end_adjust, pitch_shift)

            # Clear the inputs after adjusting
            self.clear_slice_adjust_inputs()

        except ValueError as e:
            # Handle the case where the input was not a number
            print("Please enter a valid number for all fields.", e)

    def clear_slice_adjust_inputs(self):
        # Clear the input fields
        self.slice_index_input.clear()
        self.start_adjust_input.clear()
        self.end_adjust_input.clear()
        self.pitch_shift_input.clear()

        # Remove focus from all input fields
        self.slice_index_input.clearFocus()
        self.start_adjust_input.clearFocus()
        self.end_adjust_input.clearFocus()
        self.pitch_shift_input.clearFocus()

        # Set focus back to the main window to capture key presses for playback
        self.setFocus()



    def upload_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "Audio Files (*.mp3 *.wav)", options=options)
        if fileName:
            # Define the upload folder path
            upload_folder = 'upload'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # Copy the file to the upload folder
            shutil.copy(fileName, os.path.join(upload_folder, os.path.basename(fileName)))
            print(f"File uploaded to {upload_folder}")

            # Load the new audio sample
            self.load_audio_sample(os.path.join(upload_folder, os.path.basename(fileName)))


    def keyPressEvent(self, event):
            # Check if the Slice Index field has focus
            if self.slice_index_input.hasFocus():
                # Ignore the key press event and let the base class handle it
                super().keyPressEvent(event)
            else:
                # Handle the key press for playback
                key = event.text()
                if key in self.key_to_slice_map and self.audio_sample:
                    slice_index = self.key_to_slice_map[key]
                    self.play_control.play(self.audio_sample, slice_index)

    



def main():
    app = QApplication(sys.argv)
    ex = AudioApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()