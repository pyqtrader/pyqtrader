from Pyqtrader.Apps import lib
from pyqtgraph import QtGui

PQitemtype='HorizontalLineIndicator'

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

def PQinitf(PQhline):
    s=PQhline.series
    times=lib.normalised_series(s,earliest=BARSBACK)
    highs=lib.normalised_series(s,'highs',earliest=BARSBACK)
    vls=[times[1],highs[1]]
    PQhline.set_data(vls)
    PQhline.set_selectable(True)
    PQhline.textY.setColor(QtGui.QColor(0,0,0,0)) #set the lable to transparent