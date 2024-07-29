import serial
import threading

class SensorDataReader:
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = serial.Serial(self.port, self.baud_rate)
        self.data = None
        self.lock = threading.Lock()
        self.read_thread = threading.Thread(target=self.read_data)
        self.read_thread.start()

    def read_data(self):
        while True:
            if self.serial_connection.in_waiting > 0:
                data_line = self.serial_connection.readline().decode('utf-8')
                with self.lock:
                    self.data = data_line

    def get_data(self):
        with self.lock:
            return self.data
