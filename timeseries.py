import PySide6
from PySide6 import QtCore,QtGui
from pyqtgraph.graphicsItems.PlotCurveItem import PlotCurveItem
import pyqtgraph as pg
import os, requests, typing, time
from datetime import datetime
import numpy as np
import pandas as pd
import dataclasses as dc

import cfg
import charttools as chtl, charttools

try:
    import fetcher as ftch, fetcher
except ImportError:
    pass

from _debugger import *


class Timeseries:
    def __init__(self,session=None,fetch=None,symbol=cfg.D_SYMBOL,timeframe=cfg.D_TIMEFRAME,count=cfg.D_BARCOUNT):
        ses=requests.Session() if session is None else session                                                           
        self.fetch=fetch
        self.symbol=symbol
        self.timeframe=self.tf=timeframe

        self.is_renko=False

        self.count=count
        self.lc_complete=True

        self.tf_label=cfg.tf_to_label(self.tf)
        
        # Generate absolute path to be able to use the class externally
        self.datasource=os.path.abspath(os.path.join(os.path.dirname(__file__),
            chtl.symbol_to_filename(self.symbol,self.tf_label,True)))
        
        self.data=None

        datadict=None
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

            if self.fetch:
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
            if self.fetch:
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

        df=candles['data']

        self.data=pd.concat([self.data,df])
        self.data.drop_duplicates(keep='last',subset=['t'],inplace=True)
        self.data.reset_index(drop=True,inplace=True)

        return
    
   
    def ymax(self,x0,x1): 
        try:
            y=max(self.highs[round(max(x0,0)): round(min(x1,len(self.highs)-1))])
        except Exception as e:
            y=0
        return y
    
    def ymin(self,x0,x1): 
        try:
            y=min(self.lows[round(max(x0,0)): round(min(x1,len(self.highs)-1))])
        except Exception as e:
            y=0
        return y    
    

    @property
    def bars(self):
        return self.data.index.to_numpy()

    @property
    def times(self):
        return self.data[cfg.TIMES].to_numpy()

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

    def extended_times(self,x):
        idx=self.data.index
        if x<idx[0]:
            return self.times[idx[0]]+(x-idx[0])*self.tf
        elif x>idx[-1]:
            return self.times[idx[-1]]+(x-idx[-1])*self.tf
        else:
            return self.times[x]
    
    @staticmethod
    def get_saved_symbol(symbol,timeframe=cfg.D_TIMEFRAME):
        
        # Generate absolute path to be able to use the method externally
        abs_path=os.path.abspath(os.path.join(os.path.dirname(__file__),
            cfg.DATA_SYMBOLS_DIR))

        filelist=os.listdir(abs_path)
        ascertained_list=[fl for fl in filelist 
                            if fl[:len(symbol)].upper()==symbol.upper()]

        if ascertained_list:
            for file in ascertained_list:
                fl=chtl.filename_to_symbol(file)
                if fl[1]==timeframe:
                    break
        else:
            for file in filelist:
                fl=chtl.filename_to_symbol(file)
                if fl[1]==timeframe:
                    break  
       
        symb=fl[0]            
        tf=fl[1]
       
        return symb,tf
    
    def sliced(self, ts_slice : slice|None=None):
        """
        Slice the Timeseries data.
        
        Parameters
        ----------
        ts_slice : slice or None, optional
            The slice object to be applied to the data. If None, the entire data is returned.
        
        Returns
        -------
        TsSliced
            A new timeseries object containing the sliced data.
        """
        return TsSliced(self, ts_slice)   


    def heikin_ashi(self, start=None, end=None):
        df = self.data.iloc[start-1 if start else start : end]
        # Calculate Heikin Ashi candles
        ha_df = pd.DataFrame(index=df.index)
        ha_df[cfg.CLOSES] = (df[cfg.OPENS] + df[cfg.HIGHS] + df[cfg.LOWS] + df[cfg.CLOSES]) / 4
        ha_df[cfg.OPENS] = (df[cfg.OPENS].shift(1) + df[cfg.CLOSES].shift(1)) / 2
        ha_df[cfg.HIGHS] = df[[cfg.HIGHS, cfg.OPENS, cfg.CLOSES]].max(axis=1)
        ha_df[cfg.LOWS] = df[[cfg.LOWS, cfg.OPENS, cfg.CLOSES]].min(axis=1)

        if start:
            # Drop the first row used for 'o' calculation
            ha_df = ha_df.iloc[1:]
        else:
            # Set the first open value to the first close value to start the series
            ha_df.loc[ha_df.index[0], cfg.OPENS] = ha_df.loc[ha_df.index[0], cfg.CLOSES]

        return ha_df

    @staticmethod
    def create_renko(df, chartprops : dict, **kwargs):
        mode = chartprops.get('renko_mode', cfg.RENKO_DMODE)

        if mode == cfg.RENKO_FLAT:
            base = kwargs.pop('base', chartprops.get('renko_flat_base', cfg.RENKO_DFLAT_BASE))
            brick_size = kwargs.pop('brick_size', chartprops.get('renko_flat_brick', cfg.RENKO_DFLAT_BRICK))
            return renko_flat(df, base=base, brick_size=brick_size,**kwargs)
        else:
            base = kwargs.pop('base' ,chartprops.get('renko_percent_base', cfg.RENKO_DPERCENT_BASE))
            brick_size = kwargs.pop('brick_size', chartprops.get('renko_percent_brick', cfg.RENKO_DPERCENT_BRICK))
            return renko_percent(df, base=base, brick_size=brick_size,**kwargs)


def renko_percent(df : pd.DataFrame,
            brick_size : float = cfg.RENKO_DPERCENT_BRICK, 
            base : float = cfg.RENKO_DPERCENT_BASE , # Base price from which the grid is built
            link_to_base : bool = False, # starting price, taken from the ts if False
            precision : int = 5 ) -> pd.DataFrame:
    
    def horizontal_grid(base_value, step):
        current = base_value
        while True:
            if step >= 0:
                yield round(current, precision)
                current = current * (1 + step / 100)
            else:
                yield round(current, precision)
                current = current / (1 + abs(step) / 100)
    
    def find_brick_close(price, base, brick_size):
        if price >= base:
            gen_up=horizontal_grid(base,brick_size)
            prev=next(gen_up)
            current=next(gen_up)

            while current < price:
                prev=current
                current=next(gen_up)

            return round(prev, precision)
        
        else:
            gen_down=horizontal_grid(base,-brick_size)
            prev=next(gen_down)
            current=next(gen_down)

            while current > price:
                prev=current
                current=next(gen_down)

            return round(prev, precision)

    renko_data = []
    renko_columns = [cfg.TIMES, cfg.OPENS, cfg.HIGHS, cfg.LOWS, cfg.CLOSES]
    _open0 = base if link_to_base else df['o'].iloc[0]

    # Identify initial brick
    last_brick_close=find_brick_close(_open0, base, brick_size)

    for row in df.itertuples():
        current_close = row.c
        current_timestamp = row.t

        new_brick_close = find_brick_close(current_close, last_brick_close, brick_size)
            
        price_diff = new_brick_close - last_brick_close

        # No new brick
        if price_diff==0:
            continue

        s=1 if price_diff>0 else -1

        # Draw new brick(s)
        gen=horizontal_grid(last_brick_close, s*brick_size)
        next_brick_close = next(gen)

        # Break the bar into intermediary bricks, if any
        while next_brick_close != new_brick_close:
            next_brick_close = next(gen)
            last = round(last_brick_close, precision)
            nx = round(next_brick_close, precision)
            
            # Append the new brick to the Renko data
            renko_data.append([
                current_timestamp,
                last,
                nx if price_diff >= 0 else last,
                nx if price_diff < 0 else last,
                nx                    
            ])
            last_brick_close = next_brick_close

    # Create the Renko dataframe
    renko_df = pd.DataFrame(renko_data, columns=renko_columns)
    return renko_df              

def renko_flat(df : pd.DataFrame, 
            brick_size : float = cfg.RENKO_DFLAT_BRICK, 
            base : float = cfg.RENKO_DPERCENT_BASE,
            link_to_base : bool = False, 
            precision : int = 5) -> pd.DataFrame:
    """
    Create a Renko chart dataframe from a given OHLC dataframe.

    Parameters:
    df (pd.DataFrame): The input dataframe with columns 't' (timestamp), 'o', 'h', 'l', 'c'.
    brick_size (float): The size of each Renko brick.
    base (float): The base applied to the brick boundary grid.

    Returns:
    pd.DataFrame: A dataframe representing the Renko chart with columns 't', 'o', 'c'.
    """

    renko_data = []
    renko_columns = [cfg.TIMES, cfg.OPENS, cfg.HIGHS, cfg.LOWS, cfg.CLOSES]

    # Initialize the first brick
    _unlinked = round((df['o'].iloc[0]   - base) / brick_size) * brick_size if not link_to_base else 0     
    last_brick_close = base + _unlinked

    # Calculate the brick size dynamically if percentage_based is True
    for row in df.itertuples():
        current_close = row.c
        current_timestamp = row.t
        
        # Calculate the difference between the current close and the last brick close
        price_diff = current_close - last_brick_close
        
        # Check if the price movement is sufficient to form a new brick
        if abs(price_diff) >= brick_size:
            # Determine the number of bricks to add
            num_bricks = int(abs(price_diff) // brick_size)
            
            for _ in range(num_bricks):
                if price_diff > 0:
                    # Upward brick
                    new_brick_close=last_brick_close + brick_size
                else:
                    # Downward brick
                    new_brick_close = last_brick_close - brick_size
                
                last = round(last_brick_close, precision)
                new = round(new_brick_close, precision)
                
                # Append the new brick to the Renko data
                renko_data.append([
                    current_timestamp,
                    last,
                    new if price_diff >= 0 else last,
                    new if price_diff < 0 else last,
                    new                    
                ])
                
                # Update the last brick close
                last_brick_close = new_brick_close
    
    # Create the Renko dataframe
    renko_df = pd.DataFrame(renko_data, columns=renko_columns)
    return renko_df


## Create a subclass of GraphicsObject.
## The only required methods are paint() and boundingRect() 
## (see QGraphicsItem documentation)
class CandleBarItem(pg.GraphicsObject):
    def __init__(self, charttype, timeseries : Timeseries, start, end, chartprops=cfg.D_CHARTPROPS):
        pg.GraphicsObject.__init__(self)
        self.is_cbl=True
        self.timeseries = timeseries  ## data must have fields: time, open, close, min, max
        self.symbol=timeseries.symbol
        self.datasource=timeseries.datasource        
        self.timeframe=self.tf=timeseries.timeframe
        self.tf_label=timeseries.tf_label       
        self.charttype=charttype
        self.chartprops=dict(chartprops)
        
        # Replace raw source dataframe with Renko before assigning timeseries arrays
        if charttype=="Renko" and not self.timeseries.is_renko:
            _ts=self.timeseries
            _ts.data=_ts.create_renko(_ts.data, self.chartprops, precision=chtl.precision(self.symbol))
            df=_ts.data
            if start:
                x=start
                for i in range(df.index):
                    df.index[i]=x
                    x+=1
            _ts.is_renko=True
                    
        self.bars=timeseries.bars
        self.times=timeseries.times
        self.highs=timeseries.highs
        self.lows=timeseries.lows
        
        self.start=start
        self.end=end

        self.ymax=timeseries.ymax
        self.ymin=timeseries.ymin
        self.setZValue(-1)
        
        self.generatePicture(charttype)

    def generatePicture(self, charttype):
        ## pre-computing a QPicture object allows paint() to run much more quickly, 
        ## rather than re-drawing the shapes every time.
        self.picture = QtGui.QPicture()
        p = QtGui.QPainter(self.picture)
        w=1/3
        df= self.timeseries.data.iloc[self.start:self.end]
        
        if charttype=='Candle':
            p.setPen(pg.mkPen(self.chartprops[cfg.framecolor],width=0.7)) 
            bull_brush=pg.mkBrush(self.chartprops[cfg.bull])
            bear_brush=pg.mkBrush(self.chartprops[cfg.bear])
            for row in df.itertuples():                
                t=row.Index
                if row.h!=row.l:
                    p.drawLine(QtCore.QPointF(t, row.l), QtCore.QPointF(t, row.h))
                if row.o > row.c:
                    p.setBrush(bear_brush)
                else:
                    p.setBrush(bull_brush)
                p.drawRect(QtCore.QRectF(t-w, row.o, w*2, row.c-row.o))

        elif charttype=='Bar':
            p.setPen(pg.mkPen(self.chartprops[cfg.barcolor],width=0.7))
            for row in df.itertuples():
                t=row.Index
                if row.h!=row.l:
                    p.drawLine(QtCore.QPointF(t, row.l), QtCore.QPointF(t, row.h))
                p.drawLines([QtCore.QPointF(t, row.c), QtCore.QPointF(t+w, row.c),
                    QtCore.QPointF(t, row.o), QtCore.QPointF(t-w, row.o)])
        
        elif charttype=="HeikinAshi":
            ha_df=self.timeseries.heikin_ashi(self.start, self.end)
            bull_pen=pg.mkPen(self.chartprops[cfg.bull], width=2)
            bear_pen=pg.mkPen(self.chartprops[cfg.bear], width=2)
            bull_brush=pg.mkBrush(self.chartprops[cfg.bull])
            bear_brush=pg.mkBrush(self.chartprops[cfg.bear])
            for row in ha_df.itertuples():                
                t=row.Index
                if row.o > row.c:
                    p.setPen(bear_pen)
                    p.setBrush(bear_brush)
                else:
                    p.setPen(bull_pen)
                    p.setBrush(bull_brush)
                if row.h!=row.l:
                    p.drawLine(QtCore.QPointF(t, row.l), QtCore.QPointF(t, row.h))
                p.drawRect(QtCore.QRectF(t-w, row.o, w*2, row.c-row.o))
        

        elif charttype=="Renko":
            bull_pen=pg.mkPen(self.chartprops[cfg.bull], width=0.1)
            bear_pen=pg.mkPen(self.chartprops[cfg.bear], width=0.1)
            bull_brush=pg.mkBrush(self.chartprops[cfg.bull])
            bear_brush=pg.mkBrush(self.chartprops[cfg.bear])
            for row in self.timeseries.data.itertuples():
                t=row.Index
                if row.o > row.c:
                    p.setPen(bear_pen)
                    p.setBrush(bear_brush)
                else:
                    p.setPen(bull_pen)
                    p.setBrush(bull_brush)
                p.drawRect(QtCore.QRectF(t-w, row.o, w*2, row.c-row.o))

        else:
            raise ValueError(f"Invalid {charttype=}, should be in {cfg.CHARTTYPES}")

        p.end()

    def refresh(self, start=None, end=None):
        self.start=start
        self.end=end
        self.generatePicture(self.charttype)
    
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
        super().__init__(timeseries.bars[start:end],timeseries.closes[start:end])
        self.is_cbl=True
        self.timeseries=timeseries
        self.charttype='Line'
        self.symbol=timeseries.symbol
        self.datasource=timeseries.datasource
        self.timeframe=self.tf=timeseries.timeframe
        self.tf_label=timeseries.tf_label
        self.bars=timeseries.bars
        self.times=timeseries.times
        self.highs=timeseries.highs
        self.lows=timeseries.lows
        
        self.ymax=timeseries.ymax
        self.ymin=timeseries.ymin
        self.setZValue(-1) 

        prs=dict(chartprops)
        linecolor=prs[cfg.linecolor]
        self.setPen(linecolor)
    
    def refresh(self, start=None, end=None):
        self.setData(self.timeseries.bars[start:end],self.timeseries.closes[start:end])

def plot_timeseries(symbol,ct,tf=None,ts=None,session=None,fetch=None,
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

    # Convert dt to x (times to index)  
    def _ti(self,dt):
        tf=self.ts.tf
        t0=self.ts.times[0]
        t1=self.ts.times[-1]
        x0=self.ts.data.index[0]
        x1=self.ts.data.index[-1]

        if dt<t0:
            x=int(x0+(dt-t0)/tf)
        elif dt>t1:
            x=int(x1+(dt-t1)/tf)
        else:                     
            x = np.searchsorted(self.ts.times, dt, side='left')  # Find where `dt` fits
            x = x - 1 if self.ts.times[x] != dt else x  # Adjust where dt==times[x] exactly

        return x

    # Convert x to dt (index to times)
    def _it(self,x):
        return self.ts.extended_times(round(x)) if self.ts is not None else None

    # The function caches self.dt and returns self.x,self.y for position update;
    # also sets ts if given by 'other' and updates x value correspondingly
    def apply(self,other):

        # dt(times) and x(bars) definitions:
        dt = self.dt
        x = self.x
        
        # ts definition
        if other.ts is not None: 
            self.ts=other.ts
        
        # dt(times) takes precedence over x(bars), whether x is None or not
        if other.dt is not None:
            dt=other.dt
            x=self._ti(dt) 
        # if dt is None, set position directly, eg on mouse updates, and update dt
        elif other.x is not None:
            x=other.x
            dt=self._it(x)
        elif dt is not None and other.ts is not None: # update if only new ts is given
            x=self._ti(dt)
        
        # y(price) definition
        y=other.y if other.y is not None else self.y
        

        # Fix dt values outside of allowed range
        if dt is not None:
            if dt>cfg.MAX_REGULAR_TIMESTAMP:
                dt=cfg.MAX_REGULAR_TIMESTAMP-1
            if dt<cfg.MIN_REGULAR_TIMESTAMP:
                dt=cfg.MIN_REGULAR_TIMESTAMP+1

        # returns actionable values for get/setPos()/get/setState(), 
        # simply refreshes if all are None
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



class AltAxisItem(pg.AxisItem):
    """
    AxisItem which displays dates from timestamps in the plot's x-axis.
       
    Can be added to an existing plot e.g. via 
    :func:`setAxisItems({'bottom':axis}) <pyqtgraph.PlotItem.setAxisItems>`.
    """
    def __init__(self, timeseries : Timeseries, *args,
                 chartprops=None, tz=None, **kwargs):
        super().__init__(*args,**kwargs)
        self.ts=timeseries
        self.tz=tz

        if chartprops is not None:
            self.setPen(color=chartprops[cfg.foreground])
            self.setTextPen(color=chartprops[cfg.foreground])
            if chartprops[cfg.font] is not None:
                if isinstance(chartprops[cfg.font],pg.QtGui.QFont):
                    font=chartprops[cfg.font]
                else:
                    font=pg.QtGui.QFont()
                    font.setFamily(chartprops[cfg.font])
                self.setTickFont(font)
            if chartprops[cfg.fontsize] is not None:
                font.setPointSize(chartprops[cfg.fontsize])


    def bar_to_datetime(self,bar):
        """
        Converts a bar number to a datetime object.

        This function is used by the tickStrings() method to generate the text strings
        that are used to label the ticks on the axis. The datetime object is generated
        by converting the bar number to a timestamp using self.ts.extended_times().

        :param bar: The bar number to be converted.
        :return: A datetime object corresponding to the bar number.
        """
        x=self.ts.extended_times(round(bar))

        # Fix x values outside of allowed range
        if x>cfg.MAX_REGULAR_TIMESTAMP:
            x=cfg.MAX_REGULAR_TIMESTAMP-1
        if x<cfg.MIN_REGULAR_TIMESTAMP:
            x=cfg.MIN_REGULAR_TIMESTAMP+1
        
        return datetime.fromtimestamp(x, tz=self.tz)


    def tickStrings(self, values, scale, spacing):
        """
        Generates the text strings that should be associated with the tick values.

        This function is called by pyqtgraph to generate the text strings that are used
        to label the ticks on the axis. The strings are generated by converting the tick
        values into a datetime object using self.bar_to_datetime() and then formatting
        that datetime object using a string format that is determined by the spacing
        of the ticks.

        The generated strings are then returned as a list.
        """
        
        values=[self.bar_to_datetime(v) for v in values]

        format_strings=[]

        try:
            # Process first value separately
            if len(values)>1:
                if values[0].year != values[1].year:
                    format_strings.append(str(values[0].year))
                elif values[0].month != values[1].month:
                    format_strings.append(values[0].strftime("%b"))
                elif values[0].day != values[1].day:
                    format_strings.append(values[0].strftime("%d"))
                else:
                    format_strings.append(values[0].strftime("%H:%M"))
            
            # Process values other than the first
            for i, dt in enumerate(values):
                if i>0 and dt.year != values[i - 1].year:
                    format_strings.append(str(dt.year))
                elif i>0 and dt.month != values[i - 1].month:
                    format_strings.append(dt.strftime("%b"))
                elif i>0 and dt.day != values[i - 1].day:
                    format_strings.append(dt.strftime("%d"))
                elif i>0:
                    format_strings.append(dt.strftime("%H:%M"))
        
        except ValueError: # Windows can't handle dates before 1970 as per pg
            format_strings.append('')

        return format_strings


    def tickValues(self, minVal, maxVal, size):
        """
        Compute the values used for tick marks on this axis.
        Select major ticks only.

        :param minVal: The minimum value visible on the axis.
        :param maxVal: The maximum value visible on the axis.
        :param size: The total size of the axis in pixels.
        :return: A list of tuples, each tuple containing a list of x-values and a scaling factor.
        """
        values=super().tickValues(minVal,maxVal,size)

        return [values[0]]


####################
# Auxiliary classes
####################
class TsSliced:
    """
    A class representing a slice of Timeseries data.
    
    Parameters
    ----------
    ts : Timeseries
        The Timeseries object to be sliced.
    ts_slice : slice
        The slice to be applied to the Timeseries data.
    
    Attributes
    ----------
    bars : numpy.ndarray
        The array of tick values of the sliced data.
    data : pandas.DataFrame
        The DataFrame of the sliced data.
    symbol : str
        The symbol of the Timeseries.
    timeframe : str
        The timeframe of the Timeseries.
    """
    def __init__(self, ts : Timeseries, ts_slice : slice):
        
        x=len(ts.data)

        if ts_slice:
            assert ts_slice.step is None, "ts_slice step is not supported"
        
        if ts_slice.start and x <= abs(ts_slice.start):
                ts_slice.start = None
        
        if ts_slice.stop and x <= abs(ts_slice.stop):
            ts_slice.stop = None
        
        self.bars=ts.bars[ts_slice]
        self.data=ts.data[ts_slice].reset_index(drop=True)
        
        self.symbol=ts.symbol
        self.timeframe=self.tf=ts.timeframe
    
    @property
    def times(self):
        return self.data[cfg.TIMES].to_numpy()

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
    

class TsStub:
    ''' 
    Stub for Timeseries class
    '''
    def __init__(self, df):
        self.data = df

    @property
    def times(self):
        return self.data[cfg.TIMES].to_numpy()

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