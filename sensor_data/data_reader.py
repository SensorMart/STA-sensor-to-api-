import serial
import threading
import json

class SensorDataReader:
    def __init__(self, port, baud_rate):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = serial.Serial(self.port, self.baud_rate)
        self.data = []
        self.lock = threading.Lock()
        self.read_thread = threading.Thread(target=self.read_data)
        self.read_thread.start()

    def read_data(self):
        while True:
            if self.serial_connection.in_waiting > 0:
                
                data_line = self.serial_connection.readline().decode('utf-8')
                #spliting data in srno,x,y,z
                part = data_line.split(',')
                if len(part) == 4:
                    data_point = {
                        "sr_no": part[0],
                        "X":part[1],
                        "Y":part[2],
                        "Z":part[3]
                    }
                    #to store the data in list
                with self.lock:
                    self.data.append(data_point)
                    #set the limit of ther list
                    if len(self.data)>1000:
                        self.data.pop(0)

    def get_data(self):
        with self.lock:
            return self.data