from Pyqtrader.Apps import lib
from pyqtgraph import QtGui

PQitemtype='VerticalLineIndicator'

UPTRENDCOLOR='g'
DOWNTRENDCOLOR='orange'
TRENDWIDTH=2
NONTRENDWIDTH=1
TRENDSTYLE=lib.SolidLine
NONTRENDSTYLE=lib.DotLine
BARSBACK=2

NT_PROPS=dict(width=NONTRENDWIDTH,style=NONTRENDSTYLE)
T_PROPS=dict(width=TRENDWIDTH,style=TRENDSTYLE)

PQkwords=dict(width=TRENDWIDTH) #an alternative is PQtline.set_properties(width=TRENDWITH) in PQinitf

def PQinitf(PQvline):
    s=PQvline.series
    times=lib.normalised_series(s,earliest=BARSBACK)
    PQvline.set_data(times[1])
    PQvline.set_selectable(False)
    PQvline.textX.setColor(QtGui.QColor(0,0,0,0)) #set the lable to transparent