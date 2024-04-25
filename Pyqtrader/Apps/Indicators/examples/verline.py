from cfg import SOLIDLINE, DOTLINE, DASHLINE, DASHDOTLINE, DASHDOTDOTLINE
from pyqtgraph import QtGui

PQitemtype='VerticalLineIndicator'

LINECOLOR='orange'
LINEWIDTH=0.5
LINESTYLE=DASHDOTDOTLINE
CANDLE_INDEX=1

PQkwords=dict(color=LINECOLOR,width=LINEWIDTH,style=LINESTYLE) #an alternative is PQtline.set_properties(width=LINEWIDTH...) in PQinitf

def PQinitf(PQvline):
    # For convenience, reverse the datetimes array to address the elements from the
    # latest to earliest
    times=PQvline.timeseries.times[::-1]
    
    # Pass the candle's datetime to the placement function
    PQvline.set_data(times[CANDLE_INDEX])
    PQvline.set_selectable(False)
    PQvline.textX.setColor(QtGui.QColor(0,0,0,0)) #set the lable to transparent