import serial
import threading
import time 
import csv 
import datetime
import logging 

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
    
class CSVwriter:#this is the class where csv files are made and stored 

    def __init__(self, filename_prefix, sr_no_limit):
        self.filename_prefix =  filename_prefix
        self.file_index = 1
        self.sr_no_limit = sr_no_limit
        self.current_sr_no = 0
        self.open_new_file()

    def open_new_file(self):  #logic to open new file 
        timestamp = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
        self.filename = f"{self.filename_prefix}_{timestamp}.csv"
        self.file = open(self.filename , mode ='w', newline = '')
        self.writer = csv.DictWriter(self.file, fieldnames= ['sr_no','X','Y','Z']) #used to write header in csv file
        self.writer.writeheader()

    def save_data(self, data_point):
        try:
            sr_no = int(data_point['sr_no'])
        except ValueError:
            logger.error(f"Invalid sr_no value: {data_point['sr_no']} - Skipping this data point.")
            return
        self.writer.writerow(data_point)
        self.current_sr_no = sr_no

        if self.current_sr_no >= self.sr_no_limit:
            self.close()
            self.file_index += 1
            self.open_new_file()

    def close(self):
        self.file.close()
              
class SensorDataReader:  #this calss is used to get the data from sensor data 
    def __init__(self, port, baud_rate,queue_size,csv_filename_prefix,sr_no_limit):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = serial.Serial(self.port, self.baud_rate)
        self.data_queue = MyCircularQueue(queue_size)
        self.lock = threading.Lock()
        self.csv_writer = CSVwriter(csv_filename_prefix,sr_no_limit)
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
    
