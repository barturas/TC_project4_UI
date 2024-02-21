import sys
import shutil
import os
from PyQt5.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
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
            self.slices.append({'start': start, 'end': end, 'pitch_shift': 0})

    def adjust_slice(self, slice_index, start_adjust=None, end_adjust=None, pitch_shift=None):
        if 0 <= slice_index < len(self.slices):
            slice_info = self.slices[slice_index]

            # Calculate new start and end times based on the adjustments
            slice_info['start'] += start_adjust if start_adjust is not None else 0
            slice_info['end'] += end_adjust if end_adjust is not None else 0

            # Ensure the new start and end are within the bounds of the original audio
            slice_info['start'] = max(0, min(slice_info['start'], len(self.audio_data)))
            slice_info['end'] = max(slice_info['start'], min(slice_info['end'], len(self.audio_data)))

            # Update pitch shift
            if pitch_shift is not None:
                slice_info['pitch_shift'] = pitch_shift

   
class PlayControl:
    def __init__(self):
        pygame.mixer.init()
        self.current_playback = None
        self.playback_lock = threading.Lock()

    def play(self, audio_sample, slice_index):
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
        # Adjust pitch while attempting to preserve quality
        new_frame_rate = int(audio_segment.frame_rate * (2 ** (pitch_shift / 12.0)))
        shifted_audio = audio_segment._spawn(audio_segment.raw_data, overrides={'frame_rate': new_frame_rate})
        return shifted_audio.set_frame_rate(audio_segment.frame_rate)


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
        upload_button = QPushButton('Upload Audio File (mp3, wav)', self)
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
        hbox.addWidget(QLabel('Slice No:'))
        hbox.addWidget(self.slice_index_input)
        hbox.addWidget(QLabel('Start Adjust (ms):'))
        hbox.addWidget(self.start_adjust_input)
        hbox.addWidget(QLabel('End Adjust (ms):'))
        hbox.addWidget(self.end_adjust_input)
        hbox.addWidget(QLabel('Pitch Shift:'))
        hbox.addWidget(self.pitch_shift_input)
        hbox.addWidget(self.adjust_button)

        # Add the table to display slices
        self.slices_table = QTableWidget(self)
        self.slices_table.setColumnCount(4)  # Playback Key, Start, End, Pitch
        self.slices_table.setHorizontalHeaderLabels(['Playback Key', 'Start', 'End', 'Pitch Shift'])
        layout.addWidget(self.slices_table)

        # Set the table to be read-only
        self.slices_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.slices_table.setFocusPolicy(Qt.NoFocus)  # Ensure table does not get focus
        self.slices_table.setSelectionMode(QTableWidget.NoSelection)  # Disable selection

        layout.addLayout(hbox)
        self.setLayout(layout)
        self.setWindowTitle('Audio Sample Slicer & Slice Editor')
        self.show()

    def update_slices_table(self):
        self.slices_table.setRowCount(len(self.audio_sample.slices))
        for i, slice_info in enumerate(self.audio_sample.slices):
            # Setup QTableWidgetItem for each piece of data
            playback_key_item = QTableWidgetItem("asdfghjkl"[i] if i < len("asdfghjkl") else "N/A")
            start_item = QTableWidgetItem(str(slice_info['start']))
            end_item = QTableWidgetItem(str(slice_info['end']))
            pitch_shift_item = QTableWidgetItem(str(slice_info['pitch_shift']))

            # Set flags to disable editing
            for item in (playback_key_item, start_item, end_item, pitch_shift_item):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            
            # Add the items to the table
            self.slices_table.setItem(i, 0, playback_key_item)
            self.slices_table.setItem(i, 1, start_item)
            self.slices_table.setItem(i, 2, end_item)
            self.slices_table.setItem(i, 3, pitch_shift_item)
    
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
        
        num_slices = 9
        self.audio_sample = AudioSample(file_path)
        self.audio_sample.create_slices(num_slices)

        # Enable inputs and button once an audio sample is loaded
        self.enable_all_inputs()
        self.update_slices_table()


    def adjust_slice(self):
        """
        Adjusts the properties of a selected audio slice based on user input.

        This method processes user inputs for the slice number, start adjustment, end adjustment,
        and pitch shift. It validates the inputs and applies the adjustments to the audio slice.
        If an invalid input is detected, an error message is displayed to the user.
        """
        # Retrieve the user inputs from the QLineEdit widgets
        slice_number_text = self.slice_index_input.text()
        start_adjust_text = self.start_adjust_input.text()
        end_adjust_text = self.end_adjust_input.text()
        pitch_shift_text = self.pitch_shift_input.text()

        # Check if the slice number input is empty and display an error if so
        if not slice_number_text:
            self.show_error_message("Error", "Please enter a slice number to adjust.")
            return

        # Attempt to convert the slice number to an integer and validate it
        try:
            slice_number = int(slice_number_text)
        except ValueError:
            self.show_error_message("Error", "Slice number must be an integer.")
            return

        # Calculate the slice index and ensure it's within the valid range
        slice_index = slice_number - 1
        if not (0 <= slice_index < len(self.audio_sample.slices)):
            self.show_error_message("Error", "Slice number is out of range.")
            return

        # Validate and convert the start adjust input, if provided
        try:
            start_adjust = int(start_adjust_text) if start_adjust_text else None
            if start_adjust is not None and not (0 <= start_adjust < len(self.audio_sample.audio_data)):
                self.show_error_message(
                    "Error",
                    "Start Adjust is out of range. Must be between 0 and {} ms.".format(len(self.audio_sample.audio_data))
                )
                return
        except ValueError:
            self.show_error_message("Error", "Start Adjust must be an integer.")
            return

        # Validate and convert the end adjust input, if provided
        try:
            end_adjust = int(end_adjust_text) if end_adjust_text else None
            if end_adjust is not None and not (0 <= end_adjust <= len(self.audio_sample.audio_data)):
                self.show_error_message(
                    "Error",
                    "End Adjust is out of range. Must be between 0 and {} ms.".format(len(self.audio_sample.audio_data))
                )
                return
        except ValueError:
            self.show_error_message("Error", "End Adjust must be an integer.")
            return

        # Validate and convert the pitch shift input, if provided
        try:
            pitch_shift = int(pitch_shift_text) if pitch_shift_text else None
            if pitch_shift is not None and not (-24 <= pitch_shift <= 24):
                self.show_error_message(
                    "Error",
                    "Pitch Shift is out of range. Pitch shift limit: +/- 2 octaves (+/- 24)."
                )
                return
        except ValueError:
            self.show_error_message("Error", "Pitch Shift must be an integer.")
            return

        # If all inputs are valid, apply the adjustments to the audio slice
        self.audio_sample.adjust_slice(slice_index, start_adjust, end_adjust, pitch_shift)

        # Clear the input fields and update the slices table to reflect the changes
        self.clear_slice_adjust_inputs()
        self.update_slices_table()


    def show_error_message(self, title, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

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