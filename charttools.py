import PySide6
from pyqtgraph import Point
import datetime
import numpy as np
import overrides as ovrd,overrides
import cfg

import sys,inspect

from _debugger import _exinfo,_print,_printcallers,_p,_pc,_c
   
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

def times_to_ticks(ts,x):
    tf=ts.tf
    chart_adj=1*tf if tf in cfg.ADJUSTED_TIMEFRAMES else 0
    
    if x>ts.times[-1]+tf: #to ensure that the entire last candle's time period is covered
        result=ts.ticks[-1]+(x-ts.times[-1])-chart_adj
    elif x<=ts.times[0]:
        result=ts.ticks[0]-(ts.times[0]-x)
    else:
        i=len(ts.times)-2
        while i>=0:
            if ts.times[i]<=x and x<ts.times[i+1]:
                break
            i-=1
        result=ts.ticks[i]
    
    return result

def screen_to_plot(ts,x):
    dtx=ticks_to_times(ts,x)
    dtxs = datetime.datetime.fromtimestamp(dtx)
    
    tf=ts.timeframe
    chart_adj=tf if tf in cfg.ADJUSTED_TIMEFRAMES else 0
    if int(dtx)>ts.times[-1]:
        ind=-1
    else:
        ind=int((x+0.5*tf-chart_adj)//tf)

    return dtxs,ind

def OBJ_IS(title,obj):
    pfx='graphicsItems.'
    title=f'{pfx}{title}'
    try:
        a=str(obj.__mro__)
    except Exception:
        a= str(type(obj).__mro__)
    return a.find(title)!=-1

def item_is_draw(item):
    try:
        return item.is_draw
    except Exception:
        return False

def item_is_study(item):
    try:
        return item.is_study
    except Exception:
        return False

def item_is_cbl(item):
    try:
        return item.is_cbl
    except Exception:
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
        return str(datetime.datetime.now().timestamp()).replace('.','')
    else:
        return str(datetime.datetime.now().timestamp())[-cnt:].replace('.','')

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
from uitools import simple_message_box
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
        plt.mwindow.range_setter(plt,new_item,new_item.last_tick,xcount=cnt,
            xshift=shf,tf=timef)
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
    except Exception:
        simple_message_box(text='Invalid symbol',icon=QMessageBox.Warning)
        #print('Invalid symbol')

def is_linux():
    return sys.platform.startswith('linux')

def is_windows():
    return sys.platform in ('win32','cygwin','msys')

if __name__=='__main__':
    pass