import PySide6
from PySide6 import QtCore,QtGui
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
import pyqtgraph as pg
import os, csv, time, requests

import cfg
import overrides as ovrd, overrides
import fetcher as ftch, fetcher

from _debugger import _print,_p,_pc,_printcallers,_c,_exinfo,_ptime

class Timeseries:
    def __init__(self,session=None,fetch=None,symbol=cfg.D_SYMBOL,timeframe=cfg.D_TIMEFRAME,count=cfg.D_BARCOUNT):
        super().__init__()
        self.symbol=symbol
        self.timeframe=self.tf=timeframe
        self.adj=1 if self.tf in cfg.ADJUSTED_TIMEFRAMES else 0
        self.wadj=2*cfg.PERIOD_D1 if self.tf==cfg.PERIOD_W1 else 0 # Weekly timeframes adjustment due to pyqtgraph's assigning previous Saturday 
        
        ses=requests.Session() if session is None else session                                                            # as the week's candle date
        self.count=count
        self.lc_complete=True
        
        self.tf_label=''
        for key in cfg.TIMEFRAMES:
            if cfg.TIMEFRAMES[key]==self.tf:
                self.tf_label=key
        
        self.datasource=cfg.DATA_SYMBOLS_DIR+self.symbol+'_'+self.tf_label+'.csv'
        self.data = []

        self.fetch=ftch.Fetcher() if fetch is None else fetch

        #Check-ups to establish whether the historical data already exists,
        #to correctly reload new historical data if the existing one is too old;
        #or populate it if it is non-existent
        def read_datasource():
            with open(self.datasource) as csvfile:
                reader = csv.reader(csvfile, quoting=csv.QUOTE_NONNUMERIC) # change contents to floats
                self.data=list(reader)
        
        def fill_datasource():
            self.fetch.fetch_data(session=ses,record=True,symbol=self.symbol,timeframe=self.tf,count=self.count)
            read_datasource()

        if not os.path.isfile(self.datasource) or os.stat(self.datasource).st_size==0:
            fill_datasource()
        else:   
            read_datasource()
            lc_time=self.data[-1][1]
            if (time.time()-lc_time)//self.tf>self.count:
                with open(self.datasource,'w') as f:
                    f.truncate()
                fill_datasource()                
        #----------------------------------------------------------------

        self.ticks=[] #datetimed indecies
        self.times=[] #real datetime series
        self.opens=[]
        self.highs=[]
        self.lows=[]
        self.closes=[]
        self.values=[]
        
        self.read_ts(self.data)
        self.update_ts(session=ses,record=True)
        self.update_lc(self.fetch.fetch_lc(ses,self.symbol,self.tf))
        if session is None:
            ses.close()
            del ses

    def read_ts(self,data):
        if data is None:
            return

        self.indexcut=data[-1][0]#+adj
        self.timecut=data[-1][1]
        
        for row in data:
            row[0]=(row[0]+self.adj)*self.tf#datetiming ticks
            self.ticks.append(row[0])
            self.times.append(row[1]+self.wadj)
            self.opens.append(row[2])
            self.highs.append(row[3])
            self.lows.append(row[4])
            self.closes.append(row[5])
            self.values.append([row[i]+self.wadj if i==1 else row[i] for i,val in enumerate(row)]) #the summary of the above elements

        self.last_tick=self.ticks[-1]
        self.first_tick=self.ticks[0]

        # self.bars=[[i,*row[1:]] for i,row in enumerate(self.values)]#self.bars is self.values without the tick column
        if data is not self.data:
            self.data=self.data+data
            del data
    
    def update_ts(self,session=None,record=False): #unsaved ts portion update
        fromdt=self.times[-1]+self.tf+self.wadj
        todt=time.time()#(self.tf+wa)*(time.time()//(self.tf+wa))
        if todt-fromdt>=self.tf:
            datadict=self.fetch.fetch_data(session=session, record=record, symbol=self.symbol, fromdt=fromdt,todt=todt,
                    indexcut=self.indexcut,timeframe=self.tf)
            if datadict is None:
                data=None
            else:
                data=datadict['data']
                self.lc_complete=datadict['complete']
        else:
            data=None 
        try:self.read_ts(data)
        except Exception:pass
    
    def update_lc(self,dt): #last candle update
        if dt is not None and dt['data'] is not None:
            data=dt['data'][0]
            self.lc_complete=dt['complete']
            if data[1]==int(self.data[-1][1]):
                self.data[-1]=data
                self.data[-1][0]=self.last_tick
                self.refresh_values(-1)
            else:
                data[0]=(data[0]+1+self.indexcut)
                self.read_ts([data])

    def refresh_values(self,i):
        self.ticks[i]=self.data[i][0]
        self.times[i]=self.data[i][1]+self.wadj
        self.opens[i]=self.data[i][2]
        self.highs[i]=self.data[i][3]
        self.lows[i]=self.data[i][4]
        self.closes[i]=self.data[i][5]
        self.values[i]=[self.ticks[i],self.times[i],self.opens[i],self.highs[i],self.lows[i],self.closes[i]]
        # j=i if i>=0 else len(self.values)+i
        # self.bars[i]=[j,*self.values[1:]]

    # accepts timestamp and ohlc in [t,o,h,l,c] format, finds corresponding candle 
    # in self.data by timestamp and replaces ohlc in self.data if not identical, 
    # preserving self's current tick value
    # inter alia, fixes the interim candle issue by keeping the update request 
    # in a thread separate from the UI thread
    def replace_candle(self,candle):
        index=None
        replaced=False
        #start from the latest candle is faster in most cases hence reversed
        for i,cn in enumerate(reversed(self.data)):
            # find candle by the timestamp 
            if cn[1]==candle[0]:
                index=len(self.data)-i-1
                # replace only if ohlc are not identical
                if self.data[index][1:]!=candle:
                    self.data[index][1:]=candle #[1:] to preserve tick value.
                    replaced=True                                                    
                break
        if index is not None:
            self.refresh_values(index)
        # True if ohlc not identical and replacement took place; False otherwise
        return replaced

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
        self.last_tick=timeseries.last_tick
        self.first_tick=timeseries.first_tick
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
        if(charttype=='Candle'):
            p.setPen(pg.mkPen(self.chartprops[cfg.framecolor],width=0.7)) 
            for (t, d, open, max, min, close) in self.timeseries.data[self.start:self.end]:                
                if max!=min:
                    p.drawLine(QtCore.QPointF(t, min), QtCore.QPointF(t, max))
                if open > close:
                    p.setBrush(pg.mkBrush(self.chartprops[cfg.bear]))
                else:
                    p.setBrush(pg.mkBrush(self.chartprops[cfg.bull]))
                p.drawRect(QtCore.QRectF(t-w, open, w*2, close-open))
        elif(charttype=='Bar'):
            p.setPen(pg.mkPen(self.chartprops[cfg.barcolor],width=0.7))
            for (t, d, open, max, min, close) in self.timeseries.data[self.start:self.end]:
                if max!=min:
                    p.drawLine(QtCore.QPointF(t, min), QtCore.QPointF(t, max))
                p.drawLine(QtCore.QPointF(t, close), QtCore.QPointF(t+w, close))
                p.drawLine(QtCore.QPointF(t, open), QtCore.QPointF(t-w, open))
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
        self.last_tick=timeseries.last_tick
        self.first_tick=timeseries.first_tick
        
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
    