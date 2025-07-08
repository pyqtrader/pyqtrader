import PySide6
from PySide6.QtCore import QPointF, QRectF
from PySide6 import QtGui, QtWidgets
import pyqtgraph as pg
from pyqtgraph import Point
import pandas as pd
import dataclasses as dc
from datetime import datetime
import typing

from timeseries import dtPoint
from charttools import to_pips, to_points, simple_message_box
import cfg

from _debugger import *

class TradeType:
    buy=0
    sell=1

    @staticmethod
    def name(x):
        assert x==TradeType.buy or x==TradeType.sell, "Invalid trade type"

        return "Buy" if x==TradeType.buy else "Sell"

@dc.dataclass
class Trade:

    id_number: int = None
    symbol: str = None
    trade_type: TradeType = None
    volume: float = None
    entry: dtPoint = dc.field(default_factory=dtPoint)
    close: dtPoint = dc.field(default_factory=dtPoint)
    comment: str = None

    @property
    def profit(self):
        if any(x is None for x in [self.symbol,self.entry.y, self.close.y, self.volume]):
            return None
        sign=1 if self.trade_type==TradeType.buy else -1
        return (self.close.y-self.entry.y)*to_points(self.symbol)*self.volume*sign

    @property
    def pips(self):
        if any(x is None for x in [self.symbol, self.entry.y, self.close.y]):
            return None
        sign=1 if self.trade_type==TradeType.buy else -1
        return (self.close.y-self.entry.y)*to_pips(self.symbol)*sign
    
    # Returns True if z is within the entry-close rectangle
    def contains(self, z: Point):
        z=QPointF(z.x(),z.y())
        rect=QRectF(QPointF(*self.entry.xy()),QPointF(*self.close.xy()))
        return True if rect.contains(z) else False
    
    def info(self):
        s = ""
        if self.id_number is not None:
            s+=f"#: {self.id_number}\n"
        s+=f"{self.symbol} {TradeType.name(self.trade_type)} "
        s+=f"{self.volume} lots\n" if self.volume is not None else "\n"
        s+=f"Open time: {datetime.fromtimestamp(self.entry.dt)}, price: {self.entry.y}\n"
        s+=f"Close time: {datetime.fromtimestamp(self.close.dt)}, price: {self.close.y}\n"
        s+=f"Pips: {round(self.pips,1)}"
        if self.profit is not None:
            s+=f"\nProfit: {round(self.profit,2)}" 
        if self.comment is not None:
            s+=f"\nComment: {self.comment}" 

        return s.strip()

@dc.dataclass
class TradeRecord:

    record: typing.List[Trade] | None = dc.field(default_factory=list)

    @staticmethod
    def read_from_csv(filepath):
        df=pd.read_csv(filepath)

        # Ensure that the dataframe contains all required columns (id_number, volume and comment are not obligatory)
        tr_set=set(cfg.TRADE_RECORD.values())
        tr_set.remove(cfg.TRADE_RECORD['id_number'])
        tr_set.remove(cfg.TRADE_RECORD['volume'])
        tr_set.remove(cfg.TRADE_RECORD['comment'])
        if not tr_set-set(df.columns)==set(): 
            simple_message_box("Backtest", 
                               text=f"Source file {filepath} misses some required columns",
                               icon=QtWidgets.QMessageBox.Warning)
            raise ValueError(f"Source file {filepath} misses some required columns")

        if not df[cfg.TRADE_RECORD['trade_type']].isin([TradeType.buy, TradeType.sell]).all():
            simple_message_box("Backtest", 
                               text=f"Source file {filepath} contains invalid trade types",
                               icon=QtWidgets.QMessageBox.Warning)
            raise ValueError(f"Source file {filepath} contains invalid trade types")
            
        record=[]
        for i,row in df.iterrows():
            
            trade=Trade()
            # Not required, only include if present
            if (h:=cfg.TRADE_RECORD['id_number']) in df.columns:
                trade.id_number=row[h]
            else:
                trade.id_number=i+1
            if (h:=cfg.TRADE_RECORD['volume']) in df.columns: 
                trade.volume=row[h]
            
            # Required fields
            trade.symbol=row[cfg.TRADE_RECORD['symbol']]
            
            h=cfg.TRADE_RECORD['trade_type']
            trade.trade_type=row[h]
            
            trade.entry.dt=row[cfg.TRADE_RECORD['open_time']]            
            trade.entry.y=row[cfg.TRADE_RECORD['open_price']]
            trade.close.dt=row[cfg.TRADE_RECORD['close_time']]            
            trade.close.y=row[cfg.TRADE_RECORD['close_price']]

            if (h:=cfg.TRADE_RECORD['comment']) in df.columns: 
                trade.comment=row[h]

            record.append(trade)

        return TradeRecord(record)


    def select(self, name, value):
        selection=TradeRecord()
        for r in self.record:
            for field in dc.fields(r):
                if field.name==name and getattr(r,field.name)==value:
                    selection.record.append(r)
        
        return selection


    def apply_timeseries(self,ts):
        
        for trade in self.record:
            trade.entry=trade.entry.apply(dtPoint(ts=ts))
            trade.close=trade.close.apply(dtPoint(ts=ts))


class DrawTradeRecord (pg.GraphicsObject):
    def __init__(self, plt, trade_record : TradeRecord | str | None = None, caller=None):
        pg.GraphicsObject.__init__(self)
        
        self.is_persistent=True
        self.plt=plt
        self.picture=None
        self.trade_record=None

        if type(trade_record) is str:
            self.set_props(dict(filename=trade_record))
        elif isinstance(trade_record,TradeRecord):
            self.trade_record=trade_record
            self.selected_record=self.trade_record.select('symbol',plt.symbol)
            self.selected_record.apply_timeseries(plt.chartitem.timeseries)
        elif trade_record is not None:
            raise TypeError(f'trade_record can be TradeRecord, str or NoneType, but{type(trade_record)} was given')

        if self.picture is None:    
            self.generatePicture()
        plt.addItem(self)
        plt.sigTimeseriesChanged.connect(self.ts_change)
    
    def mouseClickEvent(self, ev):
        if ev.button() == pg.QtCore.Qt.LeftButton:
            for r in self.selected_record.record:
                if r.contains(ev.pos()):
                    simple_message_box("Trade",r.info())
                    break
        elif ev.button() == pg.QtCore.Qt.RightButton:
            menu = pg.QtWidgets.QMenu()
            menu.addSection("Backtest")
            refresh_action = menu.addAction("Refresh")
            menu.addSeparator()
            remove_action = menu.addAction("Remove")
            action = menu.exec(ev.screenPos().toQPoint())
            
            if action == remove_action:
                self.plt.sigTimeseriesChanged.disconnect(self.ts_change)
                self.plt.removeItem(self)
            elif action == refresh_action:
                self.refresh()
    
    def ts_change(self,ts):
        self.selected_record=self.trade_record.select('symbol', ts.symbol)
        self.selected_record.apply_timeseries(ts)

    def refresh(self):
        self.set_props(self.props)
        self.generatePicture()
        self.plt.vb.update()

    def set_props(self,props):
        if not props:   
            return
        self.props=props
        self.trade_record=TradeRecord.read_from_csv(props['filename'])
        self.selected_record=self.trade_record.select('symbol', self.plt.symbol)

        if not self.selected_record.record:
            simple_message_box("Backtest", 
                text=f"No {self.plt.symbol} found in the source file.\nCheck the symbol name.",
                icon=QtWidgets.QMessageBox.Warning)
            return

        self.selected_record.apply_timeseries(self.plt.chartitem.timeseries)
        self.generatePicture()

        return

    def save_props(self):
        return self.props

    def save_props(self):
        if hasattr(self,'props'):
            return self.props
        else:
            return None
    
    def generatePicture(self):
        self.picture= pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        style=cfg.LINESTYLES[cfg.DASHDOTDOTLINE]
        if self.trade_record:
            for trade in self.selected_record.record:
                e=QPointF(*trade.entry.xy())
                c=QPointF(*trade.close.xy())
                p.setPen(pg.mkPen('r' if trade.pips<0 else 'g', width=1.5,style=style))
                p.drawLine(e,c)

                m=QPointF(0,1/to_pips(trade.symbol))
                if trade.trade_type==TradeType.sell: m=-m
                p.drawLines([e,e-m,c,c+m])
                
        p.end()


    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)
    
    def boundingRect(self):
        return QRectF(self.picture.boundingRect())
    
   
    def shape(self):
        p = pg.QtGui.QPainterPath()
        if not self.trade_record:
            return p
        
        # Ensure mouse interactions over the entire painted shape
        for trade in self.trade_record.record:
            h1 = Point(*trade.entry.xy())
            h2 = Point(*trade.close.xy())
            dh = h2-h1
            if dh.length() == 0:
                return p
            pxv = self.pixelVectors(dh)[1]
            if pxv is None:
                return p
                
            pxv *= 4

            p.moveTo(h1+pxv)
            p.lineTo(h2+pxv)
            p.lineTo(h2-pxv)
            p.lineTo(h1-pxv)
            p.lineTo(h1+pxv)
        
        return p

