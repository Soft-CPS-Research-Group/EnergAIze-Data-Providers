import subprocess
import time

def run_in_terminal(script_name, *args):
    command = ["start", "cmd", "/k", "python", script_name] + list(args)
    subprocess.Popen(command, shell=True)

def start_servers():
    startDate = "2023-09-15T00:00:00+0000"
    endDate = "2024-10-28T00:00:00+0000"
    period = "60"
    run_in_terminal("ICHistoricDataProducer.py")
    time.sleep(1)
    run_in_terminal("ICHistoricDataRequest.py", startDate, endDate, period)
    run_in_terminal("CWHistoricDataRequest.py", startDate, endDate, period)
    run_in_terminal("Accumulator.py")
    

start_servers()
