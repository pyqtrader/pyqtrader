import PySide6
import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui
import cfg

from _debugger import _print,_p,_pc,_printcallers

from pyqtgraph import PlotItem
def listItems(self):
    return self.items[:]
PlotItem.listItems=listItems

#WHEEL EVENT OVERRIDE
from pyqtgraph import Point
from pyqtgraph import functions as fn

def wheelEvent(self, ev, axis=None): #edited to supress y-axis scaling
        # if axis in (0, 1):
        #     mask = [False, False]
        #     mask[axis] = self.state['mouseEnabled'][axis]
        # else:
        #     mask = self.state['mouseEnabled'][:]
        mask=[True,False] #added
        s = 1.02 ** (ev.delta() * self.state['wheelScaleFactor']) # actual scaling factor
        s = [(None if m is False else s) for m in mask]
        center = Point(fn.invertQTransform(self.childGroup.transform()).map(ev.pos()))

        self._resetTarget()
        self.scaleBy(s, center)
        ev.accept()
        self.sigRangeChangedManually.emit(mask)

pg.ViewBox.wheelEvent=wheelEvent
##############

class AltViewBox(pg.ViewBox): # unused/reserved if patcher() or wheelEvent() override fails 
    def __init__(self, *args, **kwds):
        pg.ViewBox.__init__(self, *args, **kwds)

    def wheelEvent(self, ev, axis=None):
        initialRange = self.viewRange()
        pg.ViewBox.wheelEvent(self,ev,axis)
        self.setYRange(initialRange[0][0],initialRange[0][1])
        # self.setYRange(0,10)
#################

#DATEAXIS OVERRIDE
from pyqtgraph.graphicsItems.DateAxisItem import DateAxisItem
from pyqtgraph.graphicsItems.DateAxisItem import utcfromtimestamp
from pyqtgraph.graphicsItems.DateAxisItem import SEC_PER_YEAR

class AltDateAxisItem(DateAxisItem):

    def __init__(self, times, last_tick,tf,chartprops=None):
        super().__init__()
        self.times=times
        self.last_tick=last_tick
        self.tf = tf
        if chartprops is not None:
            self.setPen(color=chartprops[cfg.foreground])
            self.setTextPen(color=chartprops[cfg.foreground])
            if chartprops[cfg.font] is not None:
                if isinstance(chartprops[cfg.font],QtGui.QFont):
                    font=chartprops[cfg.font]
                else:
                    font=QtGui.QFont()
                    font.setFamily(chartprops[cfg.font])
                self.setTickFont(font)
            if chartprops[cfg.fontsize] is not None:
                font.setPointSize(chartprops[cfg.fontsize])

    def tickStrings(self, values, scale, spacing):
        tickSpecs = self.zoomLevel.tickSpecs
        tickSpec = next((s for s in tickSpecs if s.spacing == spacing), None)

        upvalues=[]

        dadj=1*self.tf if self.tf in cfg.ADJUSTED_TIMEFRAMES else 0 #Timeframe adjustments due to pyqtgraph adding additional tick 
        #to designate the month/year and shifting the plot 1 tick lefwards on that timeframe
        for v in values:
            if v>=0:
                try:       
                    upvalues.append(self.times[int(v//self.tf)])
                except Exception:
                    upvalues.append(self.times[-1]+v-self.last_tick+dadj)
            else:
                upvalues.append(self.times[0]+v)

        
        try:
            dates = [utcfromtimestamp(v - self.utcOffset) for v in upvalues]
        except (OverflowError, ValueError, OSError):
            # should not normally happen
            return ['%g' % ((v-self.utcOffset)//SEC_PER_YEAR + 1970) for v in upvalues]

        formatStrings = []
        for x in dates:  
            try:
                s = x.strftime(tickSpec.format)

                if '%f' in tickSpec.format:
                    # we only support ms precision
                    s = s[:-3]
                elif '%Y' in tickSpec.format:
                    s = s.lstrip('0')
                formatStrings.append(s)
            except ValueError:  # Windows can't handle dates before 1970
                formatStrings.append('')

        return formatStrings
#################

#PAINT ELLIPSE OVERRIDE

def paint_ellipse_override(self, p, opt, widget): #override
    r = self.boundingRect()
    p.setRenderHint(QtGui.QPainter.Antialiasing)
    p.setPen(self.currentPen)
    
    p.scale(r.width(), r.height())## workaround for GL bug
    if r.width()!=0 and r.height()!=0: #workaround division by zero error messaging in pg
        r = QtCore.QRectF(r.x()/r.width(), r.y()/r.height(), 1,1)
    else:
        pass
    
    p.drawEllipse(r)

pg.EllipseROI.paint=paint_ellipse_override
###################

#HOVER DISCARD REVERTED IN POLYLINEROI TO ENSURE DRAGS BY DRAGGING THE SEGMENTS THEMSELVES RATHER THAN THE BODY OF THE ROI
from pyqtgraph import LineSegmentROI
pg.graphicsItems.ROI._PolyLineSegment.hoverEvent=LineSegmentROI.hoverEvent
#Poly roi handle supression:
pg.graphicsItems.ROI._PolyLineSegment.mouseDragEvent=lambda *args,**kwargs: None
###################

#Get rid of Handle menu
from pyqtgraph.graphicsItems.ROI import Handle
Handle.buildMenu=lambda *args: None
Handle.raiseContextMenu=lambda *args: None

#Export override ection
from PIL import ImageShow
import warnings
import subprocess
import os
import tempfile
def show_file_override(self, path=None, **options):
        """
        Display given file.
        Before Pillow 9.1.0, the first argument was ``file``. This is now deprecated,
        and ``path`` should be used instead.
        """
        if path is None:
            if "file" in options:
                warnings.warn(
                    "The 'file' argument is deprecated and will be removed in Pillow "
                    "10 (2023-07-01). Use 'path' instead.",
                    DeprecationWarning,
                )
                path = options.pop("file")
            else:
                raise TypeError("Missing required argument: 'path'")
        fd, temp_path = tempfile.mkstemp()
        with os.fdopen(fd, "w") as f:
            f.write(path)
        with open(temp_path) as f:
            command = self.get_command_ex(path, **options)[0]
            #override - insert sleep 20 to ensure that the tmp file is not deleted before it is opened
            subprocess.Popen(
                ["im=$(cat);" + command + " $im; sleep 20; rm -f $im"], shell=True, stdin=f
            )
        os.remove(temp_path)
        return 1

ImageShow.UnixViewer.show_file=show_file_override

###################
#Supress handles when roi is unselected
from pyqtgraph.Qt import QtWidgets

def setSelected_override(self, s):
    QtWidgets.QGraphicsItem.setSelected(self, s)
    #print "select", self, s
    if s and self.translatable:
        for h in self.handles:
            h['item'].show()
    else:
        for h in self.handles:
            h['item'].hide()

pg.graphicsItems.ROI.ROI.setSelected=setSelected_override
######################
#add setFontSize() function to pg.TextItem
def setFontSize_TextItem(self,size):
    font=self.textItem.font()
    font.setPointSize(int(size))
    self.setFont(font)

pg.TextItem.setFontSize=setFontSize_TextItem
########################