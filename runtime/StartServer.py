import subprocess
import time

def run_in_terminal(script_name, *args):
    command = ["start", "cmd", "/k", "python", script_name] + list(args)
    subprocess.Popen(command, shell=True)

def start_servers():
    run_in_terminal("ICProducer.py")
    time.sleep(1)
    run_in_terminal("ICReceiver.py")
    time.sleep(1)
    run_in_terminal("CWReceiver.py")
    time.sleep(1)
    run_in_terminal("DataReceiver.py","MessageAggregator.MessageAggregator")
    time.sleep(1)
    run_in_terminal("DataReceiver.py","AlgorithmReceiver.AlgorithmReceiver")
start_servers()
