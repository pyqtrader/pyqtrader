from Pyqtrader.Apps import lib
from pyqtgraph import QtGui

PQitemtype='VerticalLineIndicator'

LINECOLOR='orange'
LINEWIDTH=0.5
LINESTYLE=lib.DashDotDotLine
BARSBACK=2

PQkwords=dict(color=LINECOLOR,width=LINEWIDTH,style=LINESTYLE) #an alternative is PQtline.set_properties(width=TRENDWITH) in PQinitf

def PQinitf(PQvline):
    s=PQvline.series
    times=lib.normalised_series(s,earliest=BARSBACK)
    PQvline.set_data(times[1])
    PQvline.set_selectable(False)
    PQvline.textX.setColor(QtGui.QColor(0,0,0,0)) #set the lable to transparent