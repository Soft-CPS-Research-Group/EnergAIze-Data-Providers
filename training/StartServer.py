import time
import os
import multiprocessing

def run_script(script_name, start_date=None, end_date=None, period=None):
    if start_date and end_date and period:
        os.system(f"python -m training.{script_name} {start_date} {end_date} {period}")
    else:
        os.system(f"python -m training.{script_name}")

def start_servers():
    '''startDate = "2023-09-15T00:00:00+0000"
    endDate = "2024-10-28T00:00:00+0000"'''
    startDate = "2025-03-25T00:00:00+0000"
    endDate = "2025-04-25T00:00:00+0000"
    period = "15"
    time.sleep(1)
    #run_in_terminal("ICHistoricDataRequest.py", startDate, endDate, period)
    multiprocessing.Process(target=run_script, args=("CWHistoricDataRequest",startDate,endDate,period,)).start()
    accumulator_process = multiprocessing.Process(target=run_script, args=("Accumulator",))
    accumulator_process.start()

    accumulator_process.join()

if __name__ == "__main__":
    multiprocessing.set_start_method('fork')
    start_servers()
