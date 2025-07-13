import os
import signal
import psutil

def kill_python_processes():
    """
    Terminate all Python processes that might be locking the ChromaDB file.
    """
    current_pid = os.getpid()
    killed = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Skip the current process
            if proc.pid == current_pid:
                continue
                
            # Check if this is a Python process
            if proc.info['name'] is not None and 'python' in proc.info['name'].lower():
                # Skip if this is the current process
                if any('kill_python_processes.py' in cmd for cmd in (proc.info['cmdline'] or [])):
                    continue
                    
                print(f"Terminating Python process (PID: {proc.pid}) - {proc.info}")
                proc.terminate()
                killed += 1
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    print(f"Terminated {killed} Python processes.")
    return killed

if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("Installing psutil...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
        import psutil
    
    kill_python_processes()
