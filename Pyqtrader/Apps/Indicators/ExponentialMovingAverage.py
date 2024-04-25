from pandas_ta import ema
from cfg import OPENS, HIGHS, LOWS, CLOSES

PQitemtype='CurveIndicator'

MODE=CLOSES
PERIOD=20
WIDTH=1
COLOR='cyan'

PQkwords=dict(width=WIDTH,color=COLOR)

def PQinitf(PQitem):
    # Create a persistent cache variable to store starting value 
    # for the EMA calculation.  Only needed if caching is used
    PQitem.Cache_Value = None

def PQcomputef(PQitem):
    # Timeseries dataframe
    df=PQitem.timeseries.data
    
    ins=df[MODE]
            
    # Cache processing for the last 2 bars
    if PQitem.cache_event and PQitem.Cache_Value is not None:
        ins=ins[-2-PQitem.ts_diff-PERIOD:] # caching array

        # pandas_ta does not support caching, therefore manufacture input data to trick
        # ta.ema() into accepting the cached ema value (PQItem.Cache_Value) as the
        # starting value for the 2 recalculated bars
        ins=ins.copy() # ensures that the source data is not modified to avoid graphical artifacts
        ins.iloc[:PERIOD]=PQitem.Cache_Value

        yvals=ema(ins,length=PERIOD,sma=True).dropna().to_numpy()

    # Initialisation/refresh when cache is unformed/needed to be refreshed
    else:
        yvals=ema(ins,length=PERIOD).dropna().to_numpy()

    return yvals

def PQtooltip(PQitem):
    index,xtext,ytext,precision=PQitem.tooltipinfo
    notes='({},{})'.format(MODE,PERIOD)
    res='{}{}\n{}\n{:.{pr}f}'.format("EMA",notes,xtext,ytext,pr=precision)
    return res