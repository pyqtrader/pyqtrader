from pandas_ta import sma
from cfg import OPENS, HIGHS, LOWS, CLOSES

PQitemtype='CurveIndicator'

MODE=CLOSES
PERIOD=20
WIDTH=1
COLOR='#ff0000'

PQkwords=dict(width=WIDTH,color=COLOR)

def PQcomputef(PQitem):
    # Timeseries dataframe:
    df=PQitem.timeseries.data
    
    # Calculate only 2 last values if the entire sma series has already been cached,
    # otherwise calculate the entire sma series
    ins=df[MODE].iloc[-2-PERIOD if PQitem.cache_event else None:]
    
    return sma(ins,length=PERIOD).dropna().to_numpy()

def PQtooltip(PQitem):
    index,xtext,ytext,precision=PQitem.tooltipinfo
    notes='({},{})'.format(MODE,PERIOD)
    res='{}{}\n{}\n{:.{pr}f}'.format("SMA",notes,xtext,ytext,pr=precision)
    return res

