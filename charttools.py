import PySide6
import sys,inspect
from pyqtgraph import Point
from datetime import datetime
import numpy as np
import pandas as pd
from pytz import timezone, UnknownTimeZoneError

import overrides as ovrd,overrides
import cfg
from uitools import simple_message_box

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

def ticks_to_times(ts,x):
    tf=ts.tf

    if tf not in cfg.ADJUSTED_TIMEFRAMES:
        if x>=ts.ticks[-1]+0.5*tf: #0.5*tf adj here and further spreads the timestamp over the width of the candle
            result=ts.times[-1]+(x-ts.ticks[-1])
        elif x<=ts.ticks[0]+0.5*tf:
            result=ts.times[0]-(ts.ticks[0]-x)
        else:
            result=ts.times[int((x+0.5*tf)//tf)] 
    
    else:
        chart_adj=1*tf 
        if x>=ts.ticks[-1]+0.5*tf: 
            result=ts.times[-1]+(x-ts.ticks[-1])+chart_adj
        elif x<=ts.ticks[0]+0.5*tf:
            result=ts.times[0]-(ts.ticks[0]-x)
        elif ts.ticks[-2]+0.5*tf<x<ts.ticks[-1]+0.5*tf: #last candle processed individually
            result=ts.times[-1]
        else:
            result=ts.times[int((x+0.5*tf-chart_adj)//tf)]

    return result

def times_to_ticks(ts,dt):
    tf=ts.tf
    chart_adj=1*tf if tf in cfg.ADJUSTED_TIMEFRAMES else 0
    
    if dt>ts.times[-1]+tf: #to ensure that the entire last candle's time period is covered
        result=ts.ticks[-1]+(dt-ts.times[-1])-chart_adj
    elif dt<=ts.times[0]:
        result=ts.ticks[0]-(ts.times[0]-dt)
    else:
        i=np.where((ts.times<=dt) & (dt<ts.times+tf))[0][0]
        result=ts.ticks[i]
    
    return result

def screen_to_plot(ts,x):
    dtx=ticks_to_times(ts,x)
    dtxs = datetime.fromtimestamp(dtx)
    
    tf=ts.timeframe
    chart_adj=tf if tf in cfg.ADJUSTED_TIMEFRAMES else 0
    if int(dtx)>ts.times[-1]:
        ind=-1
    else:
        ind=int((x+0.5*tf-chart_adj)//tf)

    return dtxs,ind

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
    elif symb[:3] in ('BTC'):
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

from PySide6.QtWidgets import QMessageBox
from drawings import CrossHair,PriceLine

def set_chart(plt,symbol=None,timeframe=None):
    old_item=plt.chartitem
    old_lc_item=plt.lc_item
    symb=symbol if symbol is not None else old_item.symbol
    timef=timeframe if timeframe is not None else old_item.timeframe
    tk=(ts:=old_item.timeseries).ticks[-1]
    ax0=(ax:=plt.getAxis('bottom')).range[0]
    ax1=ax.range[1]
    cnt=int((tk-ax0)//ts.tf)
    shf=int((ax1-tk)//ts.tf)
    try:
        try:
            plt.removeItem(old_lc_item)
        except Exception:
            pass
        new_item=plt.mwindow.cbl_plotter(plt,symbol=symb,ct=old_item.charttype,
            tf=timef)
        plt.mwindow.range_setter(plt,new_item,xcount=cnt,xshift=shf)
        plt.removeItem(old_item)
        del old_item
        plt.chartitem=new_item
        # chtl.carryover_items(plt,newitem=new_item)
        
        if plt.crosshair_enabled==True:
            del plt.crosshair_item
            plt.crosshair_item=CrossHair(plt)
        
        if plt.priceline_enabled==True:
            del plt.priceline
            plt.priceline=PriceLine(plt)
        plt.sigTimeseriesChanged.emit(new_item.timeseries)
        plt.vb.sigResized.emit(plt.vb) #workaround to ensure propogation of AltDateAxisItem data
    except Exception as e:
        simple_message_box(text=f'Invalid symbol: {e}',icon=QMessageBox.Warning)
        #print('Invalid symbol')

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

#can except both timeframes and timeframe labels
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

