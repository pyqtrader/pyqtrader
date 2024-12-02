import PySide6
from PySide6 import QtCore,QtGui
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
import pyqtgraph as pg
from pyqtgraph import Point
import os, requests, typing, time
import numpy as np
import pandas as pd
import dataclasses as dc

import cfg
import overrides as ovrd, overrides
import fetcher as ftch, fetcher
import charttools as chtl, charttools

from _debugger import *

class Timeseries:
    def __init__(self,session=None,fetch=None,symbol=cfg.D_SYMBOL,timeframe=cfg.D_TIMEFRAME,count=cfg.D_BARCOUNT):
        super().__init__()
        self.symbol=symbol
        self.timeframe=self.tf=timeframe
        self.adj=1 if self.tf in cfg.ADJUSTED_TIMEFRAMES else 0
        
        # Weekly timeframes adjustment due to 
        # pyqtgraph's assigning previous Saturday 
        # as the week's candle date
        self.wadj=2*cfg.PERIOD_D1 if self.tf==cfg.PERIOD_W1 else 0  
                                                                    
        ses=requests.Session() if session is None else session                                                           
        self.count=count
        self.lc_complete=True
        
        self.tf_label=cfg.tf_to_label(self.tf)
        
        self.datasource=chtl.symbol_to_filename(self.symbol,self.tf_label,True)
        self.data=None

        self.fetch=ftch.Fetcher() if fetch is None else fetch

        # if cached timeseries file exists
        up_to_date_save_exists=False
        if os.path.isfile(self.datasource) and os.stat(self.datasource).st_size!=0:
            self.data=pd.read_csv(self.datasource,names=cfg.TS_NAMES)
            lc_time=self.data.t.iloc[-1]
            
            # Do not retrieve exessive data
            current_time=int(time.time())
            # In absence of a better approach, use bars to current time including off market times,
            # in order to identify whether the file is up to date
            bars_to_current_time=1+(current_time-lc_time)//self.tf

            if bars_to_current_time>self.count:
                datadict=self.fetch.fetch_data(session=ses,fromdt=lc_time, symbol=self.symbol,
                    timeframe=self.tf,count=self.count)
            else:
                datadict=self.fetch.fetch_data(session=ses,fromdt=lc_time, todt=current_time, symbol=self.symbol,
                    timeframe=self.tf)

            # if connection is on 
            if datadict is not None:
                # if the file is up to date
                if bars_to_current_time<self.count:
                    up_to_date_save_exists=True
                    self.update_ts(datadict)

                    # append new data to the file
                    if self.lc_complete:
                        self.data.to_csv(self.datasource,index=None,header=None)
                    else:
                        self.data.iloc[:-1].to_csv(self.datasource,index=None,header=None) #exclude incomplete candle
                # if file is obsolete(older than count)
                else:
                    # clear the obsolete data to avoid mixing it with new data
                    self.data=None

        # if cached timeseries file does not exist or it is obsolete (older than count)
        if not up_to_date_save_exists:
            datadict=self.fetch.fetch_data(session=ses,symbol=self.symbol,timeframe=self.tf,count=self.count)
            
            if datadict is not None:
                self.update_ts(datadict)

                # save data to file
                if self.lc_complete:
                    self.data.to_csv(self.datasource,index=None,header=None)
                else:
                    self.data.iloc[:-1].to_csv(self.datasource,index=None,header=None) #exclude incomplete candle

        if session is None:
            ses.close()
            del ses

    def update_ts(self,candles: dict)-> None:
        if candles is None:
            return
        
        if candles['complete'] is not None:
            self.lc_complete = candles['complete']
        self.data=pd.concat([self.data,candles['data']])
        self.data.drop_duplicates(keep='last',subset=['t'],inplace=True)
        self.data.reset_index(drop=True,inplace=True)

        return
    
    def detimed(self,a): #conversion from ticks to index
        return int(a//self.tf) if isinstance(a,float) else a
    
    def ymax(self,x0,x1): #can accept both int index and float ticks as args due to detimed()
        
        x0=self.detimed(x0)
        x1=self.detimed(x1)

        try:
            y=max(self.highs[max(x0,0): min(x1,len(self.highs)-1)])
        except Exception:
            y=0
        return y
    
    def ymin(self,x0,x1): #can accept both int index and float ticks as args due to detimed()

        x0=self.detimed(x0)
        x1=self.detimed(x1)

        try:
            y=min(self.lows[max(x0,0): min(x1,len(self.highs)-1)])
        except Exception:
            y=0
        return y    
    
    @property
    def ticks(self):
        return (self.data.index.to_numpy()+self.adj)*self.tf

    @property
    def times(self):
        return self.data[cfg.TIMES].to_numpy()+self.wadj

    @property
    def opens(self):
        return self.data[cfg.OPENS].to_numpy()

    @property
    def highs(self):
        return self.data[cfg.HIGHS].to_numpy()

    @property
    def lows(self):
        return self.data[cfg.LOWS].to_numpy()

    @property
    def closes(self):
        return self.data[cfg.CLOSES].to_numpy()

## Create a subclass of GraphicsObject.
## The only required methods are paint() and boundingRect() 
## (see QGraphicsItem documentation)
class CandleBarItem(pg.GraphicsObject):
    def __init__(self, charttype, timeseries, start, end, chartprops=cfg.D_CHARTPROPS):
        pg.GraphicsObject.__init__(self)
        self.is_cbl=True
        self.timeseries = timeseries  ## data must have fields: time, open, close, min, max
        self.charttype=charttype
        self.symbol=timeseries.symbol
        self.datasource=timeseries.datasource        
        self.timeframe=self.tf=timeseries.timeframe
        self.tf_label=timeseries.tf_label
        self.ticks=timeseries.ticks
        self.times=timeseries.times
        self.highs=timeseries.highs
        self.lows=timeseries.lows
        self.start=start
        self.end=end
        self.chartprops=dict(chartprops)

        self.ymax=timeseries.ymax
        self.ymin=timeseries.ymin
        self.setZValue(-1)
        
        self.generatePicture(charttype)

    def generatePicture(self, charttype):
        ## pre-computing a QPicture object allows paint() to run much more quickly, 
        ## rather than re-drawing the shapes every time.
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        # w = (self.timeseries.data[1][0] - self.timeseries.data[0][0]) / 3.
        w = self.timeframe/3
        ts= self.timeseries
        # ensure the ticks array is initialized outside of the loops
        ticks=ts.ticks
        if(charttype=='Candle'):
            p.setPen(pg.mkPen(self.chartprops[cfg.framecolor],width=0.7)) 
            for index,row in ts.data[self.start:self.end].iterrows():                
                t=ticks[index]
                if row.h!=row.l:
                    p.drawLine(QtCore.QPointF(t, row.l), QtCore.QPointF(t, row.h))
                if row.o > row.c:
                    p.setBrush(pg.mkBrush(self.chartprops[cfg.bear]))
                else:
                    p.setBrush(pg.mkBrush(self.chartprops[cfg.bull]))
                p.drawRect(QtCore.QRectF(t-w, row.o, w*2, row.c-row.o))
        elif(charttype=='Bar'):
            p.setPen(pg.mkPen(self.chartprops[cfg.barcolor],width=0.7))
            for index,row in ts.data[self.start:self.end].iterrows():
                t=ts.ticks[index] 
                if row.h!=row.l:
                    p.drawLine(QtCore.QPointF(t, row.l), QtCore.QPointF(t, row.h))
                p.drawLines([QtCore.QPointF(t, row.c), QtCore.QPointF(t+w, row.c),
                    QtCore.QPointF(t, row.o), QtCore.QPointF(t-w, row.o)])
        p.end()
    
    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        ## boundingRect _must_ indicate the entire area that will be drawn on
        ## or else we will get artifacts and possibly crashing.
        ## (in this case, QPicture does all the work of computing the bouning rect for us)
        return QtCore.QRectF(self.picture.boundingRect())

class ChartLineItem(PlotCurveItem):
    def __init__(self,timeseries,start=None,end=None,chartprops=cfg.D_CHARTPROPS):
        if start!=None:
            start=start-1
        super().__init__(timeseries.ticks[start:end],timeseries.closes[start:end])
        self.is_cbl=True
        self.timeseries=timeseries
        self.charttype='Line'
        self.symbol=timeseries.symbol
        self.datasource=timeseries.datasource
        self.timeframe=self.tf=timeseries.timeframe
        self.tf_label=timeseries.tf_label
        self.ticks=timeseries.ticks
        self.times=timeseries.times
        self.highs=timeseries.highs
        self.lows=timeseries.lows
        
        self.ymax=timeseries.ymax
        self.ymin=timeseries.ymin
        self.setZValue(-1) 

        prs=dict(chartprops)
        linecolor=prs[cfg.linecolor]
        self.setPen(linecolor)

def PlotTimeseries(symbol,ct,tf=None,ts=None,session=None,fetch=None,
    start=None,end=None,chartprops=cfg.D_CHARTPROPS):

    if session is None:
        session=requests.Session()

    if fetch is None:
        fetch=ftch.Fetcher()

    tseries=Timeseries(session=session,fetch=fetch,symbol=symbol,timeframe=tf) if ts is None else ts
    if ct=='Line':
        item=ChartLineItem(tseries,start,end,chartprops=chartprops)
    else:
        item = CandleBarItem(ct,tseries,start,end,chartprops=chartprops)

    return item

# Used for simple ROIs given by 'pos' and 'size', such as infinite line, ellipse and rectangle
@dc.dataclass
class dtPoint:
    dt: int|None = None
    x:  int|None = None
    y:  float|None = None
    ts: Timeseries|None = None

    # Convert int64 args to int to ensure JSON serializability
    def __post_init__(self):
        for field in dc.fields(self):
            value = getattr(self, field.name)
            if isinstance(value, np.int64):
                setattr(self, field.name, int(value))
    
    # Adds up raw coordinates and updates dt
    def __add__(self, other):
        o=lambda z: 0 if z is None else z
        x=o(self.x)+o(other.x)
        y=o(self.y)+o(other.y)
        dt=self._it(x)
        return dtPoint(dt,x,y,self.ts)

    # Returns tuple, as dt and ts are not meaningful in the context
    # of the operation.  Primarily used to calculate pyqtgraph's state values 
    # 'size', 'pos' etc.
    def __sub__(self, other):
        o=lambda z: 0 if z is None else z
        x=o(self.x)-o(other.x)
        y=o(self.y)-o(other.y)
        return x,y

             
    def _ti(self,dt):
        return chtl.times_to_ticks(self.ts,dt) if self.ts is not None else None

    def _it(self,x):
        return chtl.ticks_to_times(self.ts,x) if self.ts is not None else None

    # The function caches self.dt and returns self.x,self.y for position update;
    # also sets ts if given by 'other' and updates x value correspondingly
    def apply(self,other):
        
        # dt(times) and x(ticks) definitions:
        dt = self.dt
        x = self.x
        # dt(times) takes precedence over x(ticks), whether x is None or not
        if other.dt is not None:
            dt=other.dt
            x=self._ti(dt) 
        # if dt is None, set position directly, eg on mouse updates, and update dt
        elif other.x is not None:
            x=other.x
            dt=self._it(x)
        # elif self.dt is not None:
        #     x=self._ti(self.dt)
        
        # y(price) definition
        y=other.y if other.y is not None else self.y

        # ts definition
        if other.ts is not None:
            self.ts=other.ts
            if dt is not None:
                x=self._ti(dt)

        # returns actionable values for get/setPos()/get/setState(), 
        # simply refresh if all are None
        return dtPoint(dt,x,y,self.ts)
    
    # Fills None attributes in 'self' with values from 'other'.
    # Used primarily to fill in dt attribute
    def fillnone(self, other):
        d=dict()
        for field in dc.fields(self):
            value=getattr(self, field.name)
            d[field.name]=value
            if value is None:
                d[field.name]=getattr(other, field.name)
        
        return dtPoint(**d)
    
    def get_raw_points(self):
        return [self.x,self.y]

    def xy(self):
        return self.get_raw_points()

    def rollout(self):
        return [self.dt,self.x,self.y]

    @staticmethod
    def zero():
        return dtPoint(0,0,0)

#Used for complex ROIs with 2 or more handles/endpoints, such segments, trendlines, channels etc.
@dc.dataclass
class dtCords:

    cords: typing.List[dtPoint]|None=dc.field(default_factory=list) 

    # Sets default length to 2
    def __post_init__(self):
        if self.cords == [] or self.cords is None:
            self.cords=[dtPoint()]*2

    def __len__(self):
        return len(self.cords)

    def __add__(self,other):
        if isinstance(other,dtPoint):
            cords=[c + other for c in self.cords]
        else:
            cords=[c + d for c,d in zip(self.cords,other.cords)]
        
        return dtCords(cords)

    # Creates an empty dtCords object of lenght n, 2 by default 
    @staticmethod
    def make(n=None):
        n=2 if n is None else n
        return dtCords([dtPoint()]*n)

    def fillnone(self,other):
        if isinstance(other,dtPoint):
            cords=[c.fillnone(other) for c in self.cords]
        else:
            cords=[c.fillnone(d) for c,d in zip(self.cords,other.cords)]
        
        return dtCords(cords)

    def apply(self,other):
        if isinstance(other,dtPoint):
            cords=[c.apply(other) for c in self.cords]
        else:
            assert len(self.cords)==len(other.cords), "dtCords length mismatch in apply() function"
            cords=[c.apply(d) for c,d in zip(self.cords,other.cords)]
            
        return dtCords(cords)

    # Set dtPoint as i element of dtCords
    def set_cord(self,i,dtp):
        self.cords[i]=dtp
        return self

    # Adds element(s) to cords
    def adjoin(self, e: dtPoint|int|None=None)->None:

        if e is None:
            self.cords.append(dtPoint()) # Appends empty dtPoint
        elif type(e) is int:
            self.cords+=dtCords(n=e).cords # Appends e empty datapoints
        elif isinstance(e, dtPoint):
            self.cords.append(e)
        elif isinstance(e,dtCords):
            self.cords+=e.cords
        else:
            raise TypeError(f"adjoin() args can be dtPoint, dtCords, int or None; {type(e)} is given")
        
        return
    
    def remove(self, index):
        """Removes the element at the specified index from self.cords"""
        if index < 0:
            index = len(self.cords) + index
        if index < 0 or index >= len(self.cords):
            raise IndexError("Index out of range")
        self.cords.pop(index)

        return self

    def zero(self):
        return dtCords([dtPoint.zero()]*len(self))
    
    def get_pos(self):
        return self.cords[0].x,self.cords[0].y
    
    # Returns 'size' in the sense of pyqtgraph's state
    def get_size(self):
        return self.cords[1]-self.cords[0]
    
    def get_slice(self,sl:slice):
        rollout=self.rollout()
        return [sublist[sl] for sublist in rollout]
    
    def get_raw_points(self):
        return self.get_slice(slice(1,None))
    
    def dt(self):
        return self.get_slice(slice(0,1))

    def rollout(self):
        return [c.rollout() for c in self.cords]