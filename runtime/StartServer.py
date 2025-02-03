import subprocess
import os
from threading import Timer
from utils.data import DataSet

configurations = DataSet.get_schema('./configs/runtimeConfigurations.json')
base_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(base_dir)

def run_in_terminal(script_name, *args):
    # Obtém o diretório base onde o projeto está localizado
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Garante que o comando será executado no diretório correto
    command = [
                  "start",
                  "cmd",
                  "/k",
                  f"cd /d {parent_dir} && python -m runtime.{script_name}"
              ] + list(args)

    # Executa o subprocesso
    subprocess.Popen(command, shell=True)


def data_requesters():
    #run_in_terminal("CPReceiver.py")
    #time.sleep(1)
    #run_in_terminal("CPProducer.py")
    run_in_terminal("CWReceiver")
    run_in_terminal("ICReceiver")
    #time.sleep(1)
    #run_in_terminal("ICProducer.py")
    run_in_terminal("ICRuntimeRequest")

def start_servers():
    time_interval = DataSet.calculate_interval(configurations.get('frequency'))
    time_interval -= time_interval*0.5
    run_in_terminal("Accumulator")
    Timer(time_interval,data_requesters).start()

start_servers()
