import subprocess

def run_in_terminal(script_name, *args):
    command = ["start", "cmd", "/k", "python", script_name] + list(args)
    subprocess.Popen(command, shell=True)

def start_servers():
    run_in_terminal("CWHistoricDataRequest.py", "2023-09-15T00:00:00+0000", "2024-10-28T00:00:00+0000","60")
    run_in_terminal("Accumulator.py")
    

start_servers()
