import subprocess, psutil, os

try:
    from mt5lp import mt5utils
except ImportError:
    import mt5lp.mt5utils as mt5utils

from charttools import simple_message_box

from _debugger import _p

# Set the Wine command
class WineProcess:
    def __init__(self, exe_path=None, 
                 headless_mode=False, 
                 winepfx=None, 
                 mt5_server_options=None,
                 python_exe_path=None): 

        # Set the proper wineprefix in the runtime environment        
        if winepfx:
            os.environ['WINEPREFIX'] = winepfx
        
        # remove wine debugging spam
        os.environ['WINEDEBUG'] = '-all'

        exe_file="/terminal64.exe"
        # Drop the filename
        exe_dir = exe_path[:exe_path.rfind(exe_file)]
        # Extract the immediate parent folder name plus the .exe filename
        self.exe_pointer = (a:=exe_dir[exe_dir.rfind("/")+1:])+exe_file
        # The same in Windows format for wine windows processes, if any
        self.exe_pointer_win=a+"\\"+exe_file[1:]

        self.wine_proc = None
        if exe_path:
            # Run the Wine command
            if winepfx is not None:
                wine_cmd = ['env', f'WINEPREFIX={winepfx}', 'wine', exe_path]
            else:
                wine_cmd = ['wine', exe_path]
            
            if headless_mode:
                # Direct the GUI to xfvb
                wine_cmd = ['xvfb-run', '--auto-servernum', '--server-num=1'] + wine_cmd

            self.wine_proc = subprocess.Popen(wine_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        self.mt5=mt5utils.mt5_server(python_exe_path, options=mt5_server_options)
        if not self.mt5.initialize():
            simple_message_box(text=f"mt5.initialize() failed, error code = {self.mt5.last_error()}")


    def shutdown(self):
        self.mt5.shutdown()
        if self.wine_proc:
            self.wine_proc.kill()
            self.wine_proc.wait()
        kill_processes(self.exe_pointer,self.exe_pointer_win,"mt5lp", "python.exe")

def kill_processes(*masks):
    """
    Kill processes that match any of the given string masks.

    Args:
        masks (*str): The tuple of string masks to match against process names.

    Returns:
        None
    """
    assert all(isinstance(mask, str) for mask in masks), "All masks must be strings"
    assert all(mask != '' for mask in masks), "All masks must be non-empty strings"

    for proc in psutil.process_iter(['pid','name','cmdline']):
        cmd=proc.info['cmdline'][0] if len(proc.info['cmdline']) > 0 else ''         
        for mask in masks:
            if mask in proc.info['name'] or mask in cmd:
                try:
                    proc.terminate()
                    # print(f"Killed process {proc.info['pid']} with name {proc.info['name']}")
                except psutil.Error as e:
                    print(f"Error killing process {proc.info['pid']}: {e}")

