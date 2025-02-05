import pandas as pd
import pandas_ta as ta

import cfg
import drawings

from Pyqtrader.Apps.customiz import MultiLineCustomItem, PenProps, points_to_segments

from _debugger import _p

LENGTH=5

class HullMA(MultiLineCustomItem):
    def __init__(self, plt : drawings.AltPlotWidget, **kwargs):
        """
        -----
        This class uses the pandas_ta library to calculate the Hull Moving Average
        (HMA) on the chartitem's timeseries.
        """
        super().__init__(plt, **kwargs)
    
        self.calc()

        self.plt.sigTimeseriesChanged.connect(self.ts_change)
        self.plt.lc_thread.sigLastCandleUpdated.connect(self.replot)

    def ts_change(self,ts):
        self.timeseries=ts
        self.calc()

    def replot(self):
        if len(self.timeseries.closes)!=self._timeseries_length_stored:
            self.calc()
            self._timeseries_length_stored=len(self.timeseries.closes)

    def calc(self,length=LENGTH):
        self.clear_coord_buffers()
        ts=self.timeseries
        prices=ts.data[cfg.CLOSES]
        hma = ta.hma(prices, length=length)

        hma = pd.DataFrame({'tick': ts.bars, 'hma': hma}).dropna()

        # Convert to segments, which is a format suitable to Qt's drawLines()     
        hma=points_to_segments(hma)

        hma_rising=hma[(hma['hma'] > hma['hma'].shift(1)) |(hma['hma'] < hma['hma'].shift(-1))]
        hma_declining=hma[(hma['hma'] < hma['hma'].shift(1)) |(hma['hma'] > hma['hma'].shift(-1))]

        self.add_coord_buffer(hma_rising,penprops=PenProps(color='g'))
        self.add_coord_buffer(hma_declining,penprops=PenProps(color='r'))

PQitemtype=HullMA