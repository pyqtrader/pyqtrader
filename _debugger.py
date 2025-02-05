#debugger


__all__=['_print','_printcallers','_exinfo','_c','_pc', "_callers",
         '_p','_pp','_fts',"_ptime","comparestr", "_time_performance",
         "_debug_sound"]

import inspect
import sys
import time, datetime
import playsound

import cfg

myself=lambda *args: inspect.stack()[2].function
_print=lambda *args: print(_c(),myself()+': \n',*args)
_p=_print

#crashes and reboots windows 11, avoid use and import:
#_psource=lambda *args: _print(sys._getframe().f_back.f_code.co_name) #function name

def _callers(): #function stack
    i=2
    a=[inspect.stack()[1].function,'CALLERS: ', inspect.stack()[i].function]
    while True:
        try:
            a.append(inspect.stack()[i].function)
            i+=1
        except Exception:
            break
    return a

def _printcallers():
    print(*_callers())

_exinfo=lambda *args: print(sys.exc_info()) #exception info
_ptime=lambda x: print(datetime.datetime.fromtimestamp(x))

class _Counter:
    def __init__(self) -> None:
        self._c=0

    def count(self):
        self._c+=1
        return self._c-1
_c=_Counter().count

def _pc():
    _print(_c())

def _pp(*x):
    _print(*x)
    _printcallers()

def _fts(x):
    return datetime.datetime.fromtimestamp(x)

def comparestr(a, b):
    for x, y in zip(a, b):
        if x != y:
            print(x,y)

# decorator
def _time_performance(func):
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        print(f"Finished {func.__name__!r} in {run_time*1000:.5f} ms")
        return value
    return wrapper_timer

def _debug_sound():
    playsound.playsound(cfg.ASSETS_DIR+"service-login.oga", block=False)
