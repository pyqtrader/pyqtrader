import PySide6
from PySide6 import QtCore, QtWidgets

import os, inspect, subprocess
import dataclasses
import typing
import pyqtgraph as pg
import numpy as np
import pandas as pd

import cfg
import drawings
from api import invoker

from _debugger import *


@dataclasses.dataclass
class PenProps:
    width: float = 1
    color: str = None
    style: QtCore.Qt.PenStyle | str = QtCore.Qt.SolidLine
    flavors: dict | None = None # User defined attributes

    
    def __post_init__(self):
        if isinstance(self.style, str):
            self.style=self.convert_style_string_to_enum(self.style)

    @classmethod
    def convert_style_string_to_enum(cls, style: str) -> QtCore.Qt.PenStyle:
        """Convert string style to QtCore.Qt.PenStyle enum object using cfg.py dictionaries"""

        assert style in cfg.LINESTYLES.keys(), \
        f"Invalid style string: {style!r}. Available styles are {list(cfg.LINESTYLES.keys())}"

        return cfg.LINESTYLES[style]
        
    def convert_style_enum_to_string(self, style: QtCore.Qt.PenStyle | None = None) -> str:
        """Convert QtCore.Qt.PenStyle enum object to string style using cfg.py dictionaries"""
        if style is None:
            style = self.style
        return next(key for key, value in cfg.LINESTYLES.items() if value == style)


class CoordBuffer:
    def __init__(self, data: typing.Union[typing.List[tuple[int, float]], np.ndarray, pd.DataFrame, None] = None,
                 penprops: PenProps | None = None):
        
        assert isinstance(data, (list, np.ndarray, pd.DataFrame, type(None))), \
            f"CoordBuffer.__init__: expected data to be one of list, np.ndarray, pd.DataFrame, None, got {type(data)}"

        self._data=None #property data holder
        self._painted_data=None # holder of data for painting
        self._bRect=QtCore.QRectF()
        self.data = data
        self.penprops = penprops
        self.pen=self.make_pen()
    
    # The property approach doubles the memory usage, but improves paint() and 
    # boundingRect() performance by over an order of magniture
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, data):
        self._data = data
        self._painted_data = self.convert_data_to_qpoints()


    def make_pen(self):
        return pg.mkPen(width=self.penprops.width, color=self.penprops.color, style=self.penprops.style)

    def convert_data_to_qpoints(self) -> typing.List[QtCore.QPointF]:
        qpoints = []
        if isinstance(self.data, list):
            qpoints = [QtCore.QPointF(x, y) for x, y in self.data]
        elif isinstance(self.data, np.ndarray):
            qpoints = [QtCore.QPointF(x, y) for x, y in self.data]
        elif isinstance(self.data, pd.DataFrame):
            qpoints = [QtCore.QPointF(row[0], row[1]) for row in self.data.itertuples(index=False)]
        return qpoints


class CustomItem(pg.GraphicsObject):
    """
    CustomItem is an abstract class derived from pyqtgraph's GraphicsObject.
    It offers customization options for graphics rendering, such as width, color, and style.
    The class supports maintaining coordinate buffers and handling right-click events.
    """

    def __init__(self, plt : drawings.AltPlotWidget, **kwargs):
        super().__init__()
        self.is_persistent = True
        self.is_new=True
        self.penprops = PenProps(
            width=kwargs.get('width', 1),
            color=kwargs.get('color', None),
            style=kwargs.get('style', QtCore.Qt.SolidLine),
            flavors=kwargs.get('flavors', None)
        )

        assert isinstance(self.penprops.color, (str, tuple, type(None))), \
            f"""{self.__class__.__name__}: Color must be a str (hex or name) 
            or tuple or None, not {type(self.penprops.color).__name__} 
            to ensure JSON serializability"""

        self.coord_buffers = []

        self.plt = plt
        self.timeseries=self.plt.chartitem.timeseries
        self._timeseries_length_stored=len(self.timeseries.closes)
        self.plt.addItem(self)


    def add_coord_buffer(self, data: typing.List[typing.Tuple[int, float]]|None = None,
                            penprops: PenProps|None=None):
        cb=CoordBuffer(None or data, penprops or self.penprops)
        self.coord_buffers.append(cb)
        self._bRect = self._calculateRectFromCoordBuffers(self.coord_buffers)
        return cb

    def update_coord_buffer(self, cb: CoordBuffer| int, data: typing.List[typing.Tuple[int, float]]|None = None,
                            penprops: PenProps|None=None):
        if isinstance(cb, CoordBuffer):
            cb.data = data or cb.data            
        else:
            cb=self.coord_buffers[cb]
            cb.data = data or cb.data

        cb.penprops = penprops or cb.penprops
        cb.pen=cb.make_pen()
        
        self._bRect = self._calculateRectFromCoordBuffers(self.coord_buffers)
        
        return cb

    def clear_coord_buffers(self):
        self.coord_buffers = []

    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.MouseButton.RightButton:
            self.right_clicked(ev)
    
    # restore props from disk
    def set_props(self,props):
        bprops=props['buffers']       
        for i,bp in enumerate(bprops):
            style=bp['style']
            width=bp['width']
            color=bp['color']
            flavors=bp['flavors']
            penprops=PenProps(width=width,color=color,
                            style=style,flavors=flavors)
            self.update_coord_buffer(i,penprops=penprops)
                
        self.is_new=False
    
    # save props to disk
    def save_props(self):
        props=dict(buffers=[])
        for cb in self.coord_buffers:
            buffer_props = {
                'style': cb.penprops.convert_style_enum_to_string(),
                'width': cb.penprops.width,
                'color': cb.penprops.color,
                'flavors': cb.penprops.flavors
            }
            props['buffers'].append(buffer_props)
            
        props['fullpath'] = os.path.abspath(inspect.getfile(self.__class__))
        return props

    def right_clicked(self,ev):
        ev_pos=ev.screenPos()
        contextMenu=QtWidgets.QMenu()
        contextMenu.addSection(self.__class__.__module__.split('/')[-1])
        refreshAct=contextMenu.addAction('Refresh')
        editAct=contextMenu.addAction('Edit')
        contextMenu.addSeparator()
        remAct=contextMenu.addAction('Remove')
        action=contextMenu.exec(QtCore.QPoint(ev_pos.x(),ev_pos.y()))
        if action==remAct:
            self.remove_act()
        elif action==refreshAct:
            self.refresh_act()
        elif action==editAct:
            subprocess.run(['xdg-open', os.path.abspath(inspect.getfile(self.__class__))])

    def refresh_act(self):
        plt=self.getViewWidget()
        plt.removeItem(self)
        invoker(self.plt.mwindow.mdi,self.__class__.__module__.split('/')[-1],os.path.abspath(inspect.getfile(self.__class__)))

    def remove_act(self):
        plt=self.getViewWidget()
        plt.removeItem(self)

    def paint(self, p, *args):
        raise NotImplementedError  

    @staticmethod
    def _calculateRectFromCoordBuffers(coord_buffers):

        if any(x.data is None for x in coord_buffers):
            return QtCore.QRectF()

        cbuffers=[x.data.to_numpy() if isinstance(x.data,pd.DataFrame) else x.data for x in coord_buffers]

        xmin = min(x for x, y in (coord for coord_buffer in cbuffers for coord in coord_buffer))
        xmax = max(x for x, y in (coord for coord_buffer in cbuffers for coord in coord_buffer))
        ymin = min(y for x, y in (coord for coord_buffer in cbuffers for coord in coord_buffer))
        ymax = max(y for x, y in (coord for coord_buffer in cbuffers for coord in coord_buffer))

        return QtCore.QRectF(xmin, ymin, xmax - xmin, ymax - ymin)

    # Ensure that self._bRect is updated whenever self.coord_buffers changes
    # Currently, no additional logic to handle this is implemented
    def boundingRect(self):
        if not self.coord_buffers:
            return QtCore.QRectF()
        
        return self._bRect


class PolylineCustomItem(CustomItem):

    def paint(self, p, *args):
        if self.coord_buffers:
            for coord_buffer in self.coord_buffers:
                p.setPen(coord_buffer.pen)
                p.drawPolyline(coord_buffer._painted_data)


class MultiLineCustomItem(CustomItem):
    
    def paint(self, p, *args):
        if self.coord_buffers:
            for coord_buffer in self.coord_buffers:
                p.setPen(coord_buffer.pen)
                p.drawLines(coord_buffer._painted_data)


class CustomPolyitem(CustomItem):
    """Abstract class for custom poly items. It provides ability to create subitems."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.subitems=[]

    def create_subitem(self, itype, *args, **kwargs):
        item=itype(*args, **kwargs)
        if hasattr(item, 'is_persistent'):
            item.is_persistent=False
        if hasattr(item, "is_selectable"):
            item.is_selectable=False
        item.setParent(self)
        self.subitems.append(item)
        plt=self.getViewWidget()
        plt.addItem(item)

        # Connect the mouse click event of the subitem to a function
        item.mouseClickEvent = self.mouseClickEvent
        
        return item
    
    def refresh_act(self):
        for si in self.subitems.copy():
            self.remove_subitem(si)
        return super().refresh_act()

    def remove_subitem(self,si):
        si.setParent(None)
        self.subitems.remove(si)
        plt=self.getViewWidget()
        plt.removeItem(si)
    
    def clear_subitems(self):
        for si in list(self.subitems):
            self.remove_subitem(si)

    def remove_act(self):
        for si in self.subitems.copy():
            self.remove_subitem(si)
        super().remove_act()

    def paint(self, p, *args):
        pass

# Converts polyline to multi-segment line for drawLines() 
def points_to_segments(values : list | np.ndarray | pd.DataFrame, sort_by: int =0,
                       slicing=slice(1,-1),
                       left_slide: float = 0, right_slide: float = 0) -> pd.DataFrame:
    
    assert isinstance(values, (list, np.ndarray, pd.DataFrame)), "Input values must be a list, numpy array, or pandas DataFrame"

    assert isinstance(left_slide,int) and isinstance(right_slide,int), "left_slide and right_slide must be integers"

    if not isinstance(values, pd.DataFrame):
        df = pd.DataFrame(values)
    else:
        df=values.copy()

    if df.duplicated().any():
        duplicates = df[df.duplicated()]
        print("Duplicates found:\n", duplicates)
        raise ValueError("Input values contain duplicates")

    df = pd.concat([df, df], ignore_index=True).dropna()
    df = df.sort_values(by=df.columns[sort_by]).reset_index(drop=True)
    
    if left_slide:
        df.iloc[::2, 0] -= left_slide
    if right_slide:
        df.iloc[1::2, 0] += right_slide

    if isinstance(values, pd.DataFrame):
        return df[slicing]

    df = df.to_numpy()
    if not isinstance(values, np.ndarray):
        df=df.tolist()

    return df[slicing]

# Converts polyline to 2-point dots that can be streched to make dashes
def points_to_dots(*args, **kwargs):
    return points_to_segments(*args, slicing=slice(None,None),**kwargs)

