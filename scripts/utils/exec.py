import subprocess

def execute(command):
    if isinstance(command, str):
        process = subprocess.Popen(command.split(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1, universal_newlines=True)
    elif isinstance(command, list):
        process = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=1, universal_newlines=True)
    else:
        return
    for line in process.stdout:
      yield line

def execute_with_output(command):
    if isinstance(command, str):
        process = subprocess.Popen(command.split(),stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    elif isinstance(command, list):
        process = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    else:
        return
    out,err = process.communicate()
    return out,err

def check_execution(command):
    try:
        if isinstance(command, str):
            subprocess.run(command.split(), check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        elif isinstance(command, list):
            subprocess.run(command, check=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        else:
            return False
        return True
    except:
        return False
