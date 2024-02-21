import os
import shutil

from PyQt5.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
from audio_sample import AudioSample
from play_control import PlayControl
from PyQt5.QtGui import QIntValidator, QPixmap

class AudioApp(QWidget):
    """
    Main application window for the audio sample slicer and editor.

    Attributes:
        audio_sample (AudioSample): The currently loaded audio sample.
        play_control (PlayControl): The playback controller for audio.
        key_to_slice_map (dict): Mapping of keyboard keys to slice indices.
    """
    
    def __init__(self):
        """Initializes the main application window."""
        super().__init__()
        self.audio_sample = None
        self.play_control = PlayControl()
        self.hbox = None
        self.max_available_slices = "..."
        self.initUI()
        self.key_to_slice_map = {key: i for i, key in enumerate("asdfghjkl")}
        
    def initUI(self):
        """
        Sets up the user interface for the audio sample slicer and editor.
        """
        
        self.resize(720, 490)

        layout = QVBoxLayout()

        # Input field for specifying the number of initial slices
        self.num_slices_input = QLineEdit(self)
        self.num_slices_input.setPlaceholderText("Number of Slices (1-9)")
        self.num_slices_input.setValidator(QIntValidator())  # Only allow integer input
        self.num_slices_input.setFixedWidth(self.num_slices_input.fontMetrics().boundingRect("Number of Slices (1-9)").width() + 10)

        # Button for uploading an audio file
        upload_button = QPushButton("Load Audio File (*.mp3, *.wav)", self)
        upload_button.setFixedWidth(250)
        upload_button.clicked.connect(self.upload_file)

        # Create a widget for the logo
        logo_widget = QWidget(self)
        logo_layout = QVBoxLayout(logo_widget)
        logo_image = QLabel(logo_widget)
        logo_pixmap = QPixmap("img/logo.png")
        logo_image.setPixmap(logo_pixmap)
        logo_layout.addWidget(logo_image, alignment=Qt.AlignRight)

        # Create a horizontal layout for the "Number of Slices" input and "Upload" button
        top_layout = QHBoxLayout()
        # top_layout.addStretch(1)
        top_layout.addWidget(logo_widget, alignment=Qt.AlignLeft)
        top_layout.addWidget(self.num_slices_input, alignment=Qt.AlignRight)
        top_layout.addWidget(upload_button)

        
        # Add the horizontal layout to the main layout
        layout.addLayout(top_layout)

        # Layout for slice adjustments
        self.slice_index_input = QLineEdit(self)
        placeholder_text = f"1 - {self.max_available_slices}"
        self.slice_index_input.setPlaceholderText(placeholder_text)
        self.start_adjust_input = QLineEdit(self)
        self.start_adjust_input.setPlaceholderText("delta")
        self.end_adjust_input = QLineEdit(self)
        self.end_adjust_input.setPlaceholderText("delta")
        self.pitch_shift_input = QLineEdit(self)
        self.pitch_shift_input.setPlaceholderText("delta")
        self.adjust_button = QPushButton('Adjust Slice', self)
        self.adjust_button.clicked.connect(self.adjust_slice)
        self.slice_index_input.setFocusPolicy(Qt.ClickFocus)

        # Disable inputs and button until an audio file is loaded
        self.disable_all_inputs()

        # Create a horizontal layout for the inputs
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

        # Table to display the audio slices
        self.slices_table = self.setup_slices_table()
        layout.addWidget(self.slices_table)

        layout.addLayout(hbox)
        self.setLayout(layout)
        self.setWindowTitle('Audio Sample Slicer & Slice Editor')
        self.show()

    def setup_slices_table(self):
        """
        Creates and configures the table for displaying audio slice information.

        Returns:
            QTableWidget: The configured table widget.
        """
        table = QTableWidget(self)
        table.setColumnCount(4)  # Columns for Playback Key, Start, End, Pitch Shift
        table.setHorizontalHeaderLabels(['Playback Key', 'Start (ms)', 'End (ms)', 'Pitch Shift'])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setFocusPolicy(Qt.NoFocus)
        table.setSelectionMode(QTableWidget.NoSelection)
        return table

    def update_slices_table(self):
        """
        Updates the table with the current slice information from the audio sample.
        """
        self.slices_table.setRowCount(len(self.audio_sample.slices))
        for i, slice_info in enumerate(self.audio_sample.slices):
            # Create table items with slice details
            playback_key_item = QTableWidgetItem("asdfghjkl"[i] if i < len("asdfghjkl") else "N/A")
            start_item = QTableWidgetItem(str(slice_info['start']))
            end_item = QTableWidgetItem(str(slice_info['end']))
            pitch_shift_item = QTableWidgetItem(str(slice_info['pitch_shift']))

            # Disable editing for the table items
            for item in (playback_key_item, start_item, end_item, pitch_shift_item):
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            
            # Add the items to their respective cells in the table
            self.slices_table.setItem(i, 0, playback_key_item)
            self.slices_table.setItem(i, 1, start_item)
            self.slices_table.setItem(i, 2, end_item)
            self.slices_table.setItem(i, 3, pitch_shift_item)

    def enable_all_inputs(self):
        """
        Enables all input fields and the adjust button.
        """
        self.slice_index_input.setEnabled(True)
        self.start_adjust_input.setEnabled(True)
        self.end_adjust_input.setEnabled(True)
        self.pitch_shift_input.setEnabled(True)
        self.adjust_button.setEnabled(True)

    def disable_all_inputs(self):
        """
        Disables all input fields and the adjust button.
        """
        self.slice_index_input.setEnabled(False)
        self.start_adjust_input.setEnabled(False)
        self.end_adjust_input.setEnabled(False)
        self.pitch_shift_input.setEnabled(False)
        self.adjust_button.setEnabled(False)

    def load_audio_sample(self, file_path):
        """
        Loads an audio sample and creates slices based on the specified number.

        Parameters:
            file_path (str): Path to the audio file to load.
        """
        num_slices_text = self.num_slices_input.text()

        if not num_slices_text:
            self.show_error_message("Error", "Please enter the number of initial slices.")
            return

        try:
            num_slices = int(num_slices_text)
            if num_slices <= 0:
                raise ValueError("Number of slices must be greater than 0.")
            self.max_available_slices = num_slices
            placeholder_text = f"1 - {self.max_available_slices}"
            self.slice_index_input.setPlaceholderText(placeholder_text)
        except ValueError as e:
            self.show_error_message("Error", str(e))
            return

        # Load the audio sample and create slices based on the specified number
        self.audio_sample = AudioSample(file_path)
        self.audio_sample.create_slices(num_slices)

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
        except ValueError:
            self.show_error_message("Error", "Start Adjust must be an integer.")
            return

        # Validate and convert the end adjust input, if provided
        try:
            end_adjust = int(end_adjust_text) if end_adjust_text else None
        except ValueError:
            self.show_error_message("Error", "End Adjust must be an integer.")
            return

        # Validate and convert the pitch shift input, if provided
        try:
            pitch_shift = int(pitch_shift_text) if pitch_shift_text else None
        except ValueError:
            self.show_error_message("Error", "Pitch Shift must be an integer.")
            return

        # If all inputs are valid, apply the adjustments to the audio slice
        try:
            self.audio_sample.adjust_slice(slice_index, start_adjust, end_adjust, pitch_shift)
        except ValueError as e:
            self.show_error_message("Error", str(e))

        # Clear the input fields and update the slices table to reflect the changes
        self.clear_slice_adjust_inputs()
        self.update_slices_table()

    def show_error_message(self, title, message):
        """
        Displays an error message box.

        Parameters:
            title (str): The title of the message box.
            message (str): The error message to display.
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec_()

    def clear_slice_adjust_inputs(self):
        """
        Clears all the input fields for slice adjustments.
        """
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
        """
        Opens a file dialog to select and upload an audio file, copying it to a local directory.
        """
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "", "Audio Files (*.mp3 *.wav)", options=options)
        
        if fileName:
            num_slices_text = self.num_slices_input.text()

            # Check if the "Number of Slices" input is empty
            if not num_slices_text:
                self.show_error_message("Error", "Please enter the number of initial slices.")
                return

            try:
                num_slices = int(num_slices_text)

                # Check if the number of slices is within the range from 1 to 9
                if not (1 <= num_slices <= 9):
                    self.show_error_message("Error", "Number of slices must be between 1 and 9.")
                    return
            except ValueError as e:
                self.show_error_message("Error", "Number of slices must be an integer.")
                return

            upload_folder = 'upload'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            shutil.copy(fileName, os.path.join(upload_folder, os.path.basename(fileName)))
            print(f"File uploaded to {upload_folder}")

            self.load_audio_sample(os.path.join(upload_folder, os.path.basename(fileName)))

            
            # Remove focus and deactivate the "Number of Slices" input field after upload
            self.num_slices_input.clearFocus()
            # self.num_slices_input.setReadOnly(True)

    def keyPressEvent(self, event):
        """
        Handles key press events for slice playback.

        Parameters:
            event (QKeyEvent): The key event to handle.
        """
        if self.slice_index_input.hasFocus():
            super().keyPressEvent(event)
        else:
            key = event.text()
            if key in self.key_to_slice_map and self.audio_sample:
                slice_index = self.key_to_slice_map[key]
                
                # Check if the slice index is within the range of the selected number of slices
                if slice_index < len(self.audio_sample.slices):
                    self.play_control.play(self.audio_sample, slice_index)                    
