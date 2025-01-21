import subprocess
import time
import os
import sys
from threading import Timer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import DataSet

configurations = DataSet.get_schema(os.path.join('..', 'runtimeConfigurations.json'))

def run_in_terminal(script_name, *args):
    command = ["start", "cmd", "/k", "python", script_name] + list(args)
    subprocess.Popen(command, shell=True)

def data_requesters():
    #run_in_terminal("CPReceiver.py")
    #time.sleep(1)
    #run_in_terminal("CPProducer.py")
    run_in_terminal("CWReceiver.py")
    run_in_terminal("ICReceiver.py")
    #time.sleep(1)
    #run_in_terminal("ICProducer.py")
    run_in_terminal("ICRuntimeRequest.py")

def start_servers():
    time_interval = DataSet.calculate_interval(configurations.get('frequency'))
    time_interval -= time_interval*0.2
    run_in_terminal("DataReceiver.py","MessageAggregator.MessageAggregator")
    #time.sleep(1)
    #run_in_terminal("DataReceiver.py","AlgorithmReceiver.AlgorithmReceiver")
    Timer(time_interval,data_requesters).start() 

start_servers()
