import subprocess
import os
from threading import Timer
from utils.data import DataSet
configurations = DataSet.get_schema('./configs/runtimeConfigurations.json')
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)


def run_in_terminal_windows(script_name, *args):
    command = [
                  "start",
                  "cmd",
                  "/k",
                  f"cd /d {parent_dir} && python -m runtime.{script_name}"
              ] + list(args)

    subprocess.Popen(command, shell=True)

def run_in_terminal_linux(script_name, *args):
    command = [
        "nohup", "python3", "-m", f"runtime.{script_name}", *args, "&"
    ]
    subprocess.run(command, shell=False)

def data_requesters():
    #run_in_terminal("PCReceiver.py")
    #time.sleep(1)
    #run_in_terminal("PCProducer.py")
    run_in_terminal_linux("CWReceiver")
    run_in_terminal_linux("ICReceiver")
    #time.sleep(1)
    #run_in_terminal("ICProducer.py")
    run_in_terminal_linux("ICRuntimeRequest")
    print("Data Requesters started!")

def start_servers():
    time_interval = DataSet.calculate_interval(configurations.get('frequency'))
    time_interval -= time_interval*0.5
    run_in_terminal_linux("Accumulator")
    Timer(time_interval,data_requesters).start()

start_servers()
