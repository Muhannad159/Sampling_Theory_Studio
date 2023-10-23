from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import loadUiType
from UliEngineering.SignalProcessing.Simulation import sine_wave
import os
import sys
from os import path
import numpy as np
import pyqtgraph as pg

FORM_CLASS, _ = loadUiType(path.join(path.dirname(__file__), "mixer.ui"))  # connects the Ui file with the Python file


class MixerApp(QDialog, FORM_CLASS):  # go to the main window in the form_class file

    def __init__(self, parent=None):  # constructor to initiate the main window  in the design
        super(MixerApp, self).__init__(parent)
        self.setupUi(self)
        self.handle_btn()
        self.sin_time = np.linspace(0, 2, 1000) 
        self.sinusoidals = [] 
        self.sin_names = []
        self.sin_graphics_view.setBackground('w')

    def handle_btn(self):
          self.plot_push_btn.clicked.connect(self.construct_signal)

    def construct_signal(self):
        self.sin_frequency = float(self.signalFrequency.text())
        self.sin_magnitude = float(self.signalMagnitude.text())
        self.sin_phase = float(self.signalPhase.text())
        self.sin_name = self.signalName.text()
        self.sinusoidal = sine_wave(frequency=self.sin_frequency, samplerate=len(
         self.sin_time), amplitude=self.sin_magnitude, phaseshift=self.sin_phase)
        self.sinusoidals.append(self.sinusoidal)
        self.sin_names.append(self.sin_name)
        self.drawSyntheticSignal()
       
    
    def drawSyntheticSignal(self):
        self.syntheticSignal = [0]*self.sin_time
        for sinusoidal in self.sinusoidals:
            self.syntheticSignal += sinusoidal
        self.sin_graphics_view.clear()
        self.sin_graphics_view.plot(self.sin_time, self.syntheticSignal, pen=pg.mkPen(color=(255, 0, 0)))
       



 

def main():  # method to start app
        app = QApplication(sys.argv)
        window = MixerApp()
        window.show()
        app.exec_()  # infinte Loop

if __name__ == '__main__':
        main()