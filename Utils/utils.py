import requests
import threading
import concurrent.futures
from PyQt5.QtCore import *
from multiprocessing import Manager


def get_data(product_url, i, shared_dict):
    response = requests.get(product_url, timeout=10)
    if response.status_code == 200:
        product_data = response.json()
        shared_dict[i] = product_data
        WorkWithReq.for_progress_bar.emit(int((len(shared_dict) / WorkWithReq.num_products) * 100))


def my_func(base_url, start, last, shared_dict):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        works = [
            executor.submit(get_data, f"{base_url}/{i}", i, shared_dict) for i in range(start + 1, last + 1)
            
        ]
        works.append(executor.submit(WorkWithReq.progres_bar, shared_dict))
        concurrent.futures.wait(works)

class WorkWithReq(QObject):
    for_progress_bar = pyqtSignal(int)
    results = pyqtSignal(dict)

    def __init__(self, resource, num_products):
        super(WorkWithReq, self).__init__()
        self.base_url = resource
        self.num_products = num_products
        self.num_range = int(self.num_products / 5)
        self.data = {}
         
    def get_data_without(self, product_url, i):
        response = requests.get(product_url, timeout=10)
        if response.status_code == 200:
            product_data = response.json()
            self.data[i] = product_data
            progress_percentage = int((len(self.data) / self.num_products) * 100)
            self.for_progress_bar.emit(progress_percentage)
        
    def progres_bar(self, shared_dict):
        print(len(self.all_data))
        while len(shared_dict) != self.num_products:
            self.for_progress_bar.emit(int((len(shared_dict) / self.num_products) * 100))

    def run_with_concurrent_futures(self):
        manager = Manager()
        self.all_data = manager.dict()

        with concurrent.futures.ProcessPoolExecutor(max_workers= 5) as process_executor:
            futures = [
                process_executor.submit(my_func, self.base_url, 0, self.num_range, self.all_data),
                process_executor.submit(my_func, self.base_url, self.num_range, 2 * self.num_range, self.all_data),
                process_executor.submit(my_func, self.base_url, 2 * self.num_range, 3 * self.num_range, self.all_data),
                process_executor.submit(my_func, self.base_url, 3 * self.num_range, 4 * self.num_range, self.all_data),
                process_executor.submit(my_func, self.base_url, 4 * self.num_range, self.num_products, self.all_data)
            ]
            # self.for_progress_bar.emit(int((len(self.all_data) / self.num_products) * 100))
        concurrent.futures.wait(futures)

        self.results.emit(dict(self.all_data))

    def run_with_threading(self):
        threads = []
        for i in range(1, self.num_products + 1):
            thread = threading.Thread(target=self.get_data_without, args=(f"{self.base_url}/{i}", i,))
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
        self.results.emit(self.data)
            

    def run_without_threads(self):
        for i in range(1, self.num_products + 1):
            self.get_data_without(f"{self.base_url}/{i}", i)
        self.results.emit(self.data)
