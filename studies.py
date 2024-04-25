import PySide6
from PySide6.QtWidgets import QMainWindow,QComboBox,QSpinBox,QDoubleSpinBox,QLabel,QMenu
from PySide6 import QtCore
from pyqtgraph import PlotCurveItem,BarGraphItem,TextItem,InfiniteLine
import numpy as np
import pandas_ta as ta

import cfg
import charttools as chtl, charttools
import timeseries as tmss, timeseries
import uitools

from _debugger import _print,_printcallers,_exinfo,_ptime,_c,_pc,_p

class MADialog(uitools.PropDialog):
    initials=dict(uitools.PropDialog.initials) #init constants used for reset_defaults()
    initials['method']=method=cfg.D_STUDYMETHOD
    def __init__(self, *args,**kwargs) -> None:
        props_on=dict(mode=True,shift=True)
        super().__init__(*args,ItemType=MAItem,props_on=props_on,**kwargs)
        self.setWindowTitle("Moving Average")
        self.state_dict['method']=self.__class__.method

        label=QLabel('Method: ')
        self.methodbox=QComboBox()
        self.methodbox.insertItems(1,cfg.D_STUDYMETHODLIST)
        self.methodbox.setCurrentText(self.__class__.method)
        self.layout.addWidget(label,self.order,0)
        self.layout.addWidget(self.methodbox,self.order,1)
        self.methodbox.currentTextChanged.connect(lambda *args: setattr(self.__class__,'method',self.methodbox.currentText()))
        self.order+=1

        self.embedded_db()  

        self.exec()
    
    def reset_defaults(self):
        super().reset_defaults()
        self.methodbox.setCurrentText(self.__class__.method)

class RSIDialog(uitools.PropDialogWithFreeze):
    levels=None
    initials=dict(uitools.PropDialogWithFreeze.initials)
    initials['period']=period=cfg.D_RSIPERIOD
    initials['color']=color=cfg.D_RSICOLOR
    def __init__(self, *args,**kwargs) -> None:
        props_on=dict(mode=True)
        super().__init__(*args,ItemType=RSIItem,props_on=props_on,**kwargs)

class RSITabsDialog(uitools.TabsDialog):
    def __init__(self,plt,item=None,**kwargs):
        self.__class__.level_props['color']=plt.graphicscolor
        level_props=dict(**self.__class__.level_props,desc_on=False)
        if item is None or item.levels is None:
            p_levels=[dict(value='70',removable=False,**level_props),
                dict(value='30',removable=False,**level_props)]
        else:
            p_levels=item.levels
        super().__init__(RSIDialog,plt,wname='Relative Strength Index',
            item=item,preset_levels=p_levels,level_props=level_props,**kwargs)

class StochDialog(uitools.PropDialogWithFreeze):
    levels=None
    initials=dict(uitools.PropDialogWithFreeze.initials)
    initials['period']=period=cfg.STOCH_K
    initials['color']=color=cfg.STOCHCOLOR_K
    initials['period_slow']=period_slow=cfg.STOCH_SLOW
    initials['period_d']=period_d=cfg.STOCH_D
    initials['width_d']=width_d=cfg.STOCHWIDTH_D
    initials['color_d']=color_d=cfg.STOCHCOLOR_D
    def __init__(self, *args,**kwargs) -> None:

        label0=QLabel('%K Slowing: ')
        self.pslowbox=QSpinBox()
        self.pslowbox.setMaximum(cfg.D_STUDYPERIODMAX)
        self.pslowbox.setMinimum(1)

        label1=QLabel('Period %D: ')
        self.pdbox=QSpinBox()
        self.pdbox.setMaximum(cfg.D_STUDYPERIODMAX)
        self.pdbox.setMinimum(1)

        label2 = QLabel('Width %D: ')
        self.wdbox=QDoubleSpinBox()
        self.wdbox.setSingleStep(0.1)
        self.wdbox.setMinimum(0.1)
        self.wdbox.setDecimals(1)

        label3=QLabel('Color %D: ')
        self.clrdbtn=uitools.ColorButton("")

        pps_on=dict(period=True, shift=False, width=True, mode=False, color=True)
        super().__init__(*args,ItemType=StochItem,props_on=pps_on,**kwargs)
        
        self.state_dict=dict(**self.state_dict,period_slow=self.__class__.period_slow,
            period_d=self.__class__.period_d,width_d=self.__class__.width_d,
            color_d=self.__class__.color_d)

        self.layout.addWidget(label0,self.order,0)
        self.layout.addWidget(self.pslowbox,self.order,1)
        self.pslowbox.textChanged.connect(lambda *args: setattr(self.__class__,'period_slow',self.pslowbox.value()))
        self.order+=1
        self.layout.addWidget(label1,self.order,0)
        self.layout.addWidget(self.pdbox,self.order,1)
        self.pdbox.textChanged.connect(lambda *args: setattr(self.__class__,'period_d',self.pdbox.value()))
        self.order+=1
        self.layout.addWidget(label2,self.order,0)
        self.layout.addWidget(self.wdbox,self.order,1)
        self.wdbox.textChanged.connect(lambda *args: setattr(self.__class__,'width_d',self.wdbox.value()))
        self.order+=1
        self.layout.addWidget(label3,self.order,0)
        self.layout.addWidget(self.clrdbtn,self.order,1)
        #correct color is assigned as clrdbtn itself is invoked prior to setattr, and internal clrdbtn color 
        #assignment is processed prior to setattr:
        self.clrdbtn.clicked.connect(lambda *args:setattr(self.__class__,'color_d',self.clrdbtn.btncolor))
        self.order+=1

        wid=self.layout.itemAt(0).widget()
        wid.setText('Period %K:')
        wid=self.layout.itemAt(2).widget()
        wid.setText('Width %K:')

        if self.item is not None:
            for att in ('width_d','color_d','period_d'):
                setattr(self.__class__,att,getattr(self.item,att))
            setattr(self.__class__,'period_slow',getattr(self.item,'funkvars')['period_slow'])
            self.set_values()        
    
    def set_values(self):
        self.pslowbox.setValue(self.__class__.period_slow)
        self.pdbox.setValue(self.__class__.period_d)
        self.wdbox.setValue(self.__class__.width_d)
        self.clrdbtn.setStyleSheet(f"background-color: {self.__class__.color_d}")
        super().set_values()

class StochTabsDialog(uitools.TabsDialog):
    def __init__(self,plt,item=None,**kwargs):
        self.__class__.level_props['color']=plt.graphicscolor
        level_props=dict(**self.__class__.level_props,desc_on=False)
        if item is None or item.levels is None:
            p_levels=[dict(value='80',removable=False,**level_props),
                dict(value='20',removable=False,**level_props)]
        else:
            p_levels=item.levels
        super().__init__(StochDialog,plt,wname='Stochastic Oscillator',
            item=item,preset_levels=p_levels,level_props=level_props,**kwargs)

class MACDDialog(uitools.PropDialog):
    initials=dict(uitools.PropDialog.initials)
    initials['period']=period=cfg.MACD_PERIODFAST
    initials['period_slow']=period_slow=cfg.MACD_PERIODSLOW
    initials['color']=color=cfg.STOCHCOLOR_K
    initials['period_signal']=period_signal=cfg.MACD_PERIODSIGNAL
    initials['width_signal']=width_signal=cfg.MACD_WIDTHSIGNAL
    initials['color_signal']=color_signal=cfg.MACD_COLORSIGNAL
    initials['width_hist']=width_hist=cfg.MACD_WIDTHHIST
    def __init__(self, *args,**kwargs) -> None:

        label0=QLabel('Slow EMA Period: ')
        self.pslowbox=QSpinBox()
        self.pslowbox.setMaximum(cfg.D_STUDYPERIODMAX)
        self.pslowbox.setMinimum(1)

        label1=QLabel('Signal Period: ')
        self.psigbox=QSpinBox()
        self.psigbox.setMaximum(cfg.D_STUDYPERIODMAX)
        self.psigbox.setMinimum(1)

        label2=QLabel('Signal Width: ')
        self.wsigbox=QDoubleSpinBox()
        self.wsigbox.setSingleStep(0.1)
        self.wsigbox.setMinimum(0.1)
        self.wsigbox.setDecimals(1)

        label3=QLabel('Signal Color: ')
        self.clrsigbtn=uitools.ColorButton("")

        label4=QLabel('Histogram Width: ')
        self.hwbox=QDoubleSpinBox()
        self.hwbox.setSingleStep(0.01)
        self.hwbox.setMinimum(0.01)
        self.hwbox.setMaximum(1.00)
        self.hwbox.setDecimals(2)

        super().__init__(*args,ItemType=MACDItem,**kwargs)
        self.setWindowTitle('MACD')
        
        self.state_dict=dict(**self.state_dict,period_slow=self.__class__.period_slow,
            period_signal=self.__class__.period_signal,width_signal=self.__class__.width_signal,
            color_signal=self.__class__.color_signal,width_hist=self.__class__.width_hist)

        self.layout.addWidget(label0,self.order,0)
        self.layout.addWidget(self.pslowbox,self.order,1)
        self.pslowbox.textChanged.connect(lambda *args: setattr(self.__class__,'period_slow',self.pslowbox.value()))
        self.order+=1
        self.layout.addWidget(label1,self.order,0)
        self.layout.addWidget(self.psigbox,self.order,1)
        self.psigbox.textChanged.connect(lambda *args: setattr(self.__class__,'period_signal',self.psigbox.value()))
        self.order+=1
        self.layout.addWidget(label2,self.order,0)
        self.layout.addWidget(self.wsigbox,self.order,1)
        self.wsigbox.textChanged.connect(lambda *args: setattr(self.__class__,'width_signal',self.wsigbox.value()))
        self.order+=1
        self.layout.addWidget(label3,self.order,0)
        self.layout.addWidget(self.clrsigbtn,self.order,1)
        #correct color is assigned as clrsigbtn itself is invoked prior to setattr, and internal clrsigbtn color 
        #assignment is processed prior to setattr:
        self.clrsigbtn.clicked.connect(lambda *args:setattr(self.__class__,'color_signal',self.clrsigbtn.btncolor))
        self.order+=1
        self.layout.addWidget(label4,self.order,0)
        self.layout.addWidget(self.hwbox,self.order,1)
        self.hwbox.textChanged.connect(lambda *args: setattr(self.__class__,'width_hist',self.hwbox.value()))
        self.order+=1

        wid=self.layout.itemAt(0).widget()
        wid.setText('Fast EMA Period:')

        if self.item is not None:
            for att in ('width_signal','color_signal','width_hist','period_signal'):
                setattr(self.__class__,att,getattr(self.item,att))
            setattr(self.__class__,'period_slow',getattr(self.item,'funkvars')['period_slow'])
            self.set_values()   

        self.embedded_db()

        self.exec()        
    
    def set_values(self):
        self.pslowbox.setValue(self.__class__.period_slow)
        self.psigbox.setValue(self.__class__.period_signal)
        self.wsigbox.setValue(self.__class__.width_signal)
        self.clrsigbtn.setStyleSheet(f"background-color: {self.__class__.color_signal}")
        self.hwbox.setValue(self.__class__.width_hist)
        super().set_values()

class BBDialog(uitools.PropDialog):
    initials=dict(uitools.PropDialog.initials) #init constants used for reset_defaults()
    initials['color']=color=cfg.BBCOLOR
    initials['method']=method=cfg.D_STUDYMETHOD
    initials['multi']=multi=cfg.BBMULTI
    def __init__(self, *args,**kwargs) -> None:
        props_on=dict(mode=True)
        super().__init__(*args,ItemType=BBItem,props_on=props_on,**kwargs)
        self.setWindowTitle("Bollinger Bands")
        self.state_dict['method']=self.__class__.method
        self.state_dict['multi']=self.__class__.multi

        label0=QLabel('Method: ')
        self.methodbox=QComboBox()
        self.methodbox.insertItems(1,cfg.D_STUDYMETHODLIST)
        self.methodbox.setCurrentText(self.__class__.method)
        self.layout.addWidget(label0,self.order,0)
        self.layout.addWidget(self.methodbox,self.order,1)
        self.methodbox.currentTextChanged.connect(lambda *args: setattr(self.__class__,'method',self.methodbox.currentText()))
        self.order+=1
        
        label1 = QLabel('Multiplier: ')
        self.multibox=QDoubleSpinBox()
        self.multibox.setSingleStep(0.01)
        self.multibox.setMinimum(0.01)
        self.multibox.setDecimals(2)
        self.multibox.setValue(self.__class__.multi)
        self.layout.addWidget(label1,self.order,0)
        self.layout.addWidget(self.multibox,self.order,1)
        self.multibox.textChanged.connect(lambda *args: setattr(self.__class__,'multi',self.multibox.value()))
        self.order+=1

        self.embedded_db()  

        self.exec()
    
    def reset_defaults(self):
        super().reset_defaults()
        self.methodbox.setCurrentText(self.__class__.method)
        self.multibox.setValue(self.__class__.multi)

class ATRDialog(uitools.PropDialog):
    initials=dict(uitools.PropDialog.initials) #init constants used for reset_defaults()
    initials['period']=period=cfg.ATRPERIOD
    def __init__(self, *args,**kwargs) -> None:
        super().__init__(*args,ItemType=ATRItem,**kwargs)
        self.setWindowTitle('Average True Range')
        self.embedded_db()
        self.exec()

class _ChartItem: #study abstract class
    def __init__(self, tseries, yvals, shift=0,caching=True,caller=None):
        self.values=self.matcher(tseries,yvals,shift=shift)
        self._length=len(tseries.data)
        self.caching=caching
        self.caller=caller

    @property
    def xvalues(self):
        return self.values[0]

    @property
    def yvalues(self):
        return self.values[1]

    def setData(self,*args,**kwargs):
        return super(_ChartItem,self).setData(*args,**kwargs)

    def set_data(self, tseries, yvals, shift=0):
        ticks=tseries.ticks
        if type(yvals)==list:
            yvals = np.array(yvals)
        
        def initial():
            self.values=self.matcher(tseries,yvals,shift=shift)
            self.setData(*self.values)
            self._length=len(ticks)
        
        if not self.caching:
            initial()
        else:
            if self._length is None or tseries is None or yvals is None:
                initial()
            else:
                delta=len(ticks)-self._length
                ly=len(yvals)
                if delta<0:
                    initial()
                elif delta==0:
                    self.values[1][-ly:]=yvals
                    try: 
                        self.setData(*self.values)
                    except Exception: #to process X,Y mismatch and other exceptions
                        initial()
                elif delta==1:
                    self.values[0]=np.append(self.values[0],ticks[-1])
                    self.values[1]=np.append(self.values[1],0) # add empty value
                    self.values[1][-ly:]=yvals
                    try:
                        self.setData(*self.values)
                    except Exception: #to process X,Y mismatch and other exceptions
                        initial()
                    self._length=len(ticks)#update length, in other cases it is updated within initials()
                else: #delta>1 - re-initialise fully if more than 1 new candles have formed
                    initial()
        return self.values
    
    def matcher(self,tseries,yvals, shift: int=0):
        if tseries is None or yvals is None:
            res=[None,None]
        
        else:
            tslen=len(tseries.ticks)
            vlen=len(yvals)
            diff=tslen-vlen
            ticks=tseries.ticks[diff:]
            tf=tseries.timeframe
            if shift>0:
                # Shift to the right
                ticks=ticks[shift:]
                ticks = np.append(ticks[:-1], np.arange(ticks[-1], ticks[-1] + (shift+1)*tf, tf))
            elif shift<0:
                # Shift to the left
                ticks=ticks[:shift]
                ticks=np.append(np.arange(ticks[0]+shift*tf, ticks[0],tf),ticks)

            res=[ticks,yvals]
        
        return res

    def update_subitem(self,values,tseries=None): #api update function
        ts=self.parent().timeseries if tseries is None else tseries
        return self.set_data(ts,values)

class _CurveItem(_ChartItem,PlotCurveItem):
    def __init__(self, tseries, yvals, shift=0, caching=True,caller=None,**kwargs):
        super().__init__(tseries, yvals, shift=shift, caching=caching,caller=caller)
        super(_ChartItem,self).__init__(*self.values,**kwargs)

    def mouseClickEvent(self, ev):
        if self.mouseShape().contains(ev.pos()):
            if ev.button()==QtCore.Qt.MouseButton.LeftButton and hasattr(self,'left_clicked'):
                self.left_clicked(ev)
            elif ev.button()==QtCore.Qt.MouseButton.RightButton and hasattr(self,'right_clicked'):
                self.right_clicked(ev)
        return super().mouseClickEvent(ev)

class _BarItem(_ChartItem,BarGraphItem):
    def __init__(self, tseries, yvals, shift=0, caching=True,caller=None,**opts):
        super().__init__(tseries, yvals, shift=shift, caching=caching,caller=caller)
        super(_ChartItem,self).__init__(x=self.values[0],height=self.values[1],**opts)
    
    def setData(self,x,height):
        self.opts['x']=x
        self.opts['height']=height
        self.setOpts()

def study_item_factory(base):
    class _StudyItem(base): #abstract class
        sigReplotted=QtCore.Signal()
        sigRightClicked=QtCore.Signal(object)
        def __init__(self,plt,windowed=False,funkvars=None,ts=None,shift=0,color=cfg.D_STUDYCOLOR, width=cfg.D_STUDYWIDTH,
                ttname=None,dialog=None, precision=None,dockplt=None,levels=None,freeze=None,
                freeze_range=(0,100),hover_on=True,caching=True,cache0: dict=None,**kwargs):
            self.is_persistent=True
            self.is_study=True
            self.windowed=windowed
            self.shift=shift
            self.color=color
            self.width=width   
            self.plt=plt
            self.timeseries=self.plt.chartitem.timeseries if ts is None else ts
            self.dockplt=dockplt if dockplt is not None else self.plt
            self.ttname=ttname
            self.dialog=dialog
            self.context_menu=self.create_menu()
            if precision is None:
                self.precision=self.dockplt.precision
            else:
                self.dockplt.precision=self.precision=precision
            self.funkvars=funkvars #function's keyword variables
            self.caching=caching
            self._length=None
            self.cache0=cache0 #dict for cache starting values
            yvals=self.computef()

            super().__init__(self.timeseries,yvals,shift=self.shift,**kwargs)
            self.setPen(dict(color=color,width=width))
            self.setZValue(1)
            self.hover_on=hover_on
            
        
            if hasattr(self,'caller') and self.caller!='open_subw': #fast way to setup
                if self.windowed==False:
                    self.plt.addItem(self)
                else:
                    subw=self.plt.subwindow
                    subw.add_plot()
                    rct=plt.viewRect()
                    self.dockplt=subw.docks[-1].widgets[0]
                    self.dockplt.addItem(self) #need to pass the placing plot in order to generate correct tooltip
                    plt.setRange(rect=rct,padding=0) 
            
            self.levels=levels
            self.level_items=[]
            if levels is not None:
                self.set_levels()
            
            self.freeze=freeze
            self.freeze_range=freeze_range
            if freeze is not None:
                self.set_freeze()

            self.labeltext=None
            if self.windowed==True:
                self.labeltext=TextItem(anchor=(0,0))
                self.dockplt.addItem(self.labeltext,ignoreBounds=True)
                self.set_label()
                self.dockplt.sigRangeChanged.connect(self.set_label)
                self.sigReplotted.connect(self.set_label)
                
            self.plt.sigChartPropsChanged.connect(self.update_label)
            self.plt.sigTimeseriesChanged.connect(self.ts_change)
            self.sigRightClicked.connect(self.right_clicked)
            self.plt.lc_thread.sigLastCandleUpdated.connect(self.replot)
            self.plt.lc_thread.sigInterimCandlesUpdated.connect(self.replot)

        def mouseClickEvent(self, ev):
            self.mc_event=ev
            if ev.button()==QtCore.Qt.MouseButton.RightButton and self.mouseShape().contains(ev.pos()):
                self.sigRightClicked.emit(ev)
            return super().mouseClickEvent(ev)
        
        def computef(self): #core function calculating the study's y-axis values,always overridden in specific classes
            return None

        @property
        def cache_event(self): #establishes whether caching operation is valid
            if self.caching and self._length is not None:
                delta=len(self.timeseries.times)-self._length
                if delta==0 or delta==1: #triggers only if no new candles formed or only 1 new candle formed, otherwise full re-calculation
                    res=True
                else:
                    res=False
            else:
                res=False
            return res

        @property
        def ts_diff(self): #difference of the length of timeseries compared to the previous server request
            diff=len(self.timeseries.data)-(self._length if self._length is not None else 0)
            return diff

        def replot(self) -> None:
            ts=self.plt.chartitem.timeseries
            if self.timeseries is not ts:
                self.timeseries=ts
            yvals=self.computef()
            if yvals is not None:
                self.set_data(self.timeseries,yvals,shift=self.shift)
                self.sigReplotted.emit()

        def flush_cache(self):
            self._length=None
            for ch in self.children():
                if hasattr(ch,'_length'):
                    ch._length=None
            if self.cache0 is not None:
                for key in self.cache0: #flush starting values
                    self.cache0[key]=None
        
        def ts_change(self,ts):
            self.flush_cache()
            self.timeseries=ts
            self.replot()
            self.plt.lc_thread.sigLastCandleUpdated.connect(self.replot)
            self.plt.lc_thread.sigInterimCandlesUpdated.connect(self.replot)

        def save_props(self):
            pen=self.opts['pen']
            self.width=pen.width()
            self.color=pen.color().name()
            a={'width' : self.width, 'color' : self.color, 'shift' : self.shift,
                'funkvars' : self.funkvars}
            if self.freeze is not None:
                a['freeze']=self.freeze
            if self.levels is not None:
                a['levels']=self.levels
            return a
        
        def set_props(self,state=None):
            self.flush_cache()
            if state is not None:
                try:
                    self.shift=state['shift']
                except Exception:
                    pass
                self.width=state['width']
                self.color=state['color']
                self.setPen(dict(color=self.color,width=self.width))
                if self.funkvars is not None:
                    for key in self.funkvars:
                        try:
                            self.funkvars[key]=state['funkvars'][key]
                        except Exception:
                            self.funkvars[key]=state[key]
                try:
                    self.levels=state['levels']
                except Exception:
                    pass
            try:
                self.freeze=state['freeze']
                self.set_freeze()
            except Exception:
                pass
            self.set_levels()
            self.replot()

        def xttip(self):
            tf=self.timeseries.timeframe
            x=self.dockplt.mapped_xy[0]
            dtxs,ind=chtl.screen_to_plot(self.timeseries,x)
            if tf<cfg.PERIOD_D1:
                xtext=dtxs.strftime("%Y-%b-%d %H:%M")
            else:
                xtext=dtxs.strftime("%Y-%b-%d")
            diff=len(self.timeseries.times)-len(self.values[0])
            index=ind-diff
            pre=chtl.precision(self.plt.symbol) if self.precision is None else self.precision
            return index,xtext,pre

        def ttip(self):
            index,xtext,pre=self.xttip()
            ytext=self.values[1][index]
            return '{}({},{})\n{}\n{:.{pr}f}'.format(self.ttname,self.funkvars['period'],
                self.funkvars['mode'],xtext,ytext,pr=pre)
        
        @chtl.string_to_html(text_color='black')
        def html_ttip(self):
            return self.ttip()

        def hoverEvent(self, ev):
            if self.hover_on==True:
                try:
                    if self.mouseShape().contains(ev.pos()):
                        self.setToolTip(self.html_ttip())  
                    else:
                        self.setToolTip('')
                except Exception:
                    pass

        def create_menu(self,description=None):
            menu=QMenu()
            if description is not None:
                menu.addSection(description)
            if self.dialog is not None:
                self.prop_act=menu.addAction('Properties')
            else:
                self.prop_act=None
            menu.addSeparator()
            self.rem_act=menu.addAction('Remove')
            return menu

        def right_clicked(self,ev):
            ev_pos=ev.screenPos()
            self.context_menu=self.create_menu(description=(s:=self.ttip())[:s.find('\n')])
            action=self.context_menu.exec(QtCore.QPoint(ev_pos.x(),ev_pos.y()))           
            if action==self.rem_act:
                self.remove_act()
            elif self.prop_act is not None and action==self.prop_act:
                self.dialog(self.plt,item=self)

        def remove_act(self):
            self.removal()
            empty=True
            for itm in self.dockplt.listItems():
                if chtl.item_is_study(itm) or chtl.item_is_cbl(itm):
                    empty=False
                    break
            if empty==True:
                self.plt.subwindow.remove_plot(self.dockplt)
        
        def set_levels(self):
            if self.level_items is not []:
                for itm in self.level_items:
                    self.dockplt.removeItem(itm)
                self.level_items=[]

            if self.levels is not None:
                for lvl in self.levels:
                    if lvl['show']==True:
                        line=InfiniteLine(pos=lvl['value'],angle=0)
                        line.setPen(width=lvl['width'],color=lvl['color'],
                            style=cfg.LINESTYLES[lvl['style']])
                        self.level_items.append(line)
                        self.dockplt.addItem(line)
        
        def set_label(self):
            ax=self.dockplt.getAxis('bottom')
            ay=self.dockplt.getAxis('right')
            x0=ax.range[0]
            y1=ay.range[1]
            txt=self.label_t()
            # self.labeltext.setText(txt)
            self.labeltext.setHtml('<div style="font-size: {}pt;">{}</div>'.format(8,txt))
            self.labeltext.setColor(self.plt.chartprops[cfg.foreground])
            self.labeltext.setPos(x0,y1)
            self.labeltext.setAnchor((0,0.25))
            
        def label_t(self):
            try:
                pre=4 if self.precision is None else self.precision
                lbl=self.ttname+f' ({self.funkvars["period"]}) '+"{:.{pr}f}".format(self.values[1][-1],pr=pre)
            except Exception:
                lbl=''
            return lbl

        def update_label(self,props):
            self.labeltext.setColor(props[cfg.foreground])

        def set_freeze(self):
            self.dockplt.vb.setYRange(*self.freeze_range,update=True)
            self.dockplt.pitm.setMouseEnabled(x=True,y=not self.freeze)
        
        def removal(self):
            self.plt.sigChartPropsChanged.disconnect(self.update_label)
            self.plt.lc_thread.sigLastCandleUpdated.disconnect(self.replot)
            self.plt.lc_thread.sigInterimCandlesUpdated.disconnect(self.replot)
            self.plt.sigTimeseriesChanged.disconnect(self.ts_change)
            self.sigRightClicked.disconnect(self.right_clicked)
            self.dockplt.removeItem(self)
    
    return _StudyItem

StudyCurveItem=study_item_factory(_CurveItem)

class MAItem(StudyCurveItem):
    def __init__(self, plt,period=cfg.D_STUDYPERIOD,mode=cfg.D_STUDYMODE,method=cfg.D_STUDYMETHOD,shift=0,**kwargs):
        fvrs=dict(period=period,mode=mode,method=method) #needed to streamline JSON storing
        super().__init__(plt,funkvars=fvrs,shift=shift,ttname=method[0].upper()+'MA',dialog=MADialog,**kwargs)
        self.v0=None
    
    def computef(self,ts=None):
        df=self.timeseries.data if ts is None else ts.data
        fv=self.funkvars
        period=fv['period']
        method=fv['method']
        mode=fv['mode']
       
        if method=='Simple':
            self.ttname='SMA'
            ins=df[mode[0].lower()][-2-period if self.cache_event else None:]
            yvals=ta.sma(ins,length=period).dropna().to_numpy()
        elif method=='Exponential':
            self.ttname='EMA'
            ins=df[mode[0].lower()]
            
            # Cache processing
            if self.cache_event and self.v0 is not None:
                ins=ins[-2-self.ts_diff-period:] # caching array

                # Tricking ta.ema() into accepting the cached ema value (self.v0) as the
                # starting value for the recalculated bars processing
                ins=ins.copy() # ensures that the source data is not modified to avoid graphical artifacts
                ins.iloc[:period]=self.v0

                yvals=ta.ema(ins,length=period,sma=True).dropna().to_numpy()

            # Non-cache processing
            else:
                yvals=ta.ema(ins,length=period).dropna().to_numpy()

            self.v0=yvals[-3] # cached ema value
        
        return yvals

class RSIItem(StudyCurveItem):
    def __init__(self, plt,period=cfg.D_RSIPERIOD,mode=cfg.D_STUDYMODE,**kwargs):
        fvrs=dict(period=period,mode=mode)
        self.cache=None
        super().__init__(plt,windowed=True,funkvars=fvrs,precision=4,
            ttname='RSI',dialog=RSITabsDialog,**kwargs)

    def computef(self,ts=None):
        tseries=self.timeseries if ts is None else ts
        mode=self.funkvars['mode']
        period=self.funkvars['period']
        values=tseries.data[mode[0].lower()]
        yres = []
        up,down=0,0
        cutoff=period+1
        if self.cache is None or self._length is None:
            for i in range(period): #calculate the first element
                diff=values[i+1]-values[i]
                if diff<0:
                    down+=-diff
                else:
                    up+=diff
            up/=period
            down/=period
            if down!=0:
                rs0=100*(1-(1/(1+up/down)))
            elif up!=0:
                rs0=100
            else:
                rs0=50
            yres.append(rs0)
        else: #use cached data to save on re-calculations
            up=self.cache['up']
            down=self.cache['down']
            for i,time in enumerate(reversed(tseries.times)):
                if time==self.cache['times']:
                    cutoff=-i-1 #start point from the end of the timeseries
                    break
        
        values=values[cutoff:]

        for i,value in enumerate(values[:-1]):#main loop
            if i==len(values)-3:#caching: take the third latest candle
                self.cache=dict(up=up,down=down,times=tseries.times[-3])
            diff=values.iloc[i+1]-value
            up=(up*(period-1)+(diff if diff>0 else 0))/period
            down=(down*(period-1)+(-diff if diff<0 else 0))/period
            if down!=0:
                rs=100*(1-(1/(1+up/down)))
            elif up!=0:
                rs=100
            else:
                rs=50
            yres.append(rs)
        return yres

class StochItem(StudyCurveItem):
    def __init__(self, plt,period=cfg.STOCH_K,period_slow=cfg.STOCH_SLOW,period_d=cfg.STOCH_D,
        width_d=cfg.STOCHWIDTH_D,color_d=cfg.STOCHCOLOR_D,**kwargs):
        fvrs=dict(period=period,period_slow=period_slow, period_d=period_d)
        self.period_d=period_d
        self.width_d=width_d
        self.color_d=color_d

        super().__init__(plt,windowed=True,funkvars=fvrs,precision=4,
            ttname='Stoch', dialog=StochTabsDialog,**kwargs)
        self.dslow=_CurveItem(self.timeseries,[])
        self.dslow.setParent(self)
        self.dockplt.addItem(self.dslow)
        self.dslow.setPen(dict(width=self.width_d,color=self.color_d))
        self.set_label()
    
    def computef(self,ts=None):
        df=self.timeseries.data if ts is None else ts.data
        period=(fv:=self.funkvars)['period']
        period_slow=fv['period_slow']
        period_d=fv['period_d']
        
        ins=df[-2-sum(fv.values()) if self.cache_event else None:]

        stoch=ta.stoch(ins.h,ins.l,ins.c,k=period,d=period_d,smooth_k=period_slow,mamode='sma')

        yvals_d=stoch.iloc[:,1].dropna().to_numpy()
        if hasattr(self, 'dslow'):
            self.dslow.set_data(self.timeseries,yvals_d) 

        return stoch.iloc[:,0].dropna().to_numpy()
    
    def save_props(self):
        a=super().save_props()
        a['period_d']=self.period_d
        a['width_d']=self.width_d
        a['color_d']=self.color_d
        return a

    def set_props(self,state=None,**kwargs):
        if state is not None:
            self.period_d=state['period_d']
            self.width_d=state['width_d']
            self.color_d=state['color_d']
            self.dslow.setPen(dict(width=self.width_d,color=self.color_d))
        super().set_props(state,**kwargs)
        
    def ttip(self):
        index,xtext,pre=self.xttip()
        ytext=self.yvalues[index]
        index1=index-(len(self.xvalues)-len(self.dslow.xvalues))
        v_d=self.dslow.yvalues[index1]
        return '{}({},{},{})\n{}\n%K:{:.{pr}f}\n%D:{:.{pr}f}'.format(self.ttname,self.funkvars['period'],
            self.funkvars['period_slow'],self.period_d,xtext,ytext,v_d,pr=self.precision)

    def label_t(self):
        try:
            a,b,c=self.funkvars["period"],self.funkvars["period_slow"],self.period_d
            lbl=self.ttname+f' ({a},{b},{c}) '+"{:.{pr}f} {:.{pr}f}".format(self.values[1][-1],
                self.dslow.values[1][-1],pr=self.precision)
            return lbl
        except Exception:
            super().label_t()

class MACDItem(StudyCurveItem):
    def __init__(self,plt,period=cfg.MACD_PERIODFAST,period_slow=cfg.MACD_PERIODSLOW,
        period_signal=cfg.MACD_PERIODSIGNAL,width_signal=cfg.MACD_WIDTHSIGNAL,
        color_signal=cfg.MACD_COLORSIGNAL,width_hist=cfg.MACD_WIDTHHIST,**kwargs):
        fvrs=dict(period=period,period_slow=period_slow)
        self.period_signal=period_signal
        self.width_signal=width_signal
        self.color_signal=color_signal
        self.width_hist=width_hist
        self.signalline=None #to fix errors before signalline initialisation and avoid using 'try'/'except'
        c0=dict(v01=None,v02=None,sgn_v0=None, hist_c=None)
        super().__init__(plt,windowed=True,funkvars=fvrs,precision=5,ttname='MACD',dialog=MACDDialog,
            cache0=c0,**kwargs)
        yvals_signal=calc_ma(self.values[1],period=period_signal,method='Exponential')
        self.sgn_v0=yvals_signal[-3] #initial value for caching purposes
        self.signalline=_CurveItem(self.timeseries,yvals_signal)
        self.signalline.setParent(self)
        self.signalline.setZValue(0)
        self.dockplt.addItem(self.signalline)
        dkvb=self.dockplt.getViewBox()
        rct=dkvb.viewRect()
        hist=self.calc_hist()
        self.histitem=_BarItem(self.timeseries, hist, 
            width=width_hist*self.timeseries.tf)
        self.histitem.setZValue(-1)
        self.dockplt.addItem(self.histitem)
        dkvb.setRange(rect=rct,padding=0) 

        self.plt.sigTimeseriesChanged.connect(self.update_hist_width)

    @property
    def v01(self):
        return self.cache0['v01']
    
    @v01.setter
    def v01(self,x):
        self.cache0['v01']=x
    
    @property
    def v02(self):
        return self.cache0['v02']
    
    @v02.setter
    def v02(self,x):
        self.cache0['v02']=x

    @property
    def sgn_v0(self):
        return self.cache0['sgn_v0']
    
    @sgn_v0.setter
    def sgn_v0(self,x):
        self.cache0['sgn_v0']=x
    
    @property
    def hist_c(self):
        a=self.cache0['hist_c']
        if a is None:
            return False
        else:
            return a
    
    @hist_c.setter
    def hist_c(self,x):
        self.cache0['hist_c']=x

    def computef(self,ts=None):
        def cached_ma(ins,period,v0=None):
            st=-3-self.ts_diff if self.cache_event else None
            ins=list(ins[st:])
            yvals=calc_ma(ins,period=period,method='Exponential',v0=v0)
            return yvals

        tseries=self.timeseries if ts is None else ts
        period_slow=self.funkvars['period_slow']
        period_fast=self.funkvars['period']
        ins=tseries.closes
        y=[]
        if self.cache_event:
            d1=0
            d2=0
        else:
            delta=period_slow-period_fast
            d1=delta if delta>0 else 0
            d2=delta if delta<0 else 0
            self.v01=None
            self.v02=None
        ema1=cached_ma(ins,period_fast,v0=self.v01)
        self.v01=ema1[-3]
        ema2=cached_ma(ins,period_slow,v0=self.v02)
        self.v02=ema2[-3]
        if self.cache_event:
            rn=range(-3-self.ts_diff,0)
        else:
            rn=range(min(len(ema1),len(ema2)))
        for i in rn:
            y.append(ema1[i+d1]-ema2[i+d2])
        return y

    def save_props(self):
        a=super().save_props()
        a['period_signal']=self.period_signal
        a['width_signal']=self.width_signal
        a['color_signal']=self.color_signal
        a['width_hist']=self.width_hist
        return a

    def set_props(self,state=None,**kwargs):
        if state is not None:
            self.period_signal=state['period_signal']
            self.width_signal=state['width_signal']
            self.color_signal=state['color_signal']
            self.signalline.setPen(dict(width=self.width_signal,color=self.color_signal))
            self.width_hist=state['width_hist']
            self.histitem.opts['width']=self.width_hist*self.timeseries.tf
            self.histitem.setOpts()
        super().set_props(state,**kwargs)
    
    def update_hist_width(self,ts):
        self.histitem.opts['width']=self.width_hist*ts.tf
        self.histitem.setOpts()

    def replot(self):
        super().replot()
        st=None
        if self.cache_event and self.sgn_v0 is not None:
            st=-3-self.ts_diff
        if self.signalline is not None:
            ins=self.values[1][st:]
            yvals_signal=calc_ma(ins,period=self.period_signal,method='Exponential',v0=self.sgn_v0)
            self.sgn_v0=yvals_signal[-3] if yvals_signal!=[] else None
            self.signalline.set_data(self.timeseries,yvals_signal)        
            hist=self.calc_hist()
            self.histitem.set_data(self.timeseries, hist)

    def ttip(self):
        index,xtext,pre=self.xttip()
        ytext=self.values[1][index]
        index1=index-(len(self.values[0])-len(self.signalline.values[0]))
        v_sig=self.signalline.values[1][index1]
        lbl= '{}({},{},{})\n{}\nMACD:{:.{pr}f}\nSignal:{:.{pr}f}'.format(self.ttname,self.funkvars['period'],
            self.funkvars['period_slow'],self.period_signal,xtext,ytext,v_sig,pr=self.precision)
        return lbl

    def label_t(self):
        try:
            a,b,c=self.funkvars["period"],self.funkvars["period_slow"],self.period_signal
            return self.ttname+f' ({a},{b},{c}) '+"{:.{pr}f} {:.{pr}f}".format(self.values[1][-1],
                self.signalline.values[1][-1],pr=self.precision)
        except Exception:
            super().label_t()
    
    def calc_hist(self):
        st=len(self.values[1])-len(self.signalline.values[0])
        v=self.values[1][st:]
        if self.cache_event and hasattr(self,'histitem') and self.hist_c:
            ts_diff=len(v)-len(self.histitem.opts['height'])
            st=-3-ts_diff
            v=v[st:]
        else:
            self.hist_c=True
        s=self.signalline.values[1][-len(v):]
        hist=[a_i - b_i for a_i, b_i in zip(v, s)]
        hist=hist
        return hist

class BBItem(StudyCurveItem):
    def __init__(self,plt,period=cfg.D_STUDYPERIOD,mode=cfg.D_STUDYMODE,method=cfg.D_STUDYMETHOD,
        multi=cfg.BBMULTI,**kwargs):
        fvrs=dict(period=period,mode=mode,method=method,multi=multi)
        self.v0=None
        
        super().__init__(plt,funkvars=fvrs,ttname='BB',dialog=BBDialog,**kwargs)
        self.upitem=_CurveItem(self.timeseries,[])
        self.upitem.setParent(self)
        self.downitem=_CurveItem(self.timeseries,[])
        self.downitem.setParent(self)
        self.plt.addItem(self.upitem)
        self.upitem.setPen(dict(width=self.width,color=self.color))
        self.plt.addItem(self.downitem)
        self.downitem.setPen(dict(width=self.width,color=self.color))

    def computef(self,ts=None):
        df=self.timeseries.data if ts is None else ts.data
        fv=self.funkvars
        period=fv['period']
        method=fv['method']
        mode=fv['mode']
        multi=fv['multi']

        ins=df[mode[0].lower()][-2-period if self.cache_event else None:]
        bands=ta.bbands(ins,length=period,std=multi)
        ma=bands.iloc[:,1]
        
        if method=='Exponential':
            sma=ma
            ins=df[mode[0].lower()]
            
            # Cache processing
            if self.cache_event and self.v0 is not None:
                ins=ins[-2-self.ts_diff-period:] # caching array

                # Tricking ta.ema() into accepting the cached ema value (self.v0) as the
                # starting value for the recalculated bars
                ins=ins.copy() # ensures that the source data is not modified to avoid graphical artifacts
                ins.iloc[:period]=self.v0

                ma=ta.ema(ins,length=period,sma=True)

            # Non-cache processing
            else:
                ma=ta.ema(ins,length=period)

            diff=ma-sma

            # Adjusting bands
            bands.iloc[:,0]+=diff
            bands.iloc[:,2]+=diff

            self.v0=ma.iloc[-3] # cached ema value
        
        downs=bands.iloc[:,0].dropna().to_numpy() # low values
        ups=bands.iloc[:,2].dropna().to_numpy() # up values
        if hasattr(self,"upitem") and hasattr(self,"downitem"):
            self.upitem.set_data(self.timeseries,ups)
            self.downitem.set_data(self.timeseries,downs)

        return ma.dropna().to_numpy() # moving average values

    def save_props(self):
        a=super().save_props()
        a['multi']=self.multi
        return a
    
    def set_props(self,state=None,**kwargs):
        if state is not None:
            self.multi=state['multi']
        super().set_props(state,**kwargs)
        self.upitem.setPen(dict(color=self.color,width=self.width))
        self.downitem.setPen(dict(color=self.color,width=self.width))

    def ttip(self):
        index,xtext,pre=self.xttip()
        ytext=self.yvalues[index]
        yname=self.funkvars['method'][0]+'MA:'
        upb,downb=self.upitem.yvalues[index],self.downitem.yvalues[index]
        pre=chtl.precision(self.plt.symbol) if self.precision is None else self.precision 
        lbl='{}({},{})\n{}\n{}{:.{pr}f}\nUpB:{:.{pr}f}\nDownB:{:.{pr}f}'.format(self.ttname,self.funkvars['period'],
            self.funkvars['mode'],xtext,yname,ytext,upb,downb,pr=pre)
        return lbl

    def removal(self):
        self.dockplt.removeItem(self.upitem)
        self.dockplt.removeItem(self.downitem)
        return super().removal()

class ATRItem(StudyCurveItem):
    def __init__(self,plt,period=cfg.ATRPERIOD,**kwargs):
        fvrs=dict(period=period)
        super().__init__(plt,windowed=True,funkvars=fvrs,ttname='ATR',precision=5,
            dialog=ATRDialog,**kwargs)
    
    def ttip(self):
        index,xtext,pre=self.xttip()
        ytext=self.values[1][index]
        return '{}({})\n{}\n{:.{pr}f}'.format(self.ttname,self.funkvars['period'],
            xtext,ytext,pr=pre)
    
    def computef(self,ts=None):
        df=self.timeseries.data if ts is None else ts.data
        period=self.funkvars['period']
        df=df[-2-period if self.cache_event else None:]
        return ta.atr(df.h,df.l,df.c,length=period).dropna().to_numpy()

def calc_ma(ins,period=cfg.D_MAPERIOD,method=cfg.D_STUDYMETHOD,v0=None,**kwargs):
    yres = []
    def sma(i):
        return sum(ins[i-period+1:i+1])/period
    if method=='Simple':
        for ind,val in enumerate(ins):
            if ind>=period-1:
                s=sma(ind)
                yres.append(s)
    elif method=='Exponential':
        k=2/(period+1)
        for ind,val in enumerate(ins):
            if v0 is None:
                if ind>=period-1:
                    if ind==period-1:
                        e=sma(ind)
                    else:
                        e=val*k+e*(1-k)
                    yres.append(e)
            else: 
                if ind==0: #caching
                    e=v0
                else:
                    e=val*k+e*(1-k)
                yres.append(e)
    return yres




