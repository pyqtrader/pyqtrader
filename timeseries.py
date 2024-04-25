import PySide6
from PySide6 import QtCore,QtGui
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
import pyqtgraph as pg
import os, csv, time, requests
import pandas as pd

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
        if os.path.isfile(self.datasource) and os.stat(self.datasource).st_size!=0:
            self.data=pd.read_csv(self.datasource,names=cfg.TS_NAMES)
            lc_time=self.data.t.iloc[-1]
            datadict=self.fetch.fetch_data(session=ses,fromdt=lc_time,symbol=self.symbol,
                timeframe=self.tf,count=self.count)
            if datadict is not None:
                self.update_ts(datadict)
                # append new data to the file, [1:] to exclude already existing candle
                if self.lc_complete:
                    datadict['data'].iloc[1:].to_csv(self.datasource,mode='a',index=None,header=None)
                else:
                    datadict['data'].iloc[1:-1].to_csv(self.datasource,mode='a',index=None,header=None) #exclude incomplete candle
        
        # if cached timeseries file does not exist
        else:
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
                p.drawLine(QtCore.QPointF(t, row.c), QtCore.QPointF(t+w, row.c))
                p.drawLine(QtCore.QPointF(t, row.o), QtCore.QPointF(t-w, row.o))
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