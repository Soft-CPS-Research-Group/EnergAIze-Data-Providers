import os
import time
import multiprocessing
from utils.data import DataSet

configurations = DataSet.get_schema('./configs/runtimeConfigurations.json')
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)

def run_script(script_name):
    os.system(f"python -m runtime.{script_name}")

def data_requesters():
    processes = [
        multiprocessing.Process(target=run_script, args=("CWReceiver",)),
        multiprocessing.Process(target=run_script, args=("ICReceiver",)),
        multiprocessing.Process(target=run_script, args=("PCReceiver",)),
        multiprocessing.Process(target=run_script, args=("ICRuntimeRequest",))
        #multiprocessing.Process(target=run_script, args=("PCRuntimeRequest",))
    ]

    for process in processes:
        process.start()

    print("Data Requesters started!")

def start_servers():
    time_interval = DataSet.calculate_interval(configurations.get('frequency'))
    time_interval -= time_interval * 0.5

    accumulator_process = multiprocessing.Process(target=run_script, args=("Accumulator",))
    accumulator_process.start()
    time.sleep(time_interval)
    data_requesters()

    accumulator_process.join()

if __name__ == "__main__":
    multiprocessing.set_start_method('fork')
    start_servers()
