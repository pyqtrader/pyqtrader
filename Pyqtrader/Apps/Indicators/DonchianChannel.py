import numpy as np

import cfg
from drawings import AltPlotWidget
from api import PolylineCustomItem

from _debugger import _p

PERIOD=24
LENGTH=None

class DonchianChannel(PolylineCustomItem):
    def __init__(self, plt: AltPlotWidget, **kwargs):
        super().__init__(plt, color=(170,0,170),width=2)
                
        self.calc_donchian()

        self.plt.sigTimeseriesChanged.connect(self.ts_change)
        self.plt.lc_thread.sigLastCandleUpdated.connect(self.replot)

    def ts_change(self,ts):
        self.timeseries=ts
        self.calc_donchian()        
    
    def replot(self):
        if len(self.timeseries.closes)!=self._timeseries_length_stored:
            self.calc_donchian()
            self._timeseries_length_stored=len(self.timeseries.closes)

    def calc_donchian(self):
        self.clear_coord_buffers()
        highs=self.timeseries.data[cfg.HIGHS].iloc[-LENGTH-1 if LENGTH!=None else None:-1]
        lows=self.timeseries.data[cfg.LOWS].iloc[-LENGTH-1 if LENGTH!=None else None:-1]
        ticks=self.timeseries.ticks[-LENGTH-1 if LENGTH!=None else None:-1]
        last_tick=self.timeseries.ticks[-1]
        
        highs = highs.rolling(window=PERIOD).max()
            
        # Exclude nan
        high_line = [(t, h) for t, h in zip(ticks, highs) if not np.isnan(h)]
        # Extrapolate last element
        high_line.append((last_tick, high_line[-1][1]))
        self.add_coord_buffer(high_line)
        
        lows = lows.rolling(window=PERIOD).min()
        # Exclude nan
        low_line = [(t, l) for t, l in zip(ticks, lows) if not np.isnan(l)]
        # Extrapolate last element
        low_line.append((last_tick, low_line[-1][1]))
        self.add_coord_buffer(low_line)
    
    
PQitemtype=DonchianChannel
