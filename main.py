

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
from PyQt5.QtWidgets import QApplication, QFileDialog
import pandas as pd
import pyqtgraph as pg
import random  # Import the random module to add noise
import sys
import numpy as np
from os import path

# Load the UI file and connect it with the Python file
FORM_CLASS, _ = loadUiType(path.join(path.dirname(__file__), "main.ui"))

class MainApp(QMainWindow, FORM_CLASS):
    def __init__(self, parent=None):
        """
        Constructor to initiate the main window in the design.

        Parameters:
        - parent: The parent widget, which is typically None for the main window.
        """
        super(MainApp, self).__init__(parent)
        self.setupUi(self)

        # Configure graph view settings
        self.graphicsView.setBackground('w')
        self.graphicsView_2.setBackground('w')
        self.graphicsView_3.setBackground('w')
        self.graphicsView.setLabel('bottom', 'time')
        self.graphicsView_2.setLabel('bottom', 'time')
        self.graphicsView_3.setLabel('bottom', 'time')

        # Initialize data and settings
        self.signals_data = {}  # Dictionary to store signal data
        self.count_signals = 0  # Counter for the number of signals added
        self.comboBox_fmax.setCurrentIndex(1)
        self.noise_slider.setRange(0, 100)  # Set the noise level range
        self.noise_level = 0  # Initialize the noise level
        self.way_of_plotting_with_add = True  # Flag to determine the signal source
        self.handle_btn()  # Connect UI elements to their handling functions

    def handle_btn(self):
        """
        Connect UI elements to their respective handling functions.
        """
        self.actionOpen_file.triggered.connect(self.add_signal)
        self.mix_signal_btn.triggered.connect(self.open_mixer)
        self.noise_slider.valueChanged.connect(self.update_noise_level)
        self.delete_btn.clicked.connect(self.delete_signal)
        self.freq_slider.valueChanged.connect(self.update_fs)
        self.comboBox_fmax.currentIndexChanged.connect(self.multp_fmax)

    def multp_fmax(self):
        selected_frequency = self.comboBox_fmax.currentText()
        if self.way_of_plotting_with_add:
            fs_max = self.original_fs / 2
        else:
            fs_max = self.mixer.overall_max_frequency
        if selected_frequency == "1x Fmax":
            new_fs = fs_max  # Reset to the original sampling frequency
        elif selected_frequency == "2x Fmax":
            new_fs = fs_max * 2
        elif selected_frequency == "3x Fmax":
            new_fs = fs_max * 3
        elif selected_frequency == "4x Fmax":
            new_fs = fs_max * 4

        # Update the slider position with the nearest integer value
        new_slider_position = round(new_fs)
        self.freq_slider.setSliderPosition(new_slider_position)
        
        # Update the actual value in the slider
        self.freq_slider.setValue(new_slider_position)

        # Update the sampling frequency and re-plot
        self.update_fs(new_fs)

    def open_mixer(self):
        """
        Open the signal mixer window and connect it with the main application.
        """
        if self.signals_data:
            self.delete_signal()
        self.way_of_plotting_with_add = False
        from mixer import MixerApp  # Import the signal mixer module
        self.mixer = MixerApp()  # Create an instance of the MixerApp class
        self.mixer.set_myapp(self)  # Set a reference to the main application
        self.mixer.show()  # Display the mixer window

    def add_signal(self):
        """
        Load a CSV signal file, add it to the application's data, and plot it.
        """
        options = QFileDialog().options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)",
                                                   options=options)
        if file_path:
            if self.signals_data or not self.way_of_plotting_with_add:
                self.delete_signal()
            self.count_signals += 1
            file_name = file_path.split("/")[-1]
            signal_data = pd.read_csv(file_name)
            time_column = signal_data.iloc[:1000, 1]
            values_column = signal_data.iloc[:1000, -1]
            time_values = time_column.tolist()
            v_values = values_column.tolist()
            self.original_fs = int(signal_data["Sampling Freq"][0])
            self.fs = int(signal_data["Sampling Freq"][0])
            self.freq_slider.setRange(int(self.fs / 8), int(self.fs * 4))
            self.freq_slider.setSliderPosition(self.fs)
            self.freq_slider.setValue(self.fs)
            # Making a new item in the dictionary, the new signal is given a key, and the values is given according to its data
            self.signals_data[self.count_signals] = [time_values, v_values, 'Red', f"{'Signal'} - {self.count_signals}"]
            self.comboBox_2.addItem(f"{'Signal'} - {self.count_signals}")
            self.way_of_plotting_with_add = True

        self.plot_graph()

    def plot_graph(self):
        """
        Plot the signals and related graphs.
        """
        self.clear_all()
        if self.way_of_plotting_with_add:
            for value in self.signals_data.values():
                x = value[0]
                y = value[1]
                # Apply noise to 'y' values
                random.seed(0)
                noisy_y = [v + random.uniform(-self.noise_level, self.noise_level) for v in y]
                self.graphicsView.plot(x, noisy_y, pen="r")
                # Set the sampling rate
                sampled_x, sampled_y = self.sample_signal(x, y, self.fs, 0)
                reconstructed_signal = self.sinc_interpolation(sampled_x, sampled_y, self.fs, x)
                self.graphicsView.plot(sampled_x, sampled_y, pen=None, symbol='o', symbolBrush='b')
                reconstruction_pen = pg.mkPen(color=(0, 0, 255))
                self.graphicsView_2.plot(x, reconstructed_signal, pen=reconstruction_pen)


                error = [abs(original - reconstructed) for original, reconstructed in
                         zip(noisy_y, reconstructed_signal)]
                # Filter error values above the threshold
                error_threshold = 0.3
                error_above_threshold = [err if err > error_threshold else 0 for err in error]
                # Plot the error above the threshold
                error_pen = pg.mkPen(color="r")
                self.graphicsView_3.setYRange(0, 2)
                self.graphicsView_3.plot(x, error_above_threshold, pen=error_pen)
                

        else:
            # Apply noise to 'y' values
            random.seed(0)
            noisy_y = [v + random.uniform(-self.noise_level, self.noise_level) for v in self.mixer.syntheticSignal]
            self.graphicsView.setYRange(min(noisy_y), max(noisy_y)) 
            self.graphicsView.setXRange(min(self.mixer.sin_time), max(self.mixer.sin_time))
            self.graphicsView.plot(self.mixer.sin_time, noisy_y, pen=pg.mkPen(color=(255, 0, 0)))
            # Set the sampling rate
            sampled_x, sampled_y = self.sample_signal(self.mixer.sin_time, noisy_y, self.fs, 0.005)
            self.graphicsView.plot(sampled_x, sampled_y, pen=None, symbol='o', symbolBrush='b')
            reconstructed_signal = self.sinc_interpolation(sampled_x, sampled_y, self.fs, self.mixer.sin_time)
            viewbox0 = self.graphicsView.getViewBox()
            viewbox2 = self.graphicsView_2.getViewBox()
            y_range, x_range = viewbox0.viewRange()
            viewbox2.setYRange(x_range[0], x_range[1])
            viewbox2.setYRange(x_range[0], x_range[1])
            self.graphicsView_2.plot(self.mixer.sin_time, reconstructed_signal, pen=pg.mkPen(color=(255, 0, 0)))

            error = [abs(original - reconstructed) for original, reconstructed in
                     zip(noisy_y, reconstructed_signal)]
            # Filter error values above the threshold
            error_threshold = 0.5
            error_above_threshold = [err if err > error_threshold else 0 for err in error]
            # Plot the error above the threshold
            error_pen = pg.mkPen(color="r")
            self.graphicsView_3.setYRange(min(reconstructed_signal),max(reconstructed_signal))
            self.graphicsView_3.plot(self.mixer.sin_time, error_above_threshold, pen=error_pen)
           
        
            
           

    
    def sample_signal(self, original_x, original_y, f_sample, start):
        """
        Sample a signal at specified time intervals.

        Args:
            original_x (array-like): The time (or position) values of the original signal.
            original_y (array-like): The corresponding signal values.
            f_sample (float): The sampling frequency (or sampling rate).
            start (float): The starting time for sampling.

        Returns:
            Tuple: A tuple containing two arrays - the new sample times and the sampled signal values.
        """
        # Calculate the time interval between samples
        time_interval = 1 / f_sample

        # Create a new array of sample times based on the time interval
        new_sample_times = np.arange(start, max(original_x), time_interval)

        # Initialize an array for the sampled signal
        sampled_signal = np.zeros(len(new_sample_times))

        # Sample the signal at the specified times
        for i, t in enumerate(new_sample_times):
            # Find the closest original sample to the current time
            closest_sample_idx = np.argmin(np.abs(original_x - t))
            sampled_signal[i] = original_y[closest_sample_idx]

        return new_sample_times, sampled_signal

    def sinc_interpolation(self, sampled_x, sampled_y, f_sample, new_time_points):
        """
        Reconstruct a signal using sinc interpolation.

        Args:
            sampled_x (array-like): The time (or position) values at which the signal is sampled.
            sampled_y (array-like): The corresponding sampled signal values.
            f_sample (float): The sampling frequency (or sampling rate).
            new_time_points (array-like): The time points at which you want to reconstruct the signal.

        Returns:
            np.array: The reconstructed signal values at new_time_points.
        """
        time_interval = 1 / f_sample
        reconstructed_signal = np.zeros(len(new_time_points))

        for n, sample in enumerate(sampled_y):
            reconstructed_signal += sample * np.sinc((new_time_points - sampled_x[n]) / time_interval)

        return reconstructed_signal

    def clear_all(self):
        """
        Clear all three graphics views used for plotting signals.
        """
        self.graphicsView.clear()
        self.graphicsView_2.clear()
        self.graphicsView_3.clear()

    def update_noise_level(self, value):
        """
        Update the noise level and re-plot the signals with the new noise level.

        Args:
            value (int): The noise level value.
        """
        self.clear_all()

        # Adjust the noise level based on the plotting mode
        if self.way_of_plotting_with_add:
            self.noise_level = value / 100
        else:
            self.noise_level = value / 10

        # Update the noise level label in the UI
        self.nsr_lbl.setText(f"Noise to Signal Ratio {str(self.noise_level)}")

        # Re-plot the signals with the updated noise level
        self.plot_graph()

    def update_fs(self, value):
        """
        Update the sampling frequency and re-plot the signals with the new frequency.

        Args:
            value (int): The new sampling frequency.
        """
        self.fs = value
        self.freq_lbl.setText(f"Sampling frequency is {str(self.fs)}")
        self.plot_graph()

    def reindex_dict_keys(self, dictionary):
        """
        Reindex dictionary keys to start from 1.

        Args:
            dictionary (dict): The input dictionary.

        Returns:
            dict: A dictionary with reindexed keys.
        """
        return {i: value for i, (key, value) in enumerate(dictionary.items(), start=1)}

    def refill_combo_from_dict(self, combo_box, dictionary):
        """
        Refill a combo box with items from a dictionary.

        Args:
            combo_box (QComboBox): The combo box to be refilled.
            dictionary (dict): The dictionary containing items to add to the combo box.
        """
        combo_box.clear()  # Clear the combo box
        combo_box.addItem("Select a Signal")

        # Add items from the dictionary to the combo box
        if self.way_of_plotting_with_add:
            for key in dictionary:
                combo_box.addItem(f"{'Signal'} - {key}")
        else:
            for key in dictionary:
                combo_box.addItem(key)

    def delete_signal(self):
        """
        Delete a selected signal and update the UI.

        Depending on the plotting mode (add or replace), the function deletes the selected signal
        and updates the combo box and signal data accordingly.
        """
        if self.way_of_plotting_with_add:
            selected_item_text = self.comboBox_2.currentText()
            selected_signal_index = int(selected_item_text.split('-')[-1].strip())

            if selected_signal_index in self.signals_data:
                del self.signals_data[selected_signal_index]
                self.count_signals -= 1
                self.comboBox_2.removeItem(self.comboBox_2.currentIndex())
                self.clear_all()
                self.signals_data = self.reindex_dict_keys(self.signals_data)
                self.refill_combo_from_dict(self.comboBox_2, self.signals_data)
        else:
            if self.mixer.sinusoidals:
                selected_item_text = self.comboBox_2.currentText()
                # Use del to delete the key from the dictionary
                del self.mixer.sinusoidals[selected_item_text]
                self.comboBox_2.removeItem(self.comboBox_2.currentIndex() - 1)
                self.clear_all()
                self.signals_data = self.reindex_dict_keys(self.mixer.sinusoidals)
                self.refill_combo_from_dict(self.comboBox_2, self.mixer.sinusoidals)
                self.mixer.sumSignals()
                if not self.mixer.sinusoidals : 
                    self.way_of_plotting_with_add = True
        self.plot_graph()


def main():  # method to start app
        app = QApplication(sys.argv)
        window = MainApp()
        window.show()
        app.exec_()  # infinte Loop

if __name__ == '__main__':
     main()
