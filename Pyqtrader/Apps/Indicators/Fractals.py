from pyqtgraph import TextItem, Point

import drawings as drws
from Pyqtrader.Apps.customiz import CustomPolyitem

from _debugger import _p

DEGREE = 2
SOFT = True
BARSBACK=50
TOP='\u2B99'
BOTTOM='\u2B9B'
TOPANCHOR=0.8
BOTTOMANCHOR=0.1


class Fractals(CustomPolyitem):
    def __init__(self, plt: drws.AltPlotWidget,**kwargs):
        super().__init__(plt,color='c')

        self.fractals_calc()

        self.plt.sigTimeseriesChanged.connect(self.ts_change)
        self.plt.lc_thread.sigLastCandleUpdated.connect(self.replot)

    def ts_change(self,ts):
        self.timeseries=ts
        self.fractals_calc()        
    
    def replot(self):
        if len(self.timeseries.closes)!=self._timeseries_length_stored:
            self.fractals_calc()
            self._timeseries_length_stored=len(self.timeseries.closes)
    
    def logic(self, degree=DEGREE, barsback=BARSBACK, soft=SOFT) -> list[list[bool, int, float]]:
        s = self.timeseries
        fractals = []
        sh = s.highs[-barsback if barsback is not None else None:]
        sl = s.lows[-barsback if barsback is not None else None:]
        bars = s.bars[-barsback if barsback is not None else None:]

        for i in range(degree, len(sh) - degree):
            # Soft or strict comparison operators
            if soft:
                high_condition = all(sh[i] >= sh[i + offset] for offset in range(-degree, degree + 1) if offset != 0)
                low_condition = all(sl[i] <= sl[i + offset] for offset in range(-degree, degree + 1) if offset != 0)
            else:
                high_condition = all(sh[i] > sh[i + offset] for offset in range(-degree, degree + 1) if offset != 0)
                low_condition = all(sl[i] < sl[i + offset] for offset in range(-degree, degree + 1) if offset != 0)

            if high_condition:
                fractals.append([True, bars[i], sh[i]])
            if low_condition:
                fractals.append([False, bars[i], sl[i]])

        return fractals


    @staticmethod
    def mark(itm : TextItem, pos):
        if pos[0]: yanch=TOPANCHOR; txt=TOP; vals=[*pos[1:]]
        else: yanch=BOTTOMANCHOR; txt=BOTTOM; vals=[*pos[1:]]
        itm.setPos(Point(vals))
        itm.setPlainText(txt)
        itm.setAnchor(Point(0.5,yanch))
        
    def fractals_calc(self):
        fractals=self.logic()
        for si in self.subitems.copy():
            self.remove_subitem(si)
        for f in fractals:
            si=self.create_subitem(TextItem)
            self.mark(si,f)

PQitemtype=Fractals
