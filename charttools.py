import PySide6
import sys,inspect
from pyqtgraph import Point
from datetime import datetime
import numpy as np
from pytz import timezone, UnknownTimeZoneError

import cfg

from _debugger import _exinfo,_print,_printcallers,_p,_pc,_c,_pp
   
def zero1P():
    return [Point(0.0,0.0)]

def zero2P():
    return [Point(0.0,0.0), Point(0.0,0.0)]

def zeroP(n): #cannot use comprehension as it works incorrectly
    a=[]
    for i in range(n):
        a.append(Point(0.0,0.0))
    return a

def item_is_draw(item):
    if hasattr(item,"is_draw"):
        return item.is_draw
    else:
        return False

def item_is_study(item):
    if hasattr(item,"is_study"):
        return item.is_study
    else:
        return False

def item_is_cbl(item):
    if hasattr(item,"is_cbl"):
        return item.is_cbl
    else:
        return False

def ray_mode(state,action):
    a=cfg.RAYDIR
    if action == a['r']:
        if state== a['r']:
            return a['n']
        elif state ==a['l']:
            return a['b']
        elif state ==a['b']:
            return a['l']
        elif state==a['n']:
            return a['r']
        else:
            return a['r']
    if action== a['l']:
        if state== a['r']:
            return a['b']
        elif state ==a['l']:
            return a['n']
        elif state ==a['b']:
            return a['r']
        elif state==a['n']:
            return a['l']
        else:
            return a['r']
    else:
        return a['r']

def precision(symb):
    if symb[3:]=='JPY' or symb[:3] in  ('XAU','XAG','BCO'):
        return 3
    elif symb[:3] in ('BTC') or symb[:4] in ('DASH'):
        return 2
    else:
        return 5

def dict_to_keys(d):
    a=[]
    for key in d:
        a.append(key)
    return a

def callers():
    i=2
    a=[(st:=inspect.stack())[1].function,'CALLERS: ', st[i].function]
    while True:
        try:
            a.append(st[i].function)
            i+=1
        except Exception:
            break
    return a

def from_open_subw():
    return 'open_subw' in callers()

def transpose(lst):
    return np.transpose(lst)

def nametag(cnt=None):
    if cnt is None:
        return str(datetime.now().timestamp()).replace('.','')
    else:
        return str(datetime.now().timestamp())[-cnt:].replace('.','')

#from pg color format to hex
from pyqtgraph.functions import Colors as pgColors
def pgclr_to_hex(clr):
    try:
        res=pgColors[clr].name()
    except Exception:
        res=clr
    return res

from PySide6 import QtWidgets 
def simple_message_box(title=None,text='Notification',icon=None):
        mbox=QtWidgets.QMessageBox()
        mbox.setWindowTitle(title)
        mbox.setText(text)
        if icon!=None:
            mbox.setIcon(icon)
        mbox.exec()

#can accept both timeframes and timeframe labels
def symbol_to_filename(s=cfg.D_SYMBOL,tf=cfg.D_TIMEFRAME, fullpath=False):
    if tf not in list(cfg.TIMEFRAMES.keys()):
        try:
            filename=f'{s}_{cfg.tf_to_label(tf)}.csv'
        except Exception:
            simple_message_box(text=f"Unknown timeframe: {tf}")
            return
    else:
        filename=f'{s}_{tf}.csv'
    
    if fullpath:
        filename=cfg.DATA_SYMBOLS_DIR+filename
    
    return filename

def is_linux():
    return sys.platform.startswith('linux')

def is_windows():
    return sys.platform in ('win32','cygwin','msys')

def string_to_html(text_color='black'):
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Replace newline characters with the <br> tag
            formatted_text = result.replace('\n', '<br>')
            # Create the HTML-formatted tooltip with the specified text color
            output_text = f'<font color="{text_color}">{formatted_text}</font>'
            return output_text
        return wrapper
    return decorator

def filename_to_symbol(filename):
    if "_" not in filename:
        return None
    else:
        parts=filename.split('_')
        symbol=parts[0]
        timeframe_label=parts[1].split('.')[0]
        if timeframe_label not in list(cfg.TIMEFRAMES.keys()):
            return None
    
    return symbol, cfg.TIMEFRAMES[timeframe_label]

def get_timezone_shift(timezone_1, timezone_2):
		"""
		This function calculates the time difference between two timezones in hours.

		Args:
			timezone_1 (str): The first timezone name (e.g., 'US/Eastern').
			timezone_2 (str): The second timezone name (e.g., 'Asia/Tokyo').

		Returns:
			float: The time difference between the two timezones in hours (positive or negative).

		Raises:
			ValueError: If any of the provided timezones are invalid.
		"""
		try:
			tz_obj_1 = timezone(timezone_1)
			tz_obj_2 = timezone(timezone_2)
		except UnknownTimeZoneError:
			raise ValueError("Invalid timezone provided")

		# Get the UTC offset for each timezone in seconds
		utc_offset_1 = tz_obj_1.utcoffset(datetime.now()).total_seconds() / 3600
		utc_offset_2 = tz_obj_2.utcoffset(datetime.now()).total_seconds() / 3600

		# Calculate the time difference in hours
		time_diff = utc_offset_2 - utc_offset_1
		return int(time_diff)

def to_pips(symbol:str =None):
    return 10**(precision(symbol if symbol else "EURUSD")-1)

def to_points(symbol: str=None):
    return 10*to_pips(symbol)

