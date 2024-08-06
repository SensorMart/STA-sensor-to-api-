import csv
from threading import Lock

class CSVwriter:
    def __init__(self, file_prefix= 'DATA' , max_points = 30000):
        self.file_prefix = file_prefix
        self.max_points = max_points
        self.file_index = 0
        self.current_serial_number = 0
        self.file_name  = self.get_file_name()
        self.file = open(self.file_name, 'w', newline='')
        self.writer = csv.DictWriter(self.file, fieldnames= ['sr_no','X','Y','Z'])
        self.writer.writeheader()
        self.lock = Lock()

    def get_file_name(self):
        return f"{self.file_prefix}_{self.file_index}.csv"
    
    def save_data(self, data_point):
        with self.lock:
            serial_number = int(data_point['sr_no'])

            if serial_number >self.current_serial_number + self.max_points: #if serial number exceed 
                self.file.close()
                self.file_index += 1
                self.current_serial_number = serial_number
                self.file_name = self.get_file_name()
                self.file = open(self.file_name, 'w' , newline='')
                self.writer = csv.DictWriter(self.file, fieldnames=['sr_no','X','Y','Z'])
                self.writer.writeheader()
            
            self.writer.writerow(data_point)