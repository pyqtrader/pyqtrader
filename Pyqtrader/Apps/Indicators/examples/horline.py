from Pyqtrader.Apps import lib
from pyqtgraph import QtGui

PQitemtype='HorizontalLineIndicator'

LINECOLOR='orange'
LINEWIDTH=0.5
LINESTYLE=lib.DotLine
BARSBACK=2

PQkwords=dict(color=LINECOLOR,width=LINEWIDTH,style=LINESTYLE) #an alternative is PQtline.set_properties(width=LINEWITH...) in PQinitf

def PQinitf(PQhline):
    s=PQhline.series
    times=lib.normalised_series(s,earliest=BARSBACK)
    highs=lib.normalised_series(s,'highs',earliest=BARSBACK)
    vls=[times[1],highs[1]]
    PQhline.set_data(vls)
    PQhline.set_selectable(True)
    PQhline.textY.setColor(QtGui.QColor(0,0,0,0)) #set the lable to transparent