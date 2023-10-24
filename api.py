import PySide6
from PySide6.QtWidgets import QMenu, QMdiArea
from PySide6 import QtCore
from PySide6.QtCore import QPoint
from importlib.machinery import SourceFileLoader
from pyqtgraph import Point,TextItem

import charttools as chtl, charttools
import cfg,timeseries,studies,labelings, drawings 
from _debugger import _print,_p,_printcallers,_c,_pc
from uitools import simple_message_box

def invoker(mdi,fname,fpath,shortcut=None):
    
    # imports the module from the given path
    app = SourceFileLoader(fname,fpath).load_module()
    aw=None
    for subw in reversed(mdi.subWindowList(QMdiArea.ActivationHistoryOrder)):
        if type(subw).__name__=='AltSubWindow':
            aw=subw
            break 
       
    if app.PQitemtype=='CurveIndicator':
        appitem=apiCurve(aw.plt,fname=fname, fpath=fpath)
    elif app.PQitemtype=='TrendLineIndicator':
        appitem=apiTrendLine(aw.plt,fname=fname,fpath=fpath)
    elif app.PQitemtype=='TextIndicator':
        appitem=apiTextStudy(aw.plt,fname=fname,fpath=fpath)
    elif app.PQitemtype=='HorizontalLineIndicator':
        appitem=apiHorLine(aw.plt,fname=fname,fpath=fpath)
    elif app.PQitemtype=='Script':
        appitem=apiScript(aw.plt,fname=fname, fpath=fpath,shortcut=shortcut)
    elif app.PQitemtype=='Expert':
        appitem=apiExpert(aw.plt,fname=fname, fpath=fpath)
    else:
        simple_message_box(text=app.PQitemtype+' - unknown type')

class apiBase:
    sigSeriesChanged=QtCore.Signal(object)
    def __init__(self, plt, fname=None, fpath=None,ts=None):
        self.plt=plt
        self.timeseries=self.ts=plt.chartitem.timeseries if ts is None else ts
        self.fname=fname
        self.fpath=fpath
        self.subitems=[]
        self.uf=self.locate_updatef()
        
        self.symbol=self.plt.symbol
        self.timeframe=self.plt.timeframe

        # !! as sigSeriesChanged is emitted after sigTimeseriesChanged, the former execution
        #appear to happen after the latter execution and thus override it. Confirmed empirically so far
        self.plt.sigTimeseriesChanged.connect(self.schange)

        # triggers self.initf() only if apiBase is called directly 
        # rather than via its subclass:
        if issubclass(apiBase,type(self)):
            self.initf()

    def schange(self,ts):
        self.timeseries=self.ts=ts
        self.sigSeriesChanged.emit(self)

    @property
    def series(self):
        return self.timeseries
    
    @property
    def yvalues(self):
        if hasattr(self,'values'):
            return self.values[1]
    
    @property
    def smodule(self):
        if self.fname is not None and self.fpath is not None:
            sm=SourceFileLoader(self.fname,self.fpath).load_module()
        else:
            sm=None
        return sm

    def initf(self):
        if hasattr(self.smodule,'PQinitf'):
            return self.smodule.PQinitf(self)
        else:
            pass
    
    def deinitf(self):
        if hasattr(self.smodule,'PQdeinitf'):
            return self.smodule.PQdeinitf(self)
        else:
            pass
    
    def locate_updatef(self):
            if self.smodule is not None and hasattr(self.smodule,'PQupdatef'):
                uf=self.smodule.PQupdatef
            else:
                uf=None
            return uf
        
    def updatef(self):
        if self.uf is None:
            return None
        else: 
            return self.uf(self)

    def create_subitem(self,itype,values=(0,0),**kwargs):
        if 'timeseries' not in kwargs or kwargs['timeseries'] is None:
            ts=self.timeseries
        else:
            ts=kwargs['timeseries']
        
        if itype=='Curve':    
            si=studies._CurveItem(ts,values)
        
        elif itype=='Bar':
            kwargs['width']*=self.timeseries.tf
            si=studies._BarItem(ts,values,**kwargs)
        
        elif itype=='Text':
            si=apiText(self.plt,values,frozen=True,persistent=False,**kwargs)
        
        elif itype=='Label':
            si=apiLabel(self.plt,frozen=True,persistent=False,**kwargs)
        
        elif itype=='TrendLine':
            vals=chtl.zero2P() if values==(0,0) else values
            si=_TrendLineItem(self.plt,values=vals,selectable=False,persistent=False,**kwargs)
        
        else:
            simple_message_box(text=itype+' - unknown type')
        
        self.subitems.append(si)
        if hasattr(self,'dockplt'):self.dockplt.addItem(si)
        else: self.plt.addItem(si)
        
        if hasattr(self,'right_clicked'):
            si.right_clicked=self.right_clicked
        
        if hasattr(self,'hoverEvent'):
            si.hoverEvent=lambda ev: self.hoverEvent(ev,subitem=si)

        return si

    def remove_subitem(self,si):
        if hasattr(self,'dockplt'):self.dockplt.removeItem(si)
        else: self.plt.removeItem(si)
        self.subitems.remove(si)

    def set_persistent(self,s):
        self.is_persistent=s

    def getViewBox(self):
        try:
            return super().getViewBox()
        except Exception:
            return self.dockplt.getViewBox()
    
    def set_chart(self,**kwargs):
        return chtl.set_chart(self.plt,**kwargs)

    def removal(self):
        self.deinitf()
        try:self.sigSeriesChanged.disconnect()
        except Exception: pass
        return super().removal()
        
class _apiItem:

    def set_persistent(self,s):
        self.is_persistent=s
    
    def set_selectable(self,s):
        self.is_selectable=s

    def left_clicked(self, ev):
        if self.is_selectable: super().left_clicked(ev)
        else: pass
    
    #api function
    def set_data(self,vls):
        return super().set_dt(vls)
    
    def get_data(self):
        return super().save_dt()

    #api function
    def set_properties(self,**props):
        return super().set_props(props)


class apiText(_apiItem,labelings.DrawText):
    props=dict(labelings.DrawText.props) #to break connection to other DrawText subclasses
    def __init__(self, plt, values=(0,0),window=0,frozen=False,persistent=True,**kwargs):
        #remove unfitting keywords
        for kw in 'ts','cache0':
            if kw in kwargs: del kwargs[kw]
        super().__init__(plt,**kwargs)
        self.set_frozen(frozen)
        self.set_persistent(persistent)
        self.dockplt=plt.subwindow.docks[window].widgets[0]
        self.metaprops={} #get rid of decorator
        self.set_dt(list(values))

class apiLabel(_apiItem, labelings.DrawLabel):
    props=dict(labelings.DrawLabel.props) #to break connection to other DrawLabel subclasses
    def __init__(self,plt,window=0,frozen=False,persistent=True,**kwargs):
        super().__init__(plt,**kwargs)
        self.dockplt=plt.subwindow.docks[window].widgets[0]
        self.set_frozen(frozen)
        self.set_persistent(persistent)
        self.metaprops={} #get rid of decorator
        self.set_bind()
        self.set_anchor(0,0.25)
        self.setState(Point(0,0))

    def set_bind(self,bind='tl'):
        self.bind=cfg.CORNER[bind]
        self.update_state()
        self.refresh()
    
    def get_bind(self):
        for key,val in cfg.CORNER.items():
            if self.bind==val:
                return key

class apiScript(apiBase,QtCore.QObject):
    def __init__(self, *args,dockplt=None,shortcut=None,**kwargs):
        super().__init__(*args,**kwargs)
        super(apiBase,self).__init__()
        self.dockplt=self.plt if dockplt is None else dockplt
        self.shortcut=shortcut
        self.initf()

class apiExpert(apiBase,apiLabel):
    props=dict(labelings.DrawLabel.props) #to break connection to other DrawLabel subclasses
    def __init__(self, plt, fname=None, fpath=None, ts=None,caller=None):
        for itm in plt.listItems(): #block more than one expert on a single plot
            if isinstance(itm,self.__class__):
                return
        self.props['live']=True
        super().__init__(plt, fname, fpath, ts)
        self.ef=self.locate_executef()
        super(apiBase,self).__init__(plt,caller=caller)
        if self.caller!='open_subw':
            self.set_text(self.marker)
            self.set_fontsize(cfg.API_LABEL_FONTSIZE)
            plt.addItem(self)
        self.set_bind('tr')
        self.setState([0,0])
        self.set_anchor(1,0.25)
        self.set_frozen(True)
        self.initf()

        self.plt.mwindow.sigMainWindowVariablesUpdate.connect(self.status_update)
        self.plt.lc_thread.sigLastCandleUpdated.connect(self.executef)
    
    @property
    def fname(self):
        return self.props['fname']
    
    @fname.setter
    def fname(self,a):
        self.props['fname']=a
    
    @property
    def fpath(self):
        return self.props['fpath']
    
    @fpath.setter
    def fpath(self,a):
        self.props['fpath']=a

    @property
    def live(self):
        return self.props['live']
    
    @live.setter
    def live(self,s):
        self.props['live']=s

    @property
    def expert_on(self):
        return self.live and self.plt.mwindow.props['experts_on']
    
    @property
    def marker(self):
        if self.fname is not None:
            if self.expert_on:
                a=self.fname.partition('.')[0]+' \u2714'
            else:
                a=self.fname.partition('.')[0]+' \u2716'
            return a

    def status_update(self):
        self.set_text(self.marker)
        self.set_fontsize(cfg.API_LABEL_FONTSIZE)
    
    def create_menu(self): #override
        context_menu=QMenu()
        self.live_act=context_menu.addAction('Live')
        self.live_act.setCheckable(True)
        context_menu.addSeparator()
        self.rem_act=context_menu.addAction('Remove')
        self.update_menu()
        return context_menu
    
    def update_menu(self): #override
        self.live_act.setChecked(True) if self.live else self.live_act.setChecked(False)

    def right_clicked(self, ev): #override
        ev_pos=ev.screenPos()
        self.maction=self.context_menu.exec(QPoint(ev_pos.x(),ev_pos.y()))
        if self.maction==self.rem_act:
            self.removal()
            return
        elif self.maction==self.live_act:
            self.live=not self.live
            self.status_update()
    
    def locate_executef(self):
            if self.smodule is not None and hasattr(self.smodule,'PQexecutef'):
                ef=self.smodule.PQexecutef
            else:
                ef=None
            return ef
        
    def executef(self):
        if self.ef is None or not self.expert_on:
            return None
        else: 
            return self.ef(self)
    
    def ts_change(self, ts):
        super().ts_change(ts)
        self.timeseries=self.ts
        self.plt.lc_thread.sigLastCandleUpdated.connect(self.executef)

    def saveState(self):
        a=super().saveState()
        a['fname']=self.fname
        a['fpath']=self.fpath
        return a
    
    def set_props(self, props):
        super().set_props(props)
        if self.caller=='open_subw':
            self.initf()
            self.ef=self.locate_executef()
            self.uf=self.locate_updatef()
    
    def removal(self):
        self.plt.mwindow.sigMainWindowVariablesUpdate.disconnect(self.status_update)
        self.plt.lc_thread.sigLastCandleUpdated.disconnect(self.executef)
        for si in self.subitems:
            if hasattr(si,'removal'):
                si.removal()
        return super().removal()
    
def api_study_factory(base):   
    class _apiStudy(apiBase,base):
        def __init__(self, plt, fname=None, fpath=None,ts=None,**kwargs):
            super().__init__(plt,fname,fpath,ts)
            self.cf=self.locate_computef()
            #kwords is a mechanism to assign "standard" self.* variables 
            #without explicitly calling self in the body of the user app:
            kwords=self.smodule.PQkwords if hasattr(self.smodule,'PQkwords') else {} 
            sm=self.smodule
            if hasattr(sm,'PQcache0'):
                c0=sm.PQcache0
            else:
                c0={}
            super(apiBase,self).__init__(plt,ts=self.timeseries,cache0=c0,**kwords,**kwargs)
            if hasattr(self,'caller') and self.caller!='open_subw':
                self.initf()
        
        @property
        def tooltipinfo(self):
            a=list(self.xttip())
            ytext=self.values[1][a[0]]
            a.insert(2,ytext)
            return a

        def locate_computef(self):
            if self.smodule is not None and hasattr(self.smodule,'PQcomputef'):
                cf=self.smodule.PQcomputef
            else:
                cf=None
            return cf
        
        def computef(self):
            if self.cf is None:
                return None
            else: 
                return self.cf(self)
        
        def right_clicked(self,ev): #full override
            ev_pos=ev.screenPos()
            contextMenu=QMenu()
            contextMenu.addSection(self.fname)
            refreshAct=contextMenu.addAction('Refresh')
            contextMenu.addSeparator()
            remAct=contextMenu.addAction('Remove')
            action=contextMenu.exec(QPoint(ev_pos.x(),ev_pos.y()))
            if action==remAct:
                self.remove_act()
            elif action==refreshAct:
                self.remove_act()
                mdi=self.plt.mwindow.mdi
                invoker(mdi,self.fname,self.fpath)

        def save_props(self):
            a=super().save_props()
            a['fname']=self.fname
            a['fpath']=self.fpath
            return a
        
        def replot(self):
            sm=self.smodule
            if hasattr(sm,'PQreplot'):
                return sm.PQreplot(self)
            else:
                return super().replot()
        
        def mreplot(self):
            return super().replot()

        def set_api(self,props):
            if hasattr(self,'caller') and self.caller=='open_subw':
                self.fname=props['fname']
                self.fpath=props['fpath']
                self.cf=self.locate_computef()
                self.uf=self.locate_updatef()
                if hasattr(self.smodule,'PQkwords'):
                    kwords=self.smodule.PQkwords
                    for key,value in kwords.items():
                        setattr(self,key,value)
                    if hasattr(self,'windowed') and self.windowed==True:
                        self.labeltext=TextItem(anchor=(0,0))
                        self.dockplt.addItem(self.labeltext,ignoreBounds=True)
                        self.set_label()
                        self.dockplt.sigRangeChanged.connect(self.set_label)
                        self.sigReplotted.connect(self.set_label)            
            sm=self.smodule
            if hasattr(sm,'PQcache0'):
                for key,value in sm.PQcache0.items():
                    if key not in self.cache0:
                        self.cache0[key]=value
        
        def set_props(self,props):
            self.set_api(props)
            a=super().set_props(props)
            if hasattr(self,'caller') and self.caller=='open_subw':
                self.initf()           
            return a

        def ttip(self): #full override
            sm=self.smodule
            if hasattr(sm,'PQtooltip'):
                return sm.PQtooltip(self)
            else:
                index,xtext,ytext,pre=self.tooltipinfo
                res='{}\n{}\n{:.{pr}f}'.format(self.fname,xtext,ytext,pr=pre)
                return res
        
        @chtl.string_to_html(text_color='black')
        def html_ttip(self):
            return self.ttip()
        
        def label_t(self): #full override
            sm=self.smodule
            if hasattr(sm,'PQstudylabel'):
                return sm.PQstudylabel(self)
            else:
                return ''
        
        def hoverEvent(self, ev, subitem=None):
            obj=self if subitem is None else subitem
            if self.hover_on==True:
                obj.setToolTip(self.html_ttip())
        
        def create_subitem(self, itype, values=(0, 0), **kwargs):
            si=super().create_subitem(itype, values, **kwargs)
            si.setParent(self)
            return si

    return _apiStudy

apiCurveItem=api_study_factory(studies.StudyCurveItem)

class apiCurve(apiCurveItem):
    def __init__(self, plt, fname=None, fpath=None, ts=None, **kwargs):
        super().__init__(plt, fname, fpath, ts, **kwargs)

############################
class _TrendLineItem(_apiItem,drawings.DrawTrendLine):
    def __init__(self, plt, values=None,dialog=None,width=None,color=None,style=None,
        selectable=True,persistent=True,caller=None,**kwargs):
        super().__init__(plt, dialog=dialog,caller=caller)
        penprops=dict(width=width,color=color,style=style)
        self.set_persistent(persistent)
        self.set_selectable(selectable)
        for key,item in penprops.items():
            if item is not None:
                setattr(self,key,item)
                self.set_props(self.props)
        self.set_selected(False)
        if values is not None:
            self.set_data(values)

def api_noncurve_study_factory(base):
    class _apiNonCurve(base):
        def __init__(self, plt, fname=None, fpath=None, ts=None, **kwargs):
            self.hover_on=True #use initf() to set to False
            super().__init__(plt, fname, fpath, ts, **kwargs)
            if hasattr(self,'caller') and self.caller!='open_subw':
                self.plt.addItem(self)
            self.set_persistent(True)
            values=self.computef()
            if values is not None:
                self.set_data(values)
            self.plt.lc_thread.sigLastCandleUpdated.connect(self.replot)
            self.plt.lc_thread.sigInterimCandleUpdated.connect(self.replot)

        def set_props(self,props):
            super().set_props(props)
            if hasattr(self,'caller') and self.caller=='open_subw':
                values=self.computef()
                if values is not None:
                    self.set_data(values)

        def replot(self):
            ts=self.plt.chartitem.timeseries
            if self.timeseries is not ts:
                self.timeseries=ts
            vals=self.computef()
            if vals is not None:
                self.set_data(vals)
        
        #overrides parent class ts_change, works for drawings.  Labelings should override
        def ts_change(self,ts):
            self.timeseries=ts
            self.replot()
            self.plt.lc_thread.sigLastCandleUpdated.connect(self.replot)
            self.plt.lc_thread.sigInterimCandleUpdated.connect(self.replot)

        def ttip(self): #full override
            sm=self.smodule
            if hasattr(sm,'PQtooltip'):
                return sm.PQtooltip(self)
            else:
                return self.fname

        def remove_act(self):
            self.plt.lc_thread.sigLastCandleUpdated.disconnect(self.replot)
            self.plt.lc_thread.sigInterimCandleUpdated.disconnect(self.replot)
            for si in self.subitems:
                if hasattr(si,'removal'):
                    si.removal()
            return super().removal()

    return _apiNonCurve

##################################
_apiTLItem=api_study_factory(_TrendLineItem)
_apiTL=api_noncurve_study_factory(_apiTLItem)

class apiTrendLine(_apiTL):
    def __init__(self, plt, fname=None, fpath=None, ts=None, caller=None,**kwargs):
        super().__init__(plt, fname, fpath, ts, selectable=False,caller=caller,**kwargs)

#################################
_apiTextStudyItem=api_study_factory(apiText)
_apiTextStudy=api_noncurve_study_factory(_apiTextStudyItem)

class apiTextStudy(_apiTextStudy):
    def __init__(self, plt, fname=None, fpath=None, ts=None, **kwargs):
        super().__init__(plt, fname, fpath, ts, frozen=True, **kwargs)
            
#################################
class _HorLineItem(_apiItem,drawings.DrawHorLine):
    def __init__(self, plt, values=None,dialog=None,width=None,color=None,style=None,
        selectable=True,persistent=True,caller=None,**kwargs):
        super().__init__(plt, dialog=dialog,caller=caller)
        penprops=dict(width=width,color=color,style=style)
        self.set_persistent(persistent)
        self.set_selectable(selectable)
        for key,item in penprops.items():
            if item is not None:
                setattr(self,key,item)
                self.set_props(self.props)
        self.set_selected(False)
        if values is not None:
            self.set_data(values)

_apiHLItem=api_study_factory(_HorLineItem)
_apiHL=api_noncurve_study_factory(_apiHLItem)

class apiHorLine(_apiHL):
    def __init__(self, plt, fname=None, fpath=None, ts=None, caller=None,**kwargs):
        super().__init__(plt, fname, fpath, ts, selectable=False,caller=caller,**kwargs)