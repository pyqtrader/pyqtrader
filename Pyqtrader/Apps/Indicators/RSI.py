import pandas_ta as ta

PQitemtype='CurveIndicator'

PERIOD=14
WIDTH=1
COLOR='#0055ff'
FREEZE=True
FREEZE_RANGE=[0,100]

def lvl(x):
    return {'show': True, 'value': x, 'width': 0.2, 'style': '....',
    'color': '#ffffff', 'desc_on': False, 'removable': False}

LEVELS=[lvl(x) for x in (30,70)]

# Places the indicator to a separate window, assigns properties and
# sets horizontal level lines
PQkwords=dict(windowed=True,width=WIDTH,color=COLOR,freeze=FREEZE,
    freeze_range=FREEZE_RANGE,levels=LEVELS)

#Calculate RSI using pandas_ta library
def PQcomputef(PQitem):
    rsi=ta.rsi(PQitem.timeseries.data['c'],length=PERIOD)
    rsi.dropna(inplace=True)
    
    return rsi.to_numpy()

#The label at the top-left corner of the indicator window
def PQstudylabel(PQitem):
    v=PQitem.yvalues
    if v is None:
        res=f'RSI({PERIOD})'
    else:
        res=f'RSI({PERIOD}) {v[-1]:.2f}'
    return res
