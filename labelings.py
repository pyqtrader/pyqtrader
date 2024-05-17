import PySide6
from PySide6 import QtWidgets,QtCore,QtGui
from pyqtgraph import Point,TextItem
from pyqtgraph.Qt.QtWidgets import QGraphicsItem
from pyqtgraph import functions as fn

import cfg
import drawings as drws, drawings
import overrides as ovrd, overrides
import charttools as chtl,charttools
import uitools
from timeseries import dtPoint, dtCords

from _debugger import _print,_printcallers,_c,_pc,_p

class _DrawElliottLabel(TextItem):
    def __init__(self,*args, handler=None,place=None,**kwargs):
        super().__init__(*args,anchor=(0.5,0.5),**kwargs)
        self.is_persistent=False
        self.handler=handler
        self.is_draw=self.handler.is_draw
        self.place=place 
        self.set_props()


    def mouseDragEvent(self, ev):
        if not self.handler.frozen:
            if ev.button() == QtCore.Qt.MouseButton.LeftButton:
                if ev.isStart():
                    self.moving = True
                    self.cursorOffset = self.pos() - self.mapToParent(ev.buttonDownPos())
                    self.startPosition = self.pos()
                ev.accept()

                if not self.moving:
                    return

                self.setPos(self.cursorOffset + self.mapToParent(ev.pos()))
                if ev.isFinish():
                    self.moving = False
                    xy=self.cursorOffset + self.mapToParent(ev.pos())
                    
                    # similar to mouse_update in ROIs,=> force=False 
                    # used to update dts in dtcords
                    update_dtc=dtCords.make(self.handler.clicks).set_cord(self.place,dtPoint(None,*xy))
                    self.handler.set_dtc(update_dtc) 

    # makes self hoverable and ensures that self.is_draw propogates to plt.mouse_clicked
    # for selection/deselection purposes
    def hoverEvent(self,ev):
        pass

    def set_props(self):
        h=self.handler
        txt=self.handler.labeldict[h.degree][self.place]
        self.setHtml('<div style="font-size: {}pt;">{}</div>'.format(h.fontsize,txt))
        if h.color is not None:
            self.setColor(h.color)
    
    def set_selected(self,s):
        if s:
            self.border=fn.mkPen(self.color)
            self.update()
        else:
            self.border=fn.mkPen(None)
            self.update()

class DrawElliottImpulse(QGraphicsItem,drws.DrawProps):
    multiclick=True
    def __init__(self, plt, xy=None, dockplt=None, caller=None, labeldict=cfg.ELLIOTT_IMPULSE, 
                 degree=cfg.D_EIDEGREE,fontsize=cfg.D_ELSIZE, dialog=uitools.ElliottPropDialog):
        super().__init__()
        self.config_props(plt.mwindow,caller=caller)
        self.plt=plt if dockplt is None else dockplt
        self.timeseries=self.plt.chartitem.timeseries
        self.dialog=dialog
        self.labels=[]
        
        self.labeldict=labeldict
        if not self.degree: self.degree=degree
        if not self.fontsize: self.fontsize=fontsize
        if not self.frozen: self.frozen=False
        
        self.clicks=len(self.labeldict[self.degree])
        self.frozen=False
        self.context_menu=self.create_menu()

        self._dtc=dtCords.make(self.clicks).apply(dtPoint(ts=self.timeseries))

        self.plt.addItem(self)

        # add first label initiated by mouse clicks, and connect to mouse click processor
        if xy:
            self.add_label(xy[0])
            self.plt.scene().sigMouseClicked.connect(self.setup_mouseclicks)
        
        # fill up all labels if restored from a saved file
        else:
            for _ in range(self.clicks):
                self.add_label()
            self.plt.scene().sigMouseClicked.connect(self.mouse_clicked)
        
        self.plt.sigTimeseriesChanged.connect(self.ts_change)


    @property
    def rawdtc(self):
        endpoints=[]
        for label in self.labels:
            endpoints.append(dtPoint(None,*label.pos()))
        return dtCords(endpoints)
    
    @property
    def fontsize(self):
        return self.props.get('fontsize',None)
    
    @fontsize.setter
    def fontsize(self,x):
        self.props['fontsize']=x

    @property
    def degree(self):
        return self.props.get('degree',None)
    
    @degree.setter
    def degree(self,x):
        self.props['degree']=x
    
    @property
    def frozen(self):
        return self.props.get('frozen',None)
    
    @frozen.setter
    def frozen(self,x):
        self.props['frozen']=x

    @property
    def is_selected(self):
        if len(self.labels)==0:
            return False
        
        if self.labels[0].border.style()==QtGui.Qt.PenStyle.NoPen:
            return False
        else: 
            return True
    

    def setup_mouseclicks(self,ev):
    
        if ev.button()==QtCore.Qt.MouseButton.LeftButton:
            xy=self.plt.mapped_xy
            self.add_label(xy)

        if len(self.labels)>=self.clicks:
            self.plt.scene().sigMouseClicked.disconnect(self.setup_mouseclicks)
            self.plt.scene().sigMouseClicked.connect(self.mouse_clicked)
            
            return

    def mouse_clicked(self,ev):

        if self.shape().contains(ev.pos()):
            if ev.button()==QtCore.Qt.MouseButton.RightButton:
                self.right_clicked(ev)
            elif ev.button()==QtCore.Qt.MouseButton.LeftButton:
                self.set_selected(not self.is_selected)

    def set_dtc(self, dtc, force=False):
        
        update_pos=drws.DrawItem.set_dtc(self,dtc,force=force)
        
        if update_pos:
            points=self._dtc.get_raw_points()
            for i,label in enumerate(self.labels):
                label.setPos(*points[i])

        return update_pos

    def get_dtc(self):
        return self.rawdtc.fillnone(self._dtc)
    
    def save_dtc(self):
        return self.get_dtc().rollout()

    def add_label(self,xy=None):
        self.labels.append(_DrawElliottLabel(handler=self,place=len(self.labels)))
        if xy: # works on mouse click setup
            update_dtc=dtCords.make(n=self.clicks).set_cord(len(self.labels)-1,dtPoint(None,*xy))
            self.set_dtc(update_dtc, force=True)
        self.plt.addItem(self.labels[-1])

    def set_selected(self,s):
        for label in self.labels:
            label.set_selected(s)
    
    def create_menu(self):
        context_menu=QtWidgets.QMenu()
        self.freeze_act=context_menu.addAction('Freeze')
        self.freeze_act.setCheckable(True)
        self.prop_act=context_menu.addAction('Properties')
        self.pushdown_act=context_menu.addAction('Push down')
        self.liftup_act=context_menu.addAction('Lift up')
        context_menu.addSeparator()
        self.rem_act=context_menu.addAction('Remove')
        self.update_menu()
        return context_menu

    def update_menu(self):
        self.freeze_act.setChecked(True) if self.frozen else self.freeze_act.setChecked(False)

    def right_clicked(self,ev,**kwargs):
        ev_pos=ev.screenPos()
        self.maction=self.context_menu.exec(QtCore.QPoint(ev_pos.x(),ev_pos.y()))
        if self.maction==self.rem_act:
            self.removal()
            return
        elif self.maction==self.prop_act:
            self.dialog(self.plt,item=self,**kwargs)
        elif self.maction==self.freeze_act:
            self.freezing()
        elif self.maction==self.pushdown_act:
            zv=self.zValue()
            self.setZValue(zv-1)
        elif self.maction==self.liftup_act:
            zv=self.zValue()
            self.setZValue(zv+1)

    def freezing(self):
        self.frozen=not self.frozen
        return not self.frozen
    
    def ts_change(self,ts):
        self.timeseries=ts
        self.set_dtc(dtPoint(ts=ts))

    def set_props(self, props):#full override
        for key in props:
            self.props[key]=props[key]
        if self.is_persistent and self.caller!='open_subw':
            self.mwindow.props[self.__module__+'.'+type(self).__name__]=self.get_props()

        for label in self.labels:
            label.set_props()
            # Ensure that the border is changed if the item is selected
            if label.border.style()!=QtGui.Qt.PenStyle.NoPen:
                label.border=fn.mkPen(self.color)
                label.update()
        
        self.update_menu()

        return

    def paint(self, p, *args):
        pass
    
    def boundingRect(self):
        return QtCore.QRectF()

    def shape(self):
        # Create a QPainterPath that includes the shapes of all text items
        path = QtGui.QPainterPath()
        for label in self.labels:
            label_shape = label.shape()
            # Transform the shape of the text item to the coordinate system of the mouse
            transformed_shape = label.mapToDevice(label_shape)
            path.addPath(transformed_shape)
        return path

    #override
    def item_hide(self, **kwargs):
        for label in self.labels:
            label.hide()
        self.is_persistent=False
        self.hide()
    
    #override
    def item_show(self, **kwargs):
        for label in self.labels:
            label.show()
        self.is_persistent=True
        self.show()


    def removal(self):
        self.plt.scene().sigMouseClicked.disconnect(self.mouse_clicked)
        self.plt.sigTimeseriesChanged.disconnect(self.ts_change)
        for label in self.labels:
            self.plt.removeItem(label)
        self.plt.removeItem(self)

class EC_Dialog(uitools.ElliottPropDialog):
    
    initials=dict(uitools.ElliottPropDialog.initials)
    initials['degree']=degree=cfg.D_ECDEGREE
    def __init__(self, *args,**kwargs):
        super().__init__(*args,title='Elliott Correction',labeldict=cfg.ELLIOTT_CORRECTION,**kwargs)

class DrawElliottCorrection(DrawElliottImpulse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, dialog=EC_Dialog,labeldict=cfg.ELLIOTT_CORRECTION,
            degree=cfg.D_ECDEGREE,**kwargs)

class EEC_Dialog(uitools.ElliottPropDialog):
    initials=dict(uitools.ElliottPropDialog.initials)
    initials['degree']=degree=cfg.D_EECDEGREE
    def __init__(self, *args,**kwargs):
        super().__init__(*args,title='Elliott Extended Correction',labeldict=cfg.ELLIOTT_EXTENDED_CORRECTION,**kwargs)

class DrawElliottExtendedCorrection(DrawElliottImpulse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, dialog=EEC_Dialog,labeldict=cfg.ELLIOTT_EXTENDED_CORRECTION,
            degree=cfg.D_EECDEGREE,**kwargs)

class DrawText(TextItem):
    props=dict(text='Text',font=None,fontsize=None,color=None,anchX=0.5,anchY=0.5,italic=False,bold=False)
    def __init__(self, plt,dockplt=None,text='Text',dialog=uitools.DrawTextDialog,
        caller=None,**kwargs):
        clr=self.__class__.props['color'] ##workaround the conflict of the parent class name conflict
        super().__init__(text=text,**kwargs)
        self.is_persistent=True
        self.plt=plt if dockplt is None else dockplt
        if clr is not None:##    
            self.color=clr
        else:
            self.color=self.plt.chartprops[cfg.foreground]
        self.setColor(self.color)##
        self.ts=plt.chartitem.timeseries
        self.props=dict(self.__class__.props)
        if self.font is None:
            self.font=self.textItem.font().family()
        if self.fontsize is None:
            self.fontsize=self.textItem.font().pointSize()
        self.frozen=False
        self.text=text
        self.set_text(self.text) #to process snippets
        self.set_anchor()
        self.dialog=dialog
        self.context_menu=self.create_menu()
        self.is_new=False
        self.caller=caller

        self._dtp=dtPoint(ts=self.ts)

        if self.caller=='click_action':#fast way to setup the first drawing by mouse clicks
            self.is_new=True
            self.set_props(self.props)
            self.plt.addItem(self) #stub to ensure signals connection
            for dk in self.plt.subwindow.docks:
                dkplt=dk.widgets[0]
                dkplt.scene().sigMouseClicked.connect(self.setup_mouseclick)
        
        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.LeftButton | QtCore.Qt.MouseButton.RightButton)
        self.plt.sigTimeseriesChanged.connect(self.ts_change)   
    
    def set_anchor(self,x=None,y=None):
        if x is not None:
            self.anchX=x
        if y is not None:
            self.anchY=y
        self.setAnchor((self.anchX,self.anchY))

    @property
    def text(self):
        return self.props['text']
       
    @text.setter
    def text(self,a):
        self.props['text']=a
    
    @property
    def font(self):
        return self.props['font']
       
    @font.setter
    def font(self,a):
        self.props['font']=a
    
    @property
    def fontsize(self):
        return self.props['fontsize']
       
    @fontsize.setter
    def fontsize(self,a):
        self.props['fontsize']=a

    @property #parent class override
    def color(self):
        return self.props['color']
       
    @color.setter
    def color(self,a):
        if isinstance(a,QtGui.QColor): #to ensure JSON compatibility of the parent class format 
            a=a.name()
        self.props['color']=a
    
    @property
    def anchX(self):
        return self.props['anchX']
       
    @anchX.setter
    def anchX(self,a):
        self.props['anchX']=a
    
    @property
    def anchY(self):
        return self.props['anchY']
       
    @anchY.setter
    def anchY(self,a):
        self.props['anchY']=a
    
    @property
    def frozen(self):
        return self.props['frozen']
    
    @frozen.setter
    def frozen(self,a):
        self.props['frozen']=a
    
    @property
    def italic(self):
        return self.props['italic']
    
    @italic.setter
    def italic(self,a):
        self.props['italic']=a
        self.__class__.props['italic']=a
        if self.caller!='open_subw':
            self.metaprops['italic']=a

    @property
    def bold(self):
        return self.props['bold']
    
    @bold.setter
    def bold(self,a):
        self.props['bold']=a
        self.__class__.props['bold']=a
        if self.caller!='open_subw':
            self.metaprops['bold']=a
    
    @property
    def metaprops(self):
        if (md:=self.__class__.__module__)==__name__:    
            return self.plt.mwindow.props[md+'.'+self.__class__.__name__]
        else:
            return {}
    
    @metaprops.setter
    def metaprops(self,a):
        if (md:=self.__class__.__module__)==__name__: 
            self.plt.mwindow.props[md+'.'+self.__class__.__name__]=a
        else: #to discard api and other class props
            d={}
            d=a
        
    def setup_mouseclick(self,ev):
        pitm=ev.currentItem.parentItem()
        for dk in self.plt.subwindow.docks:#identify clicked dock plot
            dkplt=dk.widgets[0]
            if pitm is dkplt.pitm:
                break
        if pitm is not self.plt.pitm:
            self.plt.removeItem(self)
            dkplt.addItem(self)
            self.plt.sigTimeseriesChanged.disconnect(self.ts_change)
            self.plt=dkplt
            self.plt.sigTimeseriesChanged.connect(self.ts_change)
        self.set_text(self.text)
        xy=self.plt.mapped_xy
        
        self._set_dtc(dtPoint(None,*xy),force=True)
        
        for dk in self.plt.subwindow.docks:
            dkplt=dk.widgets[0]
            dkplt.scene().sigMouseClicked.disconnect(self.setup_mouseclick)
    
    def create_menu(self):
        context_menu=QtWidgets.QMenu()
        self.freeze_act=context_menu.addAction('Freeze')
        self.freeze_act.setCheckable(True)
        self.prop_act=context_menu.addAction('Properties')
        self.ital_act=context_menu.addAction('Italics')
        self.bold_act=context_menu.addAction('Bold')
        self.pushdown_act=context_menu.addAction('Push down')
        self.liftup_act=context_menu.addAction('Lift up')
        context_menu.addSeparator()
        self.rem_act=context_menu.addAction('Remove')
        self.update_menu()
        return context_menu
    
    def update_menu(self):
        self.freeze_act.setChecked(True) if self.frozen else self.freeze_act.setChecked(False)

    def mouseClickEvent(self,ev):
        if ev.button()==QtCore.Qt.MouseButton.RightButton:
            self.right_clicked(ev)
    
    def mouseDragEvent(self, ev):
        if not self.frozen:
            if ev.button() == QtCore.Qt.MouseButton.LeftButton:
                if ev.isStart():
                    self.moving = True
                    self.cursorOffset = self.pos() - self.mapToParent(ev.buttonDownPos())
                    self.startPosition = self.pos()
                ev.accept()

                if not self.moving:
                    return

                self.setPos(self.cursorOffset + self.mapToParent(ev.pos()))
                if ev.isFinish():
                    self.moving = False
                    xy=self.cursorOffset + self.mapToParent(ev.pos())
                    
                    # similar to mouse_update in ROIs,=> force=False 
                    # used to update dts in dtcords
                    update_dtp=dtPoint(None,*xy)
                    self._set_dtc(update_dtp) 


    def right_clicked(self,ev,**kwargs):
        ev_pos=ev.screenPos()
        self.maction=self.context_menu.exec(QtCore.QPoint(ev_pos.x(),ev_pos.y()))
        if self.maction==self.rem_act:
            self.removal()
            return
        elif self.maction==self.prop_act:
            self.dialog(self.plt,item=self,**kwargs)
        elif self.maction==self.freeze_act:
            self.freezing()
        elif self.maction==self.ital_act:
            self.stylize()
        elif self.maction==self.bold_act:
            self.stylize(mode='bold')
        elif self.maction==self.pushdown_act:
            zv=self.zValue()
            self.setZValue(zv-1)
        elif self.maction==self.liftup_act:
            zv=self.zValue()
            self.setZValue(zv+1)

    def freezing(self):
        self.frozen=not self.frozen
        return not self.frozen

    ###explicit setups for api and other purposes:
    def set_frozen(self,s): 
        self.frozen=s
        self.update_menu()

    def set_bold(self,s):
        self.bold=s
        (font:=self.textItem.font()).setBold(s)
        self.setFont(font)
    
    def set_italic(self,s):
        self.italic=s
        (font:=self.textItem.font()).setItalic(s)
        self.setFont(font)
    
    def set_fontsize(self,sz):
        self.fontsize=sz
        self.setFontSize(sz)
    #processes sniptexts unlike raw setText():
    def set_text(self,text,**kwargs):
        self.text=text
        a=self.sniptext(text)
        self.setText(a,**kwargs)
    ######################################

    def stylize(self,mode='italic',toggle=True):
        if isinstance(self.font, str):
            self.font=self.textItem.font()
        
        if mode=='italic':
            fnc=self.font.setItalic
            trigger=self.italic
        elif mode=='bold':
            fnc=self.font.setBold
            trigger=self.bold
        
        if toggle==True:
            if trigger:
                fnc(False)
                self.setFont(self.font)
                trigger=False
            else:
                fnc(True)
                self.setFont(self.font)
                trigger=True
            
            if mode=='italic':
                self.italic=trigger
            elif mode=='bold':
                self.bold=trigger
        else:
            fnc(trigger)
            self.setFont(self.font)

        self.font=self.font.family()

    # Similar to AltInfiniteLine set_dtc with the exception of setPos(float,float)
    def _set_dtc(self,dtpos, force=False):

        c=dtpos if type(dtpos) == dtPoint else dtPoint(*dtpos)
            
        self._dtp=self._dtp.apply(c) #update dtc

        # dont setPos solely based on getPos coords unless explicitly forced
        # to avoid idle setPos eg. on mouse_updates
        update_pos=(c.dt is not None or c.ts is not None) or force
        if update_pos:  
            self.setPos(self._dtp.x,self._dtp.y)

        return update_pos

    # Help DrawLabel override
    def set_dtc(self,*args,**kwargs):
        return self._set_dtc(*args,**kwargs)      

    def get_dtc(self):

        c=dtPoint(None,*self.pos()).fillnone(self._dtp) # sets dt from self._dtp instead of None
        
        return c

    def save_dtc(self):
        return self.get_dtc().rollout()

    def ts_change(self,ts):
        self.timeseries=ts
        self.set_dtc(dtPoint(ts=ts))
        self.setText(self.text) #snippets processing
        self.set_fontsize(self.fontsize)

    def set_props(self,props):
        if isinstance(props['font'],QtGui.QFont):
            props['font']=props['font'].family()
        open=(self.caller=='open_subw')
        for key in props:
            if not open:
                self.__class__.props[key]=props[key]
            self.props[key]=props[key]
        if not open:
            self.metaprops=self.props
        if props['text'] is not None:
            self.text=props['text']
            self.set_text(self.text)

        if props['font'] is not None:
            self.setFont(props['font'])
        else:
            self.font=self.textItem.font().family()
        
        if props['fontsize'] is not None:
            self.set_fontsize(props['fontsize'])
        if props['color'] is not None:
            self.setColor(props['color'])
        
        self.set_anchor()

        try:
            self.italic=props['italic']
            self.stylize(toggle=False)
        except Exception:
            self.stylize(toggle=False) #no italics key rendered from the dialog menu
        try:
            self.bold=props['bold']
            self.stylize(mode='bold',toggle=False)
        except Exception:
            self.stylize(mode='bold',toggle=False) #no italics key rendered from the dialog menu
        self.update_menu()
    
    def save_props(self):
        return self.props

    def sniptext(self,text):
        a=text
        try:a=a.replace('!@tf',cfg.tf_to_label(self.ts.tf))
        except Exception:pass
        try:a=a.replace('!@tk',self.ts.symbol)
        except Exception:pass
        try:a=a.replace('!@pq','@pyqtrader')
        except Exception:pass
        return a
    
    def removal(self):
        self.plt.sigTimeseriesChanged.disconnect(self.ts_change)
        self.plt.removeItem(self)

class DrawLabel(DrawText):
    props=dict(DrawText.props)
    props['text']=cfg.D_LABEL
    props['bind']=cfg.CORNER['tl']
    def __init__(self, *args, text=cfg.D_LABEL,**kwargs):
        clr=self.__class__.props['color'] ##workaround the conflict of the parent class name conflict
        super().__init__(*args,dialog=DrawLabelDialog,text=text,**kwargs)
        if clr is not None:##
            self.color=clr
        else:
            self.color=self.plt.chartprops[cfg.foreground]
        self.setColor(self.color)##
        
        self.state=[None,None]
        self.ax=self.plt.getAxis('bottom')
        self.ay=self.plt.getAxis('right')

        if self.is_new==False:
            self.plt.vb.sigStateChanged.connect(self.refresh)
            self.plt.vb.sigTransformChanged.connect(self.refresh)

    @property
    def bind(self):
        return self.props['bind']
    
    @bind.setter
    def bind(self,a):
        self.props['bind']=a

    @property
    def ci(self):
        return self.plt.subwindow.plt.chartitem #dock plots fix
    
    @property
    def vbw(self):
        return self.plt.vb.size().width()
    
    @property
    def vbh(self):
        return self.plt.vb.size().height()

    def setup_mouseclick(self,ev):
        super().setup_mouseclick(ev)
        self.update_state()
        self.plt.vb.sigStateChanged.connect(self.refresh)
        self.plt.vb.sigTransformChanged.connect(self.refresh)

    def setState(self,state):
        st=None if None in state else Point(state[0],state[1])
        if st is not None:
            self.state=st
            if self.bind==cfg.CORNER['tr']:
                st=st+Point(self.vbw,0)
            elif self.bind==cfg.CORNER['bl']:
                st=st+Point(0,self.vbh)
            elif self.bind==cfg.CORNER['br']:
                st=st+Point(self.vbw,self.vbh)
            xy=self.ci.mapFromDevice(st)
            self.setPos(xy)
    
    def refresh(self):
        self.setState(self.state)
        self.bring_back()

    def saveState(self):
        return [self.state.x(),self.state.y()]
    
    def set_dtc(self,state):
        return self.setState(state)
    
    def save_dtc(self):
        return self.saveState()
    
    def ts_change(self, ts):
        self.ax=self.plt.getAxis('bottom')
        self.ts=ts
        self.set_text(self.text) #snippets processing
        self.set_fontsize(self.fontsize)
        self.setState(self.state)

    def update_state(self):
        st=self.ci.mapToDevice(self.pos())
        if self.bind==cfg.CORNER['tl']:
            self.state=Point(st.x() if st.x()>0 else 0, st.y() if st.y()>0 else 0)
        elif self.bind==cfg.CORNER['tr']:
            x=self.vbw-st.x()
            self.state=Point(-x if x>0 else 0,st.y() if st.y()>0 else 0)
        elif self.bind==cfg.CORNER['bl']:
            y=self.vbh-st.y()
            self.state=Point(st.x() if st.x()>0 else 0, -y if y>0 else 0)
        elif self.bind==cfg.CORNER['br']:
            x=self.vbw-st.x()
            y=self.vbh-st.y()
            self.state=Point(-x if x>0 else 0, -y if y>0 else 0)
        else:
            self.state=Point(st.x() if st.x()>0 else 0, st.y() if st.y()>0 else 0)
        return self.state

    #brings the label back to the viewbox if it was lost outside
    #due to faulty anchoring
    def bring_back(self):
        st=self.ci.mapToDevice(self.pos())
        r=self.textItem.boundingRect()
        tl=r.topLeft()
        br=r.bottomRight()
        offset=(br-tl)
        if self.bind==cfg.CORNER['tl']:
            st+=offset*(Point(0,0.25)-self.anchor)
            if st.x()<0 or st.y()<0:
                self.set_anchor(0,0.25)
        elif self.bind==cfg.CORNER['tr']:
            st=(Point(self.vbw,0)-st)*Point(1,-1)
            st+=offset*(Point(0,0.25)-self.anchor)
            if st.x()<0 or st.y()<0:
                self.set_anchor(1,0.25)
        elif self.bind==cfg.CORNER['bl']:
            st=(Point(0,self.vbh)-st)*Point(-1,1)
            st+=offset*(Point(0,0.25)-self.anchor)
            if st.x()<0 or st.y()<0:
                self.set_anchor(0,0.75)
        elif self.bind==cfg.CORNER['br']:
            st-=Point(self.vbw,self.vbh)
            st+=offset*(Point(0,0.25)-self.anchor)
            if st.x()<0 or st.y()<0:
                self.set_anchor(1,0.75)
        else:
            if st.x()<0 or st.y()<0:
                self.set_anchor(0.5,0.5)

    def mouseDragEvent(self, ev):
        super().mouseDragEvent(ev)
        if not self.frozen:
            self.update_state()
    
    def removal(self):
        self.plt.vb.sigStateChanged.disconnect(self.refresh)
        self.plt.vb.sigTransformChanged.connect(self.refresh)
        super().removal()

class DrawLabelDialog(uitools.DrawTextDialog):
    initials=dict(uitools.DrawTextDialog.initials)
    initials['bind']=bind=cfg.CORNER['tl']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, exec_on=False, title='Label', **kwargs)
        self.state_dict['bind']=self.__class__.bind=self.item.bind

        self.order+=1
        label0=QtWidgets.QLabel('Bind: ')
        self.bindbox=QtWidgets.QComboBox()
        self.bindbox.insertItems(1,[cfg.CORNER[key] for key in cfg.CORNER])
        self.bindbox.setCurrentText(self.__class__.bind)
        self.layout.addWidget(label0,self.order,0)
        self.layout.addWidget(self.bindbox,self.order,1)
        self.bindbox.currentTextChanged.connect(lambda *args: setattr(self.__class__,'bind',self.bindbox.currentText()))
        self.order+=1

        
        self.set_values()
        self.embedded_db()
        self.exec()

    def set_values(self):
        try:
            self.bindbox.setCurrentText(cfg.CORNER['tl'] if self.__class__.bind is None else self.__class__.bind)
        except Exception:
            pass
        return super().set_values()

    def update_item(self, **kwargs):
        super().update_item(**kwargs)
        self.item.update_state()
    
    def reset_defaults(self):
        return super().reset_defaults()