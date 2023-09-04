from Pyqtrader.Apps.lib import *

PQitemtype='CurveIndicator'

MODE='Close'
PERIOD=20
WIDTH=1
COLOR='cyan'

PQkwords=dict(width=WIDTH,color=COLOR)
PQcache0=dict(v0=None)

def PQcomputef(PQitem):
    series=PQitem.series
    if PQitem.cache_event:     
        st=-3-PQitem.ts_diff
    else:
        st=None

    ins=inputs(series,mode=MODE,start=st)
    yvals=calc_ema(ins,PERIOD,v0=PQitem.cache0['v0'])
    PQitem.cache0['v0']=yvals[-3]
    
    return yvals

def PQtooltip(PQitem):
    index,xtext,ytext,precision=PQitem.tooltipinfo
    notes='({},{})'.format(MODE,PERIOD)
    res='{}{}\n{}\n{:.{pr}f}'.format("EMA",notes,xtext,ytext,pr=precision)
    return res