import subprocess
import os
from threading import Timer
from utils.data import DataSet

configurations = DataSet.get_schema('./configs/runtimeConfigurations.json')

def run_in_terminal(script_name, *args):
    command = ["start", "cmd", "/k", "python", "-m", script_name] + list(args)
    subprocess.Popen(command, shell=True)

def data_requesters():
    #run_in_terminal("CPReceiver.py")
    #time.sleep(1)
    #run_in_terminal("CPProducer.py")
    run_in_terminal("runtime.CWReceiver")
    run_in_terminal("runtime.ICReceiver")
    #time.sleep(1)
    #run_in_terminal("ICProducer.py")
    run_in_terminal("runtime.ICRuntimeRequest")

def start_servers():
    time_interval = DataSet.calculate_interval(configurations.get('frequency'))
    time_interval -= time_interval*0.7
    run_in_terminal("runtime.Accumulator")
    Timer(time_interval,data_requesters).start()

start_servers()