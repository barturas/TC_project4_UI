import sys
import shutil
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from slicer import AudioSample

class AudioApp(QWidget):
    def __init__(self):
        super().__init__()
        self.audio_sample = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Button for file upload
        upload_button = QPushButton('Upload Audio File', self)
        upload_button.clicked.connect(self.upload_file)
        layout.addWidget(upload_button)

        info_label = QLabel("Up to 9 slices can be created, which will be played using keyboard letters from 'a' to 'l' (a - slice[0], s - slice[1], ..., k - slice[7], l - slice[8]).")
        layout.addWidget(info_label)        
        
        # Input for number of slices
        self.num_slices_input = QLineEdit(self)
        self.num_slices_input.setPlaceholderText("Enter number of slices")
        layout.addWidget(self.num_slices_input)

        # Create layout for slice adjustments
        self.slice_index_input = QLineEdit(self)
        self.start_adjust_input = QLineEdit(self)
        self.end_adjust_input = QLineEdit(self)
        self.pitch_shift_input = QLineEdit(self)
        self.adjust_button = QPushButton('Adjust Slice', self)
        self.adjust_button.clicked.connect(self.adjust_slice)

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
        self.setWindowTitle('Audio Sample Adjuster')
        self.show()

    def load_audio_sample(self, file_path):
        self.audio_sample = AudioSample(file_path)
        self.audio_sample.create_slices(9)  # Adjust slice count as needed

        # Enable inputs and button once an audio sample is loaded
        self.slice_index_input.setEnabled(True)
        self.start_adjust_input.setEnabled(True)
        self.end_adjust_input.setEnabled(True)
        self.pitch_shift_input.setEnabled(True)
        self.adjust_button.setEnabled(True)

    def adjust_slice(self):
        # Get values from inputs
        slice_index = int(self.slice_index_input.text())
        start_adjust = int(self.start_adjust_input.text())
        end_adjust = int(self.end_adjust_input.text())
        pitch_shift = int(self.pitch_shift_input.text())

        # Adjust the audio slice
        self.audio_sample.adjust_slice(slice_index, start_adjust, end_adjust, pitch_shift)

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

def main():
    app = QApplication(sys.argv)
    ex = AudioApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
