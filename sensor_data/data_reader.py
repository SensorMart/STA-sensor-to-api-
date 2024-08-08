import serial
import threading
import time 
from queue import Queue
import csv 

class listNode:
     def __init__(self, val, nxt, prev):
        self.val = val
        self.next = nxt
        self.prev = prev

class MyCircularQueue:
    def __init__(self, k: int) : #initialise the   object with the size of queue to be k
            self.space =k #space that is left
            self.left = listNode(0, None , None)
            self.right =listNode(0,None,self.left)
            self.left.next = self.right

    def enQueue(self,value: int) -> bool: #inserts the element into circular queue. return true if the operation  is true
        if self.space == 0: return False
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
    
class CSVwriter:
    def __init__(self, filename_prefix):

        self.filename_prefix =  filename_prefix
        self.file_index = 1
        self.record_count = 0
        self.max_records = 3000
        self.open_new_file()

    def open_new_file(self):
        self.filename = f"{self.filename_prefix}_{self.file_index}.csv"
        self.file = open(self.filename , mode ='w', newline = '')
        self.writer = csv.DictWriter(self.file, fieldnames= ['sr_no','X','Y','Z'])
        self.writer.writeheader()

    def save_data(self, data_point):
        self.writer.writerow(data_point)
        self.record_count += 1
        if self.record_count >= self.max_records:
            self.close()
            self.file_index += 1
            self.record_count = 0
            self.open_new_file()

    def close(self):
        self.file.close()

              
class SensorDataReader:
    def __init__(self, port, baud_rate,queue_size,csv_filename_prefix):
        self.port = port
        self.baud_rate = baud_rate
        self.serial_connection = serial.Serial(self.port, self.baud_rate)
        self.data_queue = MyCircularQueue(queue_size)
        self.lock = threading.Lock()
        self.csv_writer = CSVwriter(csv_filename_prefix)
        self.read_thread = threading.Thread(target=self.read_data)
        self.read_thread.start()

    def read_data(self):
        while True:
            if self.serial_connection.in_waiting > 0:
                
                data_line = self.serial_connection.readline().decode('utf-8', errors = 'replace').strip()
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
                    self.data_queue.enQueue(data_point)
                self.csv_writer.save_data(data_point)
            time.sleep(0.005)

    def get_data(self):
        with self.lock:
            data_list = []
            current  = self.data_queue.left.next
            while current != self.data_queue.right:
                data_list.append(current.val)
                # csv_writer.save_data(data_list)
                current = current.next
            return data_list
    
    def stop(self):
        self.csv_writer.close()
        self.read_thread.join()
