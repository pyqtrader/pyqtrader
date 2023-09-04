from Pyqtrader.Apps.lib import *

PQitemtype='CurveIndicator'

MODE='Close'
PERIOD=20
WIDTH=1
COLOR='#ff0000'

PQkwords=dict(width=WIDTH,color=COLOR)

def PQcomputef(PQitem):
    series=PQitem.series
    if PQitem.cache_event:     
        st=-2-PERIOD
    else:
        st=None

    ins=inputs(series,mode=MODE,start=st)
    yvals=calc_sma(ins,PERIOD)
    
    return yvals

def PQtooltip(PQitem):
    index,xtext,ytext,precision=PQitem.tooltipinfo
    notes='({},{})'.format(MODE,PERIOD)
    res='{}{}\n{}\n{:.{pr}f}'.format("SMA",notes,xtext,ytext,pr=precision)
    return res

