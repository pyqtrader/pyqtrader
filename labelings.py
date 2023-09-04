import PySide6
from PySide6 import QtWidgets,QtCore,QtGui
from pyqtgraph import Point,TextItem

import cfg
import drawings as drws, drawings
import overrides as ovrd, overrides
import charttools as chtl,charttools
import uitools

from _debugger import _print,_printcallers,_c,_pc,_p

class _DrawElliottLabel(TextItem):
    def __init__(self,*args,parent=None,place=None,**kwargs):
        super().__init__(*args,anchor=(0.5,0.5),**kwargs)
        self.is_persistent=False
        self.is_draw=True #to ensure that the parent roi is not unselected on click
        self.setParent(parent)
        self.place=place
        self.update_pos()
        self.parent().plt.addItem(self)

        self.parent().plt.scene().sigMouseClicked.connect(self.mouse_clicked)
        self.parent().sigRegionChanged.connect(self.update_pos)
        self.parent().sigPropsUpdated.connect(self.set_props)
        self.parent().sigRemoval.connect(self.removal)

    def update_pos(self):
        try:
            pstate=self.parent().getState()
            ppos=pstate['pos']
            ppoint=pstate['points'][self.place]
            label_pos=ppoint+ppos
            self.setPos(label_pos)
        except Exception:
            pass      
    
    def mouse_clicked(self,ev):
        if self.isUnderMouse():
            if ev.button()==QtCore.Qt.MouseButton.LeftButton:
                self.parent().set_selected(not self.parent().translatable)
            elif ev.button()==QtCore.Qt.MouseButton.RightButton:
                self.parent().right_clicked(ev,valid=True)
    
    def hoverEvent(self,ev): #to ensure no unselection of the parent roi
        pass

    def set_props(self,labeldict,props):
        txt=labeldict[props['style']][self.place]
        self.setHtml('<div style="font-size: {}pt;">{}</div>'.format(props['fontsize'],txt))
        if props['color'] is not None:
            self.setColor(props['color'])

    def removal(self):
        self.parent().plt.scene().sigMouseClicked.disconnect(self.mouse_clicked)
        self.parent().sigRegionChanged.disconnect(self.update_pos)
        self.parent().sigPropsUpdated.disconnect(self.set_props)
        self.parent().sigRemoval.disconnect(self.removal)
        self.parent().plt.removeItem(self)

class DrawElliottImpulse(drws.DrawItem,drws.AltPolyLine):
    sigRemoval=QtCore.Signal()
    sigPropsUpdated=QtCore.Signal(object,object)
    
    def __init__(self, plt,coords=chtl.zero2P(),clicks=5,dialog=uitools.ElliottPropDialog,
        labeldict=cfg.ELLIOTT_IMPULSE,ellstyle=cfg.D_EISTYLE,**kwargs):
        props=dict(width=1,color=None,style=ellstyle,fontsize=cfg.D_ELSIZE)
        super().__init__(plt,clicks=clicks,dialog=dialog,props=props,**kwargs)
        super(drws.DrawItem,self).__init__(coords)
        self.initialisation()
        transparent=QtGui.QColor(QtCore.Qt.transparent)
        self.setPen(color=transparent)
        self.hoverPen.setColor(transparent)
        self.setZValue(-10)
        self.hsz=cfg.D_ELSIZE
        self.labeldict=labeldict
        self.is_draw=False #to exclude the body of the roi from valid selectable areas and leave only the segments as such areas
        self.labels=[]
        if self.is_new:
            self.set_label(0)
        else:
            for i in range(self.clicks):
                self.set_label(i)
        
        self.mouseClickEvent=lambda *args: None
        self.left_clicked=lambda *args: None
        self.mouseDragEvent=lambda *args: None
    
    @property
    def fontsize(self):
        return self.props['fontsize']
    
    @fontsize.setter
    def fontsize(self,x):
        self.props['fontsize']=x

    def set_label(self,count):
        label=self.labeldict[self.style][count]
        litem=_DrawElliottLabel(text=label,parent=self,place=count)
        self.set_props(self.props)
        self.labels.append(litem)

    def setup_mouseclicks(self, mouseClickEvent):
        self.set_label(self.click_count)
        xy=Point(self.plt.vb.mapSceneToView(mouseClickEvent.scenePos()))
        self.click_count+=1
        if self.click_count<self.clicks:
            self.xy.append(xy)
            self.write_state()
            self.setState(self.state)
        else:
            self.write_state()
            self.setState(self.state)
            self.xy_ticks_to_times()
            self.plt.scene().sigMouseClicked.disconnect(self.setup_mouseclicks)

    def set_props(self, props):#full override
        for key in props:
            self.props[key]=props[key]
        if self.is_persistent and self.caller!='open_subw':
            self.mwindow.props[self.__module__+'.'+type(self).__name__]=self.get_props()
        self.sigPropsUpdated.emit(self.labeldict,props)
    
    def left_clicked(self, ev):
        return super(drws.DrawItem,self).left_clicked(ev)

    def right_clicked(self, ev, valid=False):
        if valid==True:
            return super().right_clicked(ev)
    
    def ts_change(self, ts):
        super().ts_change(ts)
        self.setSelected(self.selected)
    
    def removal(self):
        self.sigRemoval.emit()
        return super().removal()

class EC_Dialog(uitools.ElliottPropDialog):
    labeldict=cfg.ELLIOTT_CORRECTION
    initials=dict(uitools.ElliottPropDialog.initials)
    initials['style']=cfg.D_ECSTYLE
    def __init__(self, *args,**kwargs):
        super().__init__(*args,title='Elliott Correction',**kwargs)

class DrawElliottCorrection(DrawElliottImpulse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, clicks=3, dialog=EC_Dialog,labeldict=cfg.ELLIOTT_CORRECTION,
            ellstyle=cfg.D_ECSTYLE,**kwargs)

class EEC_Dialog(uitools.ElliottPropDialog):
    labeldict=cfg.ELLIOTT_EXTENDED_CORRECTION
    initials=dict(uitools.ElliottPropDialog.initials)
    initials['style']=cfg.D_EECSTYLE
    def __init__(self, *args,**kwargs):
        super().__init__(*args,title='Elliott Extended Correction',**kwargs)

class DrawElliottExtendedCorrection(DrawElliottImpulse):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, dialog=EEC_Dialog,labeldict=cfg.ELLIOTT_EXTENDED_CORRECTION,
            ellstyle=cfg.D_EECSTYLE,**kwargs)

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
        self.xy=Point(0,0)
        self.dtxy=[0,0]
        self.dialog=dialog
        self.context_menu=self.create_menu()
        self.is_new=False
        self.caller=caller
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

    def xy_ticks_to_times(self):
        self.dtxy[0]=chtl.ticks_to_times(self.ts,self.xy[0])
        self.dtxy[1]=self.xy[1]
        return self.dtxy

    def xy_times_to_ticks(self):
        self.xy[0]=chtl.times_to_ticks(self.ts,self.dtxy[0])
        self.xy[1]=self.dtxy[1]
        return self.xy
        
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
        self.xy=self.plt.mapped_xy
        self.xy_ticks_to_times()
        self.setPos(self.xy)
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
                    self.xy=self.cursorOffset + self.mapToParent(ev.pos())
                    self.xy_ticks_to_times()

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

    def setState(self,state):
        self.xy=state
        self.setPos(*state)
    
    def saveState(self):
        return [self.xy[0],self.xy[1]]
    
    def set_dt(self,dt):
        self.dtxy=dt
        self.xy_times_to_ticks()
        self.setState(self.xy)

    def save_dt(self):
        self.xy_ticks_to_times()
        return self.dtxy

    def ts_change(self,ts):
        self.ts=ts
        self.xy_times_to_ticks()
        self.setPos(*self.xy)
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
        self.xy_ticks_to_times=lambda *args,**kwargs: None
        self.xy_times_to_ticks=lambda *args,**kwargs: None

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
    
    def set_dt(self,state):
        return self.setState(state)
    
    def save_dt(self):
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