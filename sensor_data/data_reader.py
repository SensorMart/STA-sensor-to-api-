import serial
import threading
import time 
import csv 
import datetime
import logging 
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class listNode:
     def __init__(self, val, nxt, prev):
        self.val = val
        self.next = nxt  #it is the starting pointer of circular queue 
        self.prev = prev #it is the end pointer of the circular queue

class MyCircularQueue:  #this si the class for circular queue logic

    def __init__(self, k: int) : #initialise the   object with the size of queue to be k
            self.space =k #space that is left
            self.left = listNode(0, None , None)
            self.right =listNode(0,None,self.left)
            self.left.next = self.right

    def enQueue(self,value: int) -> bool: #inserts the element into circular queue. return true if the operation  is true
        if self.space == 0: return False #checks the queue has space or not to store other data points
        cur = listNode(value , self.right, self.right.prev)
        self.right.prev.next = cur 
        self.right.prev = cur
        self.space -= 1
        return True
    
    def deQueue(self) -> bool:#delete the elemen t from circular queue , return true if operation is sucessful
        if self.isEmpty(): return False # to make sure it is nbot empty
        self.left.next = self.left.next.next
        self.left.next.prev = self.left
        self.space += 1
        return True
    
    def Front(self) -> int: #get the front item from the queue if the queue is empty , return -1
        if self.isEmpty(): return -1
        return self.left.next.val

    def Rear(self) -> int: #get the last item from the queue .if the queue is empty return -1
         if self.isEmpty(): return -1
         return self.right.prev.val

    def isEmpty(self) -> bool:  #check wether circulaar queue is empty or not 
        return  self.left.next == self.right
    
    def isFull(self) -> bool: #check wether the circular queue is full or not 
         return self.space == 0

class LogWriter:

    def __init__(self,log_filename ="log.csv"):
        self.log_folder ="log"
        self.log_filename = os.path.join(self.log_folder,log_filename)
        self.index_no = 1  
        self.ensure_log_file_exist()
        self.initialize_log_file()

    def ensure_log_file_exist(self):
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)

    def initialize_log_file(self):
        if not os.path.exists(self.log_filename):
            with open(self.log_filename,mode = 'w', newline='') as log_file:
                writer = csv.DictWriter(log_file,fieldnames=['index_no','file_name','time_of_creation'])
                writer.writeheader()

    def log_file_creation(self, file_name):
        time_of_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_filename,mode='a',newline='') as log_file:
            writer = csv.DictWriter(log_file,fieldnames=['index_no','file_name','time_of_creation']) 
            writer.writerow({
                'index_no': self.index_no,
                'file_name': file_name,
                'time_of_creation': time_of_creation,
            })
        self.index_no += 1


class CSVwriter:#this is the class where csv files are made and stored 

    def __init__(self, filename_prefix, sr_no_limit,log_writer):
        self.filename_prefix =  filename_prefix
        self.file_index = 1
        self.sr_no_limit = sr_no_limit
        self.current_sr_no = 0
        self.current_date = datetime.now().strftime("%d-%m-%Y")
        self.base_folder = "data"
        self.log_writer = log_writer
        self.ensure_base_folder_exists()
        self.open_new_file()

    def ensure_base_folder_exists(self): #make shure base folder exist if not make it
        if not os.path.exists(self.base_folder):
            os.makedirs(self.base_folder)

    def open_new_file(self):  #logic to open new file 
        new_date = datetime.now().strftime("%d-%m-%Y")# check if the date has changed or not
        if new_date != self.current_date:
            self.current_date = new_date
            self.file_index = 1 #reset the file index for new date

            #create the folder for current data if it do not exist of date
            date_folder = os.path.join(self.base_folder,self.current_date)
            if not os.path.exists(date_folder):
                os.makedirs(date_folder)

        #generate the new file name with date and time 
        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        self.filename = f"{timestamp}.csv"  #file name is deciced by this line 

        self.file = open(self.filename , mode ='w', newline = '')
        self.writer = csv.DictWriter(self.file, fieldnames= ['sr_no','X','Y','Z']) #used to write header in csv file
        self.writer.writeheader()
        self.log_writer.log_file_creation(self.filename,0)

    def save_data(self, data_point):
        try:
            sr_no = int(data_point['sr_no'])
        except ValueError:
            logger.error(f"Invalid sr_no value: {data_point['sr_no']} - Skipping this data point.")
            return
        
        self.writer.writerow(data_point)
        self.current_sr_no = sr_no

        if self.current_sr_no >= self.sr_no_limit:
            self.close() #close current file and log its creation
            self.file_index += 1
            self.open_new_file()

    def close(self):
        self.file.close()
        self.log_writer.log_file_creation(self.filename, self.current_sr_no)

class SensorDataReader:  #this class is used to get the data from sensor data 
    def __init__(self, port, baud_rate,queue_size,csv_filename_prefix,sr_no_limit,log_writer):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = serial.Serial(self.port, self.baud_rate)
        self.data_queue = MyCircularQueue(queue_size)
        self.lock = threading.Lock()
        log_writer = LogWriter()#initialise log writer
        self.csv_writer = CSVwriter(csv_filename_prefix,sr_no_limit,log_writer)
        self.read_thread = threading.Thread(target=self.read_data)
        self.read_thread.start()

    def read_data(self):
        while True:
            if self.serial_connection.in_waiting > 0: #initiate serial connection 
                data_line = self.serial_connection.readline().decode('utf-8', errors = 'replace').strip() #reads the data decode it and remove the errors in linme if present 
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
                    if self.data_queue.isFull():
                         self.data_queue.deQueue()
                    self.data_queue.enQueue(data_point)  #store the data points in the circular queue
                self.csv_writer.save_data(data_point) #calls the csv function to save the data in csv file
            time.sleep(0.005)

    def get_data(self):
        with self.lock:
            data_list = [] # empy queue is initated where data points will be stored 
            current  = self.data_queue.left.next 
            while current != self.data_queue.right:
                data_list.append(current.val) #append the data points in the queue
                current = current.next
            return data_list
    
    def stop(self):
        self.csv_writer.close()
        self.read_thread.join()
    
