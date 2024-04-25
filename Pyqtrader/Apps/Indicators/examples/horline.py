from cfg import SOLIDLINE, DOTLINE, DASHLINE, DASHDOTLINE, DASHDOTDOTLINE
from pyqtgraph import QtGui

PQitemtype='HorizontalLineIndicator'

LINECOLOR='orange'
LINEWIDTH=0.5
LINESTYLE=DOTLINE
CANDLE_INDEX=1

PQkwords=dict(color=LINECOLOR,width=LINEWIDTH,style=LINESTYLE) #an alternative is PQtline.set_properties(width=LINEWITH...) in PQinitf

def PQinitf(PQhline):
    # For convenience, reverse the dataframe to address the elements from the
    # latest to earliest
    df=PQhline.timeseries.data[::-1].reset_index(drop=True)
    
    # Pass the candle's datetime and high coordinates to the placement function
    vls=[df.t[CANDLE_INDEX],df.h[CANDLE_INDEX]]
    PQhline.set_data(vls)
    PQhline.set_selectable(True)
    PQhline.textY.setColor(QtGui.QColor(0,0,0,0)) #set the lable to transparent