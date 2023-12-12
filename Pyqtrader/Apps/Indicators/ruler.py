import cfg
from charttools import pipper
import pyqtgraph as pg
from Pyqtrader.Apps.lib import ItemDF

PQitemtype="TrendLineIndicator"

PQshortcut="Ctrl+D"

def PQinitf(PQitem):
    closes=PQitem.series.closes
    times=PQitem.series.times
    PQitem.set_data([[times[-12],closes[-12]],[times[-2],closes[-2]]])
    PQitem.set_selectable(True)
    PQitem.set_properties(color='r',extension=cfg.RAYDIR['n'])
    for h in PQitem.getHandles():
        h.pen=pg.mkPen('r')
        h.currentPen=pg.mkPen('r')
        h.hoverPen=pg.mkPen('y')
    PQitem.create_subitem("Text")
    ruler_tag(PQitem)

    PQitem.sigRegionChangeFinished.connect(lambda: ruler_tag(PQitem))

def ruler_tag(PQitem):
    df=ItemDF(PQitem).df
    df.set_index('t', inplace=True)
    si=PQitem.subitems[0]
    pos=PQitem.get_data()
    si.set_data(pos[1])
    t0=df['i'].loc[pos[0][0]]
    t1=df['i'].loc[pos[1][0]]
    bars=int((t1-t0)//PQitem.series.timeframe)
    pips=(pos[1][1]-pos[0][1])*pipper(PQitem.series.symbol)
    si.set_text(f"Pips: {pips:.1f}\nBars: {str(bars)}")
    si.setColor('r')
    si.set_anchor(0.5,1)
