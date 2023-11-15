from Pyqtrader.Apps.lib import ItemDF
import pandas_ta as ta

PQitemtype='CurveIndicator'

PERIOD=14
WIDTH=1
COLOR='#0055ff'
FREEZE=True
FREEZE_RANGE=[0,100]

LEVELS=[{'show': True, 'value': 70.0, 'width': 0.2, 'style': '....',
'color': '#ffffff', 'desc_on': False, 'removable': False}, 
{'show': True, 'value': 30.0, 'width': 0.2, 'style': '....',
'color': '#ffffff', 'desc_on': False, 'removable': False}]

# Places the indicator to a separate window, assigns properties and
# sets horizontal level lines
PQkwords=dict(windowed=True,width=WIDTH,color=COLOR,freeze=FREEZE,
    freeze_range=FREEZE_RANGE,levels=LEVELS)

#Set up clearing the dataframe upon a change of symbol or timeframe
def PQinitf(PQitem):
    PQitem.sigSeriesChanged.connect(PQupdatef)

#Calculate RSI using pandas_ta library
def PQcomputef(PQitem):
    if not hasattr(PQitem,"Item_df"):
        PQitem.Item_df=ItemDF(PQitem)
    PQitem.Item_df.refresh()
    rsi=ta.rsi(PQitem.Item_df.df['c'],length=PERIOD)
    rsi.dropna(inplace=True)
    
    return rsi.tolist()

#The label at the top-left corner of the indicator window
def PQstudylabel(PQitem):
    v=PQitem.yvalues
    if v is None:
        res=f'RSI({PERIOD})'
    else:
        res=f'RSI({PERIOD}) {v[-1]:.2f}'
    return res

# Replace the old timeseries with the new timeseries    
def PQupdatef(PQitem):
    PQitem.Item_df=ItemDF(PQitem)