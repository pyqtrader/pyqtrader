import PySide6
from PySide6 import QtWidgets,QtCore,QtGui
import math, time, datetime
import pyqtgraph as pg
from pyqtgraph import Point
from pyqtgraph.graphicsItems.TargetItem import TargetItem

import cfg
import overrides as ovrd, overrides
import timeseries as tmss, timeseries
import charttools as chtl,charttools
import uitools

#debugging section
from _debugger import _print,_printcallers,_exinfo,_ptime,_c,_p,_pc,_pp,_fts

class DrawProps:
    def INIT(self,mwindow,props=None,caller=None):
        self.is_persistent=True
        self.is_draw=True
        self.props=dict(width=1,color=None,style=cfg.D_STYLE)
        if props is not None:
            for key in props:
                if props[key] is not None:
                    self.props[key]=props[key]
        # self.unpack_props()
        self.mwindow=mwindow
        self.mprops=mwindow.props
        self.myref=self.__module__+'.'+type(self).__name__
        if self.myref in (mwp:=self.mwindow.props):
            self.props=dict(mwp[self.myref])
        self.caller=caller

    def get_props(self):
        return self.props

    def save_props(self):
       a=self.get_props()
       return a

    @property
    def width(self):
        return self.props['width']
    
    @width.setter
    def width(self,x):
        self.props['width']=x
    
    @property
    def color(self):
        return self.props['color']
    
    @color.setter
    def color(self,x):
        self.props['color']=x

    @property
    def style(self):
        return self.props['style']

    @style.setter
    def style(self,x):
        self.props['style']=x

    # def unpack_props(self): #to use instead of @property if the latter fails
    #     for key in self.props:
    #         setattr(self,key,self.props[key])
    
    def set_props(self,props):
        for key in props:
            self.props[key]=props[key]
        # self.unpack_props()
        pen=dict(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.setPen(**pen)
        if hasattr(self,'hoverPen'):
            self.hoverPen=pg.functions.mkPen(**pen)
        if self.is_persistent and self.caller!='open_subw':
            self.mwindow.props[self.myref]=self.get_props()
    
    def childobjects(self):
        a=[] if not hasattr(self,'children') else self.children()
        b=[] if not hasattr(self,'childItems') else self.childItems()
        return list(set(a).union(set(b)))

    def item_hide(self,persistence_modifier=None,selected=None): #hide instead of remove to retain for restoration with Ctrl-Z
        def dig(item):
            item.hide()
            if hasattr(item,'childobjects'):
                for im in item.childobjects():
                    dig(im) #recursion to ensure that all child items are processed
        if persistence_modifier is not None and type(persistence_modifier) is bool:
            self.is_persistent=persistence_modifier
        dig(self)
        if selected is not None:
            if hasattr(self,'set_selected'):
                self.set_selected(selected)
            elif hasattr(self,'setSelected'):
                self.setSelected(selected)

    def item_show(self,selected=None):
        def dig(item):
            item.show()
            if hasattr(item,'childobjects'):
                for im in item.childobjects():
                    dig(im) #recursion to ensure that all child items are processed
        dig(self)
        if selected is not None:
            if hasattr(self,'set_selected'):
                self.set_selected(selected)
            elif hasattr(self,'setSelected'):
                self.setSelected(selected)

    def item_replicate(self):
        newitem=self.__class__(self.plt)
        self.plt.addItem(newitem)
        if hasattr(newitem,'set_dt'):
            newitem.set_dt(self.save_dt())
        if hasattr(newitem,'set_props'):
            newitem.set_props(self.save_props())
        if hasattr(newitem,'set_selected'):
            newitem.set_selected(True)

class DrawItem(DrawProps): #ROI generic class
    sigHoverLeaveEvent=QtCore.Signal(object)
    def __init__(self,plt,dockplt=None,dialog=uitools.DrawPropDialog,clicks=2,
        props=None,caller=None):
        super().INIT(plt.mwindow,props=props,caller=caller)
        self.timeseries=plt.chartitem.timeseries
        self.plt=plt if dockplt is None else dockplt
        self.precision=self.plt.precision
        self.dialog=dialog
        self.hsz=cfg.HANDLE_SIZE
        try:
            self.context_menu=self.create_menu()
        except Exception:
            pass
        self.ray_on=False
        self.clicks=clicks
        self.click_count=1
        self.is_new=False #to inform derivative classes whether the item is new
        if self.color is None:
            self.color=self.plt.graphicscolor

    def addHandle(self, *args, **kwargs): #imported module override (handle size)
            self.handleSize = self.hsz
            self.handlePen=self.plt.foregroundcolor
            self.handleHoverPen=self.handlePen
            super(DrawItem,self).addHandle(*args, **kwargs)

    def initialisation(self):
        self.state=self.getState()
        self.xy=self.read_state()
        self.dtxy= chtl.zeroP(self.clicks if self.clicks is not None else 0)
        self.xy_ticks_to_times() # conversion from timeseries.ticks to timeseries.times
        self.change=False #user drag state monitoring
        super(DrawItem,self).setZValue(0)
        
        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.LeftButton | QtCore.Qt.MouseButton.RightButton)
        self.sigRegionChangeStarted.connect(self.change_state)
        self.sigRegionChangeFinished.connect(self.mouse_update)
        # uncomment to unsupress the handles, see overrides
        # self.sigHoverEvent.connect(lambda *args: self.hvr(hovered=True))
        # self.sigHoverLeaveEvent.connect(lambda *args: self.hvr(hovered=False))
        self.plt.subwindow.plt.sigTimeseriesChanged.connect(self.ts_change)

        if self.caller=='mouse_clicked':#fast way to setup the first drawing by mouse clicks
            self.plt.scene().sigMouseClicked.connect(self.setup_mouseclicks)
            self.plt.scene().sigMouseMoved.connect(self.setup_mousemoves)
            self.is_new=True
            self.plt.addItem(self)
        else: #to ensure exclusion of the setup routine when item already exists (fix trendline non-deletion bug)
            self.click_count=self.clicks
    
    def mouseClickEvent(self, ev):
        if ev.button()==QtCore.Qt.MouseButton.LeftButton:
            self.left_clicked(ev)
        elif ev.button()==QtCore.Qt.MouseButton.RightButton:
            self.right_clicked(ev)
        return super().mouseClickEvent(ev)
                 
    def xy_ticks_to_times(self):
        xy=self.xy
        try:
            self.dtxy=chtl.zeroP(len(xy)) #to ensure equal length of xy and dtxy lists
            for i in range(len(xy)):
                self.dtxy[i][0]=chtl.ticks_to_times(self.timeseries,xy[i][0])
                self.dtxy[i][1]=xy[i][1]
        except Exception:
            print ('Ticks-to-times conversion failed')
        return self.dtxy
    
    def xy_times_to_ticks(self):
        dtxy=self.dtxy
        try:
            self.xy=chtl.zeroP(len(dtxy)) #to ensure equal length of xy and dtxy lists
            for i in range(len(dtxy)):
                self.xy[i][0]=chtl.times_to_ticks(self.timeseries,dtxy[i][0])
                self.xy[i][1]=dtxy[i][1]
        except Exception as e:
            print ('Times-to-ticks conversion failed: ',e)
        return self.xy

    def redraw(self):
        self.xy_times_to_ticks()
        self.write_state()
        self.setState(self.state)
    
    def ts_change(self,ts):
        self.timeseries=ts
        self.redraw()
    
    def set_selected(self, s):
        self.translatable=s #translatable=movable
        self.setSelected(s)

    def mouse_update(self):
        self.state=self.getState()
        def lf():
            if self.change:
                self.xy=self.read_state()
                self.xy_ticks_to_times()
                self.change=False
        try: #for rois with points
            pos=self.state['pos']
            points=self.state['points']
            if pos!=Point(0,0): #convert pos to Point(0,0) to ensure compatibility with dialogs and coordinates
                points=[point+pos for point in points]
                pos=Point(0,0)
                self.state['pos']=pos
                self.state['points']=points
                self.setState(self.state)
                self.xy=self.read_state()
                self.xy_ticks_to_times()
            else:
                lf()
        except Exception:
            lf()
                
    def change_state(self):
        self.change=True

    def left_clicked(self,ev):
        self.set_selected(not self.translatable)
    
    def hoverEvent(self, ev): #imported module override
        if ev.isExit():
            self.sigHoverLeaveEvent.emit(self)
        return super(DrawItem,self).hoverEvent(ev)
    
    #uncomment to unsupress the handles, see overrides
    # def hvr(self, hovered=True):
    #     if hovered or (hovered==False and self.translatable==False):
    #         self.setSelected(hovered)
    
    def save_dt(self):
        return [list(a) for a in self.dtxy]

    def set_dt(self,dtxy):
        self.dtxy=dtxy
        self.xy_times_to_ticks()
        self.state=self.getState()
        self.write_state()
        self.setState(self.state)

    def create_menu(self,ray_on=False,description=None):
        context_menu=QtWidgets.QMenu()
        if description is not None:
            context_menu.addSection(description)
        self.prop_act=context_menu.addAction('Properties')
        self.pushdown_act=context_menu.addAction('Push down')
        self.liftup_act=context_menu.addAction('Lift up')
        context_menu.addSeparator()
        self.rem_act=context_menu.addAction('Remove')
        if ray_on==True:
            self.ray_on=True
            self.ray_submenu=QtWidgets.QMenu('Ray')
            context_menu.insertMenu(self.prop_act,self.ray_submenu)
            self.ray_right_act=self.ray_submenu.addAction(cfg.RAYDIR['r']) 
            self.ray_right_act.setCheckable(True)
            self.ray_left_act=self.ray_submenu.addAction(cfg.RAYDIR['l']) 
            self.ray_left_act.setCheckable(True)
            self.update_menu()
        return context_menu

    def right_clicked(self,ev,**kwargs):
        ev_pos=ev.screenPos()
        self.maction=self.context_menu.exec(QtCore.QPoint(ev_pos.x(),ev_pos.y()))
        if self.maction==self.rem_act:
            self.plt.remove_item(self)
            return
        elif self.maction==self.prop_act:
            self.dialog(self.plt,item=self,**kwargs)
        elif self.maction==self.pushdown_act:
            zv=self.zValue()
            self.setZValue(zv-1)
        elif self.maction==self.liftup_act:
            zv=self.zValue()
            self.setZValue(zv+1)
        if self.ray_on==True:
            def fray(rd):
                self.props['extension']=rd
                self.set_props(self.props)
                self.repaint_ray()
            if self.maction == self.ray_right_act:
                raydir=chtl.ray_mode(self.props['extension'],cfg.RAYDIR['r'])
                fray(raydir)
            elif self.maction == self.ray_left_act:
                raydir=chtl.ray_mode(self.props['extension'],cfg.RAYDIR['l'])
                fray(raydir)
            self.plt.vb.update()
            self.redraw()
    
    def update_menu(self):
        if self.props['extension']==cfg.RAYDIR['b']:
            self.ray_right_act.setChecked(True)
            self.ray_left_act.setChecked(True)
        elif self.props['extension']==cfg.RAYDIR['n']:
            self.ray_right_act.setChecked(False)
            self.ray_left_act.setChecked(False)
        elif self.props['extension']==cfg.RAYDIR['r']:
            self.ray_right_act.setChecked(True)
            self.ray_left_act.setChecked(False)
        elif self.props['extension']==cfg.RAYDIR['l']:
            self.ray_right_act.setChecked(False)
            self.ray_left_act.setChecked(True)
        else:
            self.ray_right_act.setChecked(False)
            self.ray_left_act.setChecked(False)
    
    def repaint_ray(self):
        pass


    # def read_state(self):
    #     pass

    # def write_state(self):
    #     pass

    def setup_mouseclicks(self,mouseClickEvent):
        if mouseClickEvent.button()==QtCore.Qt.MouseButton.LeftButton:
            xy=Point(self.plt.vb.mapSceneToView(mouseClickEvent.scenePos()))
            self.click_count+=1
            if self.clicks is None or self.click_count<self.clicks:
                self.xy.append(xy)
                self.write_state()
                self.setState(self.state)
            else:
                self.write_state()
                self.setState(self.state)
                self.xy_ticks_to_times()
                self.plt.scene().sigMouseClicked.disconnect(self.setup_mouseclicks)
                self.set_selected(True)

    def setup_mousemoves(self,mouseMoveEvent):
        xy=Point(self.plt.vb.mapSceneToView(mouseMoveEvent))
        if self.clicks is None or self.click_count<self.clicks:
            self.xy[-1]=xy
            self.write_state()
            self.setState(self.state)
        else:
            self.plt.scene().sigMouseMoved.disconnect(self.setup_mousemoves)

    def magnetize(self,hls=2):#hls is the number of handles to be magnetized: 2- both, 1 - only the first
                                #This is needed for channel sync 
        if self.translatable: # and self.click_count==self.clicks:
            props=self.plt.mwindow.props
            yes=props['magnet']
            mapper=lambda x: self.mapFromDevice(x)
            mp0=mapper(Point(0,0))
            if yes and mp0 is not None:
                values=list(reversed(self.timeseries.values))

                class mag: #magnetized obj(bar or ohlc point) 'structure'
                    def __init__(self,obj,dist) -> None:
                        self.obj=obj
                        self.dist=dist
               
                ax0=self.plt.getAxis('bottom').range[0]
                state=self.getState()
                pts=state['points']
                
                vect=mapper(Point(cfg.MAGNET_DISTANCE,cfg.MAGNET_DISTANCE))-mp0
                vect=Point(abs(vect.x()),abs(vect.y()))
                cnt=0
                while cnt<min(hls,len(pts)): #fix pitchfork initial setup
                    minx=mag(values[0],abs(values[0][0]-pts[cnt][0]))#initialize minimum x axis distance from the base point
                    for val in values: #identify magnetized bar
                        if val[0]>=ax0 or val[0]>=0:
                            a=abs(val[0]-pts[cnt][0])
                            if a<minx.dist:
                                minx.obj=val
                                minx.dist=a
                        else:
                            break        
                        
                    if minx.dist<vect.x():
                        magbar=minx.obj #magnetized bar
                        miny=mag(magbar[2],abs(magbar[2]-vect.y())) #initialize minimum y axis distance 
                        if miny.dist>0:
                            for price in magbar[2:]: #identify magnetized ohlc point
                                b=abs(price-pts[cnt][1])
                                if b<miny.dist:
                                    miny.obj=price
                                    miny.dist=b
                            if miny.dist<vect.y() and miny.dist>0:
                                state['points'][cnt]=Point(minx.obj[0],miny.obj)
                                self.setState(state)
                                self.xy=state['points']
                                self.xy_ticks_to_times()
                    cnt+=1
    
    def removal(self):
        self.plt.subwindow.plt.sigTimeseriesChanged.disconnect(self.ts_change)
        self.plt.removeItem(self)

class DTrendLineDialog(uitools.DrawPropDialog):
    initials=dict(uitools.DrawPropDialog.initials)
    levels=None
    def __init__(self,*args, tseries=None,dtxy=chtl.zero2P(),exec_on=True,**kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Trendline')
        if exec_on==True: #to isolate the class variable from subclasses
            self.setup_extension()
        self.tseries=tseries
        self.dtx,self.dtxs=[None,None],[None,None]
        self.dte=[None,None]
        self.dtx[0]=dtxy[0][0]
        self.dtxs[0] = datetime.datetime.fromtimestamp(self.dtx[0])
        self.dtx[1]= dtxy[1][0]
        self.dtxs[1] = datetime.datetime.fromtimestamp(self.dtx[1])
        self.yv0=dtxy[0][1]
        self.yv1=dtxy[1][1]
        
        label0=QtWidgets.QLabel('Datetime 1: ')
        self.dte[0]=QtWidgets.QDateTimeEdit()
        self.dte[0].setDateTime(self.dtxs[0])
        self.dte[0].setDisplayFormat('dd.MM.yyyy hh:mm')
        self.layout.addWidget(label0,self.order,0)
        self.layout.addWidget(self.dte[0],self.order,1)
        self.dte[0].dateTimeChanged.connect(lambda *args: self.update_dt(0))

        label1=QtWidgets.QLabel('Value 1: ')
        pbox0=QtWidgets.QDoubleSpinBox()
        pbox0.setDecimals(self.item.precision)
        pbox0.setSingleStep(pow(10,-self.item.precision))
        pbox0.setMaximum(self.yv0*100)
        pbox0.setValue(self.yv0)
        self.layout.addWidget(label1,self.order,3)
        self.layout.addWidget(pbox0,self.order,4)
        pbox0.valueChanged.connect(lambda *args: setattr(self,'yv0',pbox0.value()))
        self.order+=1

        label2=QtWidgets.QLabel('Datetime 2: ')
        self.dte[1]=QtWidgets.QDateTimeEdit()
        self.dte[1].setDateTime(self.dtxs[1])
        self.dte[1].setDisplayFormat('dd.MM.yyyy hh:mm')
        self.layout.addWidget(label2,self.order,0)
        self.layout.addWidget(self.dte[1],self.order,1)
        self.dte[1].dateTimeChanged.connect(lambda *args: self.update_dt(1))

        label3=QtWidgets.QLabel('Value 2: ')
        pbox1=QtWidgets.QDoubleSpinBox()
        pbox1.setDecimals(self.item.precision)
        pbox1.setSingleStep(pow(10,-self.item.precision))
        pbox1.setMaximum(self.yv1*100)
        pbox1.setValue(self.yv1)
        self.layout.addWidget(label3,self.order,3)
        self.layout.addWidget(pbox1,self.order,4)
        pbox1.valueChanged.connect(lambda *args: setattr(self,'yv1',pbox1.value()))
        self.order+=1
    
        if exec_on==True:
            self.embedded_db()
            self.exec()

    @property
    def dtxy(self):
        return [[self.dtx[0],self.yv0],[self.dtx[1],self.yv1]]

    def setup_extension(self):
        if 'extension' in self.item.props:
            self.state_dict['extension']=self.__class__.extension=self.item.props['extension']
        

    def update_dt(self,i):
        self.dtxs[i]=self.dte[i].dateTime()
        self.dtx[i]=self.dtxs[i].toSecsSinceEpoch()
    
    def update_item(self,**kwargs):
        self.item.set_dt(self.dtxy)
        return super().update_item(**kwargs)

class DrawTrendLine(DrawItem,pg.LineSegmentROI):
    def __init__(self,plt,coords=chtl.zero2P(),dialog=DTrendLineDialog, **kwargs):
        super().__init__(plt,dialog=dialog,**kwargs)
        super(DrawItem,self).__init__(coords)
        if 'extension' not in self.props:
            self.props['extension']=cfg.RAYDIR['r']
        self.initialisation()
        pen=dict(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.setPen(**pen)
        self.hoverPen=pg.functions.mkPen(**pen)
        pen['style']=self.style
        self.ray=InfiniteTrendLine(self.plt,self,extension=self.props['extension'],props=pen,persist=False)
        self.plt.addItem(self.ray)

        self.raying()

        self.sigRegionChanged.connect(self.line_move)
        self.plt.sigMouseOut.connect(self.magnetize)
        self.ray.sigDragged.connect(self.ray_move)

        self.context_menu=self.create_menu(ray_on=True,description='Trend Line')

    def read_state(self):
        return self.state['points']

    def write_state(self):
        self.state['points']=self.xy
    
    def set_props(self,props):
        super().set_props(props)
        if self.caller=='open_subw':
            self.repaint_ray()
        pen=dict(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.ray.setPen(**pen)
        self.ray.hoverPen=pg.functions.mkPen(**pen)
        self.update_menu()
                    
    def raying(self):
        xshift=self.state['pos'][0]
        yshift=self.state['pos'][1]
        x0=self.xy[0][0]+xshift
        y0=self.xy[0][1]+yshift
        x1=self.xy[1][0]+xshift
        y1=self.xy[1][1]+yshift
        ysign=1 if y1-y0>=0 else -1
        ang= 90*ysign if x1-x0==0 else math.degrees(math.atan((y1-y0)/(x1-x0)))
        self.ray.setPos([x0,y0])
        self.ray.setAngle(ang)
        self.ray.setPen(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])

    def line_move(self):
        self.state=self.getState()
        self.xy=self.state['points']
        if self.click_count<self.clicks: #to fix no-repaint on initialisation
            self.repaint_ray()
        else: #to reduce overhead in general use
            self.raying()
    
    def ray_move(self):
        self.state=self.getState()
        rxy=self.ray.getPos()
        lxy=self.state['points']
        dx,dy=rxy[0]-lxy[0][0],rxy[1]-lxy[0][1]
        lxy[0][0],lxy[0][1],lxy[1][0],lxy[1][1]=lxy[0][0]+dx,lxy[0][1]+dy,lxy[1][0]+dx,lxy[1][1]+dy
        self.state['points']=lxy
        self.state['pos']=[0,0]
        self.xy=self.state['points']
        self.xy_ticks_to_times()
        self.setState(self.state)

    def right_clicked(self,ev):#full override is simpler
        super().right_clicked(ev,tseries=self.timeseries,dtxy=self.dtxy)

    def repaint_ray(self): #workaround for the failure to repaint after update()
        self.plt.removeItem(self.ray)
        del self.ray
        self.ray=InfiniteTrendLine(self.plt,self,extension=self.props['extension'],persist=False)
        self.ray.sigDragged.connect(self.ray_move)#reconnect the signal after the removal
        self.plt.addItem(self.ray)
        self.raying()

    def left_clicked(self,ev):
        self.ray.setMovable(not self.translatable)
        super().left_clicked(ev)
    
    def setZValue(self, z):
        try:
            self.ray.setZValue(z-1)
        except Exception:
            pass
        return super().setZValue(z)

    def removal(self):
        self.plt.removeItem(self.ray)
        super().removal()

class DrawEllipse(DrawItem,pg.EllipseROI):
    def __init__(self,plt,coords=chtl.zero2P(),**kwargs):
        pos=coords[0]
        size=[coords[1][0]-coords[0][0],coords[1][1]-coords[0][1]]
        super().__init__(plt,dialog=uitools.DrawPropDialog,**kwargs)
        super(DrawItem,self).__init__(pos,size)
        self.initialisation()
        self.setPen(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])

    def read_state(self):
        xy=[]
        xy.append(self.state['pos'])
        xy.append(self.state['size'])
        return xy
    
    def write_state(self):
        self.state['pos']=self.xy[0]
        self.state['size']=[self.xy[1][0]-self.xy[0][0],self.xy[1][1]-self.xy[0][1]]
    
    def right_clicked(self, ev,**kwargs):
        return super().right_clicked(ev,exec_on=True,**kwargs)
    
    def mouse_update(self):#override over segment rois
        if self.change:
            self.state=self.getState()
            self.xy=self.read_state()
            self.xy[1]=self.xy[0]+self.xy[1]
            self.xy_ticks_to_times()
            self.change=False
    
    def save_props(self):
        a=super().save_props()
        a['angle']=self.getState()['angle']
        return a
    
    def set_props(self, props):
        try:
            angle=props.pop('angle')
            self.setAngle(angle)
        except Exception:
            pass
        return super().set_props(props)

class DrawRectangle(DrawItem,pg.RectROI):
    def __init__(self,plt,coords=chtl.zero2P(),**kwargs):
        pos=coords[0]
        size=[coords[1][0]-coords[0][0],coords[1][1]-coords[0][1]]
        super().__init__(plt,dialog=uitools.DrawPropDialog,**kwargs)
        super(DrawItem,self).__init__(pos,size,sideScalers=True)
        self.initialisation()
        self.setPen(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
    
    def read_state(self):
        xy=[]
        xy.append(self.state['pos'])
        xy.append(self.state['size'])
        return xy
    
    def write_state(self):
        self.state['pos']=self.xy[0]
        self.state['size']=[self.xy[1][0]-self.xy[0][0],self.xy[1][1]-self.xy[0][1]]
    
    def right_clicked(self, ev,**kwargs):
        return super().right_clicked(ev,exec_on=True,**kwargs)
    
    def mouse_update(self):#override over segment rois
        if self.change:
            self.state=self.getState()
            self.xy=self.read_state()
            self.xy[1]=self.xy[0]+self.xy[1]
            self.xy_ticks_to_times()
            self.change=False

class AltInfiniteLine(DrawProps,pg.InfiniteLine):
    def __init__(self,plt,*args,dockplt=None,dialog=uitools.DrawPropDialog,
        props=None,caller=None,**kwargs):
        super().INIT(plt.mwindow,props=props,caller=caller)
        super(DrawProps,self).__init__(*args,**kwargs)
        self.plt=plt if dockplt is None else dockplt
        self.color=self.plt.chartprops[cfg.foreground] if self.color is None else self.color
        pen=dict(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.setPen(**pen)
        self.hoverPen=pg.functions.mkPen(**pen)
        self.precision=self.plt.precision
        self.timeseries=plt.chartitem.timeseries
        self.dtx=0.0
        self.dialog=dialog
        self.extension=None if 'extension' not in self.props else self.props['extension']
        self.context_menu=self.create_menu()

        self.sigDragged.connect(self.mouse_dragged)

    def mouseClickEvent(self, ev):
        if ev.button()==QtCore.Qt.MouseButton.LeftButton:
            self.left_clicked(ev)
        elif ev.button()==QtCore.Qt.MouseButton.RightButton:
            self.right_clicked(ev)
        return super().mouseClickEvent(ev)

    def left_clicked(self,ev):
        self.set_selected(not self.movable)

    def set_selected(self,s):
        if s:
            self.setMovable(True)
            self.addMarker('^', position=0.0, size=10.0)
            self.addMarker('v', position=1.0, size=10.0)
        else:
            self.setMovable(False)
            self.clearMarkers()

    def mouse_dragged(self):
        try:
            self.mouse_update()
        except Exception:
            pass
    
    def save_dt(self):
        return self.dtx
    
    def set_dt(self,dtx):
        self.dtx=dtx
    
    def paint(self, p, *args):#override of the parent function
        if self.extension==cfg.RAYDIR['n']: 
            pass #no paint if neither direction
        else:
            if self.extension==cfg.RAYDIR['r']:
                rgt=self._endPoints[1]
                del self._endPoints
                self._endPoints=(0,rgt)
            elif self.extension==cfg.RAYDIR['l']:
                lft=self._endPoints[0]
                del self._endPoints
                self._endPoints=(lft,0)
            elif self.extension==cfg.RAYDIR['b'] or self.extension is None:
                pass
            else:
                uitools.simple_message_box(text='Unrecognized ray direction',
                    icon=QtWidgets.QMessageBox.Warning)
                #print(f'{self.extension} Unrecognized ray direction')
            super().paint(p, *args)
    
    def mouse_area(self,x):
        x0=self.getPos()[0]
        if self.extension==cfg.RAYDIR['n']:
            return False
        elif self.extension==cfg.RAYDIR['r']:
            return True if x>=x0 else False
        elif self.extension==cfg.RAYDIR['l']:
            return True if x<=x0 else False
        elif self.extension==cfg.RAYDIR['b']:
            return True
        else:
            return True
    
    def yvalue(self,x):
        x0,y0=self.getPos()
        return y0 if self.angle==90 else y0+(x-x0)*math.tan(math.radians(self.angle))
    
    def xvalue(self,y):
        x0,y0=self.getPos()
        return x0 if self.angle==0 else x0+(y-y0)/math.tan(math.radians(self.angle))

    #to monitor mouse hover distance/no longer used as the bug was fixed but retained just in case
    def in_vicinity(self,xy,dst=cfg.VICINITY_DISTANCE):
        pixy=self.mapToDevice(xy)
        p_x=self.mapToDevice(Point(self.xvalue(xy.y()),xy.y()))
        p_y=self.mapToDevice(Point(xy.x(),self.yvalue(xy.x())))
        dx=abs(pixy.x()-p_x.x())
        dy=abs(pixy.y()-p_y.y())
        res = True if dx<dst or dy<dst else False
        return res

    def create_menu(self,description=None):
        context_menu=QtWidgets.QMenu()
        if description is not None:
            context_menu.addSection(description)
        self.prop_act=context_menu.addAction('Properties')
        self.pushdown_act=context_menu.addAction('Push down')
        self.liftup_act=context_menu.addAction('Lift up')
        context_menu.addSeparator()
        self.rem_act=context_menu.addAction('Remove')
        return context_menu
    
    def right_clicked(self,ev,**kwargs):
        ev_pos=ev.screenPos()
        self.maction=self.context_menu.exec(QtCore.QPoint(ev_pos.x(),ev_pos.y()))
        if self.maction==self.rem_act:
            self.plt.remove_item(self)
        elif self.maction==self.prop_act:
            self.dialog(self.plt,item=self,**kwargs)
            # self.context_menu.close()
        elif self.maction==self.pushdown_act:
            zv=self.zValue()
            self.setZValue(zv-1)
        elif self.maction==self.liftup_act:
            zv=self.zValue()
            self.setZValue(zv+1)

    def magnetize(self): 
        if self.movable:
            props=self.plt.mwindow.props
            yes=props['magnet']
            mapper=lambda x: self.mapFromDevice(x)
            mp0=mapper(Point(0,0))
            if yes and mp0 is not None:
                values=list(reversed(self.timeseries.values))

                class mag: #magnetized obj(bar or ohlc point) 'structure'
                    def __init__(self,obj,dist) -> None:
                        self.obj=obj
                        self.dist=dist
               
                ax0=self.plt.getAxis('bottom').range[0]
                pts=self.getState()
                
                vect=mapper(Point(cfg.MAGNET_DISTANCE,cfg.MAGNET_DISTANCE))-mp0
                vect=Point(abs(vect.x()),abs(vect.y()))
                minx=mag(values[0],abs(values[0][0]-pts[0]))#initialize minimum x axis distance from the base point
                for val in values: #identify magnetized bar
                    if val[0]>=ax0 or val[0]>=0:
                        a=abs(val[0]-pts[0])
                        if a<minx.dist:
                            minx.obj=val
                            minx.dist=a
                    else:
                        break        
                    
                if minx.dist<vect.x():
                    magbar=minx.obj #magnetized bar
                    miny=mag(magbar[2],abs(magbar[2]-vect.y())) #initialize minimum y axis distance 
                    if miny.dist>0:
                        for price in magbar[2:]: #identify magnetized ohlc point
                            b=abs(price-pts[1])
                            if b<miny.dist:
                                miny.obj=price
                                miny.dist=b
                        if miny.dist<vect.y() and miny.dist>0:
                            xy=Point(minx.obj[0],miny.obj)
                            self.setState(xy)
                            return xy
        return None #if xy is not returned, return None

    def removal(self):
        self.plt.removeItem(self)

class InfiniteTrendLine(AltInfiniteLine): #Subclass tailored to DrawTrendLine as attachment of it
    def __init__(self,plt,parent_segment,*args,extension=cfg.RAYDIR['r'],persist=True,**kwargs) -> None:
        super().__init__(plt,*args,**kwargs)
        self.is_persistent=persist
        self.setParent(parent_segment)
        self.left_clicked=self.parent().left_clicked #def left-clicked function
        self.extension=extension
        pen=dict(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.hoverPen=pg.functions.mkPen(**pen)
        self.setZValue(self.parent().zValue()-1)

    def getState(self):
            pass

    def right_clicked(self,ev):
        return self.parent().right_clicked(ev)
    
class DrawVerLine(AltInfiniteLine):
    def __init__(self,plt,pos=[0,0],**kwargs):
        super().__init__(plt,pos,angle=90,dialog=DVLineDialog,**kwargs)
        self.state=self.getState()
        self.dtx =chtl.ticks_to_times(self.timeseries,self.state[0])
        self.context_menu=self.create_menu(description='Vertical Line')

        self.ay=self.plt.getAxis('right')
        self.textX = pg.TextItem(anchor=(0,1))
        self.textX.setParent(self)
        self.textX.setColor(self.plt.graphicscolor)
        self.refresh()
        self.plt.addItem(self.textX, ignoreBounds=True)

        self.plt.vb.sigStateChanged.connect(self.refresh)
        self.plt.subwindow.plt.sigTimeseriesChanged.connect(self.ts_change)
 
    def getState(self):
        return self.getPos()
    
    def setState(self,xy): 
        self.p=[0,0] #fix bug blocking redrawing, self.p is an pg.InfiniteLine variable
        self.setPos(xy)
        self.refresh()

    def saveState(self): #standard function override
        return self.getState()
    
    def mouse_update(self):
        self.dtx=chtl.ticks_to_times(self.timeseries,self.getPos()[0])
        self.refresh()

    def ts_change(self,ts):
        self.timeseries=ts
        self.redraw()

    def redraw(self):
        self.state[0]=chtl.times_to_ticks(self.timeseries,self.dtx)
        self.setState(self.state)
        self.refresh()
    
    def refresh(self):
        x=self.getPos()[0]
        dtx=chtl.ticks_to_times(self.timeseries,x)
        ts=self.timeseries
        tf=ts.timeframe
        dtx = datetime.datetime.fromtimestamp(dtx)
       
        self.setPos(x)
        y0=self.ay.range[0]    
        self.textX.setPos(x,y0)

        if tf>=cfg.PERIOD_D1:
            self.textX.setText(dtx.strftime("%d %b'%y"))
            self.textX.setFontSize(cfg.D_FONTSIZE)
        else:
            self.textX.setText(dtx.strftime("%d %b'%y %H:%M"))
            self.textX.setFontSize(cfg.D_FONTSIZE)
    
    def set_dt(self, dtx):
        super().set_dt(dtx)
        self.redraw()

    def removal (self):
        self.plt.removeItem(self.textX)
        # del self.textX
        super().removal()
    
    def right_clicked(self,ev):
        super().right_clicked(ev,tseries=self.timeseries,dtxval=self.dtx)

class DVLineDialog(uitools.DrawPropDialog):
    initials=dict(uitools.DrawPropDialog.initials)
    def __init__(self, *args, tseries=None,dtxval=0, exec_on=True,**kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Vertical Line')
        self.tseries=tseries
        self.dtx=dtxval
        self.dtxs = datetime.datetime.fromtimestamp(self.dtx)
        
        label=QtWidgets.QLabel('Datetime: ')
        self.vl=QtWidgets.QDateTimeEdit()
        self.vl.setDateTime(self.dtxs)
        self.vl.setDisplayFormat('dd.MM.yyyy hh:mm')
        self.layout.addWidget(label,self.order,0)
        self.layout.addWidget(self.vl,self.order,1)
        self.vl.dateTimeChanged.connect(self.update_dt)
        self.order+=1

        if exec_on==True:
            self.embedded_db()
            self.exec()

    def update_dt(self):
        self.dtxs=self.vl.dateTime()
        self.dtx=self.dtxs.toSecsSinceEpoch()
    
    def update_item(self,**kwargs):
        self.item.set_dt(self.dtx)
        self.item.setState([chtl.times_to_ticks(self.tseries,self.dtx),0])
        return super().update_item(**kwargs)

class DHLineDialog(DVLineDialog):
    initials=dict(DVLineDialog.initials)
    def __init__(self, *args, yval=0.0, **kwargs):
        super().__init__(*args, exec_on=False,**kwargs)
        self.setWindowTitle('Horizontal Line')
        self.state_dict['extension']=self.__class__.extension=self.item.extension
        self.yv=yval

        label=QtWidgets.QLabel('Value: ')
        pricebox=QtWidgets.QDoubleSpinBox()
        pricebox.setDecimals(self.item.precision)
        pricebox.setSingleStep(pow(10,-self.item.precision))
        pricebox.setMaximum(self.yv*100)
        pricebox.setValue(self.yv)
        self.layout.addWidget(label,self.order,0)
        self.layout.addWidget(pricebox,self.order,1)
        pricebox.valueChanged.connect(lambda *args: setattr(self,'yv',pricebox.value()))
        self.order+=1

        self.embedded_db()
        self.exec()

    def update_item(self,**kwargs):
        self.item.set_dt([self.dtx,self.yv])
        return super(DVLineDialog,self).update_item(**kwargs) #equivalent to AltInfiniteLine.update_item()

class DrawHorLine(AltInfiniteLine):
    def __init__(self,plt,pos=[0,0],dialog=DHLineDialog,**kwargs):
        super().__init__(plt,pos,angle=0,dialog=dialog,**kwargs)
        self.state=list(pos)
        self.dtx=chtl.ticks_to_times(self.timeseries,self.state[0])
        self.target=None

        self.ax=self.plt.getAxis('bottom')
        self.textY = pg.TextItem(anchor=(1,0.75))
        self.textY.setParent(self)
        self.textY.setColor(self.plt.graphicscolor)
        self.refresh()
        self.movable=True
        self.plt.addItem(self.textY, ignoreBounds=True)

        self.plt.vb.sigStateChanged.connect(self.refresh)
        self.plt.subwindow.plt.sigTimeseriesChanged.connect(self.ts_change)
        if self.caller!='open_subw': #fast way to magnetize on initiation
            self.plt.sigMouseOut.connect(self.init_magnetize) 

    @property
    def extension(self):
        if 'extension' in self.props:
            return self.props['extension']
        else:
            return None
    
    @extension.setter
    def extension(self,x):
        self.props['extension']=x

    def init_magnetize(self):
        self.mouse_update()
        self.plt.sigMouseOut.disconnect(self.init_magnetize)
    
    def getState(self): #standard function override to avoid bloat in DrawItem
        return self.getPos()
    
    def setState(self,xy): #standard function override to avoid bloat in AltInfiniteLine
        self.p=[0,0] #fix bug blocking redraw, self.p is an pg.InfiniteLine variable
        self.state=xy
        self.setPos(xy)
        self.refresh()

    def saveState(self): #standard function override
        return self.state

    def mouse_update(self):
        try:
            self.state=self.magnetize()
            if self.state is None:
                self.state=[self.plt.mapped_xy[0],self.getPos()[1]]
        except Exception:
            pass

        try:
            self.target.setPos(*self.state) #to avoid y-axis de-synch with the line
        except Exception:
            self.set_target()

        self.dtx=chtl.ticks_to_times(self.timeseries,self.state[0])
        self.refresh()

    def ts_change(self,ts):
        self.timeseries=ts
        self.redraw()

    def redraw(self): #no need to do transformations on price axis
        self.ax=self.plt.getAxis('bottom') #update axis on timeframe change
        self.state[0]=chtl.times_to_ticks(self.timeseries,self.dtx)
        self.setState(self.state)
        self.refresh()

    def refresh(self):
        if self.target is not None:
            self.target.setPos(*self.state)
        else:
            self.set_target()
        y=self.getPos()[1]
        x1=self.ax.range[1]
        self.textY.setPos(x1,y)
        self.textY.setText("{:.{pr}f}".format(y,pr=self.precision))
        self.textY.setFontSize(cfg.D_FONTSIZE)  
    
    def set_target(self):
        clr=self.color
        self.target=TargetItem(movable=False,symbol='o',size=3,pen=clr,hoverPen=clr)
        self.target.setParent(self)
        self.target.setPos(*self.state)
        self.plt.addItem(self.target, ignoreBounds=True)
    
    def save_dt(self):
        pos=self.getPos()
        return [self.dtx,pos[1]]
    
    def set_dt(self, dtxy):
        self.dtx=dtxy[0]
        self.state[1]=dtxy[1]
        self.redraw()
    
    def create_menu(self):
        context_menu=super().create_menu(description='Horizontal Line')
        self.extension=cfg.RAYDIR['b'] if self.extension is None else self.extension
        self.ray_act=QtGui.QAction('Ray')
        self.ray_act.setCheckable(True)
        context_menu.insertAction(self.prop_act,self.ray_act)
        return context_menu
    
    def left_clicked(self, ev):
        evp=self.mapToView(ev.pos())
        if self.mouse_area(evp.x()):
            return super().left_clicked(ev)

    def right_clicked(self, ev,**kwargs):
        self.ray_act.setChecked(True if self.extension==cfg.RAYDIR['r'] else False)
        super().right_clicked(ev,tseries=self.timeseries,dtxval=self.dtx,
            yval=self.state[1],**kwargs)
        if self.maction == self.ray_act:
            if self.extension!=cfg.RAYDIR['r']:
                self.extension=cfg.RAYDIR['r']
                self.set_props(self.props)
            else:
                self.extension=cfg.RAYDIR['b']
                self.set_props(self.props)
        self.plt.vb.update()
        self.redraw()
    
    def get_props(self):
        a=super().get_props()
        a['extension']=self.extension
        return a
    
    def set_props(self,props):
        super().set_props(props)
        self.extension=props['extension']

    def removal(self):
        self.plt.removeItem(self.textY)
        self.plt.removeItem(self.target)
        super().removal()

class AltPolyLine(pg.PolyLineROI): #abstract class to ensure mouse interactions via segments 
    def __init__(self,coords=chtl.zero2P()):
        super().__init__(coords)
        self.selected=True
    
    def addSegment(self, h1, h2, index=None):
        super().addSegment(h1, h2, index=index)
        self.segments[-1].setAcceptedMouseButtons(QtCore.Qt.MouseButton.LeftButton | QtCore.Qt.MouseButton.RightButton)
        self.segments[-1].is_draw=True

    def segmentClicked(self, segment, ev=None, pos=None):
        if ev.button()==QtCore.Qt.MouseButton.LeftButton:
            self.left_clicked(ev)
        elif ev.button()==QtCore.Qt.MouseButton.RightButton:
            self.right_clicked(ev)

    def setSelected(self, s):
        self.selected=s
        return super().setSelected(s)

    def hoverEvent(self, ev):
        pass

    def mouseClickEvent(self, ev):
        pass

    def left_clicked(self,ev):
        self.translatable=not self.translatable
        self.setSelected(self.translatable)

    def right_clicked(self,ev):
        pass

    def read_state(self):
        return self.state['points']

    def write_state(self):
        self.state['points']=self.xy

class DrawPolyLine(DrawItem,AltPolyLine):
    def __init__(self,plt,coords=chtl.zero2P(),clicks=None,**kwargs):
        dlg=lambda *args,**kwargs: uitools.DrawPropDialog(*args,exec_on=True,**kwargs)
        super().__init__(plt,dialog=dlg,clicks=clicks,**kwargs)
        super(DrawItem,self).__init__(coords)
        self.initialisation()
        self.setPen(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.clicks=clicks
        self.is_draw=False #to exclude the body of the roi from valid selectable areas and leave only the segments as such areas
        self.context_menu=self.create_menu(description='Polyline')

        if self.is_new:
            self.plt.scene().sigMouseClicked.connect(self.completion)
    
    def completion(self,ev):
        if ev.button()==QtCore.Qt.MouseButton.RightButton:
            self.write_state()
            self.setState(self.state)
            self.xy_ticks_to_times()
            self.plt.scene().sigMouseClicked.disconnect(self.setup_mouseclicks)
            self.plt.scene().sigMouseMoved.disconnect(self.setup_mousemoves)
            self.plt.scene().sigMouseClicked.disconnect(self.completion)
            self.translatable=True
            self.setSelected(True)

    def left_clicked(self, ev):
        return super(DrawItem,self).left_clicked(ev)
    
    def right_clicked(self,ev):#full override is simpler
        super().right_clicked(ev)
    
    def ts_change(self, ts):
        super().ts_change(ts)
        self.setSelected(self.selected)

class DrawArrow(DrawItem,pg.LineSegmentROI):
    def __init__(self,plt,coords=chtl.zero2P(),dialog=uitools.DrawPropDialog, **kwargs):
        super().__init__(plt,dialog=dialog,**kwargs)
        super(DrawItem,self).__init__(coords)
        self.initialisation()
        self.setPen(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.arrow=pg.ArrowItem(angle=self.ang, tipAngle=30, baseAngle=-30, headLen=10, 
            tailLen=None, brush=self.arcolor, pen={'width':self.width,'color':self.arcolor})
        self.arrow.setPos(self.xy[1])
        self.context_menu=self.create_menu(description='Arrow')
        self.plt.addItem(self.arrow)

        self.sigRegionChanged.connect(self.arrow_refresh)
        self.plt.vb.sigStateChanged.connect(self.arrow_refresh)
        self.plt.vb.sigTransformChanged.connect(self.arrow_refresh)

    
    def read_state(self):
        return self.state['points']

    def write_state(self):
        self.state['points']=self.xy

    @property
    def ang(self):
        ci=self.plt.subwindow.plt.chartitem
        xy=self.getState()['points']
        xy0=ci.mapToDevice(xy[0])
        xy1=ci.mapToDevice(xy[1])
        dxy=xy1-xy0
        a=math.degrees(math.atan2(dxy.y(),dxy.x()))-180
        return a

    @property
    def arcolor(self):
        return self.color if self.color is not None else '#ffffff'

    def arrow_refresh(self):
        state=self.getState()
        pos=state['points'][1]+state['pos']
        self.arrow.setPos(pos)
        self.arrow.setStyle(angle=self.ang)
    
    def right_clicked(self, ev,**kwargs):
        return super().right_clicked(ev,exec_on=True,**kwargs)
    
    def set_props(self, props):
        super().set_props(props)
        self.arrow.setStyle(brush=self.arcolor,pen={'width':self.width,'color':self.arcolor})
    
    def hide(self): #implement undo functionality
        self.arrow.hide()
        super().hide()

    def removal(self):
        self.sigRegionChanged.disconnect(self.arrow_refresh)
        self.plt.vb.sigStateChanged.disconnect(self.arrow_refresh)
        self.plt.vb.sigTransformChanged.disconnect(self.arrow_refresh)
        self.plt.removeItem(self.arrow)
        del self.arrow
        return super().removal()

class DrawPolyArrow(DrawPolyLine):
    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
    
        self.arrow=pg.ArrowItem(angle=self.ang, tipAngle=30, baseAngle=-30, headLen=10, 
                tailLen=None, brush=self.arcolor, pen={'width':self.width,'color':self.arcolor})
        self.arrow.setPos(self.xy[1])
        self.context_menu=self.create_menu(description='Polyarrow')
        self.plt.addItem(self.arrow)

        self.sigRegionChanged.connect(self.arrow_refresh)
        self.plt.vb.sigStateChanged.connect(self.arrow_refresh)
        self.plt.vb.sigTransformChanged.connect(self.arrow_refresh)
    
    @property
    def arcolor(self):
        return self.color if self.color is not None else '#ffffff'
    
    @property
    def ang(self):
        ci=self.plt.subwindow.plt.chartitem
        xy=self.getState()['points']
        xy0=ci.mapToDevice(xy[-2])
        xy1=ci.mapToDevice(xy[-1])
        dxy=xy1-xy0
        a=math.degrees(math.atan2(dxy.y(),dxy.x()))-180
        return a
    
    def arrow_refresh(self):
        try:
            state=self.getState()
            pos=state['points'][-1]+state['pos']
            self.arrow.setPos(pos)
            self.arrow.setStyle(angle=self.ang)
        except Exception:
            pass
    
    def set_props(self, props):
        super().set_props(props)
        self.arrow.setStyle(brush=self.arcolor,pen={'width':self.width,'color':self.arcolor})
    
    def hide(self): #implement undo functionality
        self.arrow.hide()
        super().hide()

    def removal(self):
        self.sigRegionChanged.disconnect(self.arrow_refresh)
        self.plt.vb.sigStateChanged.disconnect(self.arrow_refresh)
        self.plt.vb.sigTransformChanged.disconnect(self.arrow_refresh)
        self.plt.removeItem(self.arrow)
        del self.arrow
        return super().removal()

class _Fiboline(pg.LineSegmentROI):
    def __init__(self, *args,parent_line=None,**kwargs):
        super().__init__(*args, positions=chtl.zero2P(),movable=False,rotatable=False,
            resizable=False,**kwargs)
        self.setParent(parent_line)
        self.plt=self.parent().plt
        self.setSelected(False)
        self.is_persistent=False
        self.props=None
        self.label=None
        for hd in self.getHandles():
            hd.disconnectROI(self)
        #Disconnect from mouse interactions
        self.mouseDragHandler=None
        self.mouseClickEvent=lambda *args: None
        self.mouseDragEvent=lambda *args: None
        self.hoverEvent=lambda *args: None

        self.parent().sigRemoval.connect(self.removal)
        self.parent().sigRayStatusUpdate.connect(self.set_level)
        self.plt.vb.sigStateChanged.connect(self.refresh)        
    
    def set_level(self):
        ext=self.parent().props['extension']
        ax=self.plt.getAxis('bottom')

        parent_state=self.parent().getState()
        ppos=parent_state['pos']
        ppoints=parent_state['points']
        if isinstance(self.parent(), DrawFibo):
            pts=[ppoints[0]+ppos,ppoints[1]+ppos]
            dx=abs(pts[1].x()-pts[0].x())
            xpos=min(pts[0].x(),pts[1].x())
            dy=pts[0].y()-pts[1].y()
            ypos=pts[1].y()
        else:
            pts=[ppoints[0]+ppos,ppoints[1]+ppos,ppoints[2]+ppos]
            dx=abs(pts[2].x()-pts[1].x())
            xpos=min(pts[1].x(),pts[2].x())
            dy=pts[1].y()-pts[0].y()
            ypos=pts[2].y()

        x0=xpos-dx/2 if ext==cfg.RAYDIR['r'] or ext==cfg.RAYDIR['n'] else ax.range[0] 
        x1=xpos+3*dx if ext==cfg.RAYDIR['l'] or ext==cfg.RAYDIR['n'] else ax.range[1]
        y0=ypos+dy*self.props['value']/100
        y1=y0

        self.state=self.getState()
        self.state['points']=[pg.Point(x0,y0),pg.Point(x1,y1)]
        self.setState(self.state)
       
        if self.label is None:
            self.label=pg.TextItem(text=self.props['desc'],color=self.props['color'],anchor=(1,0.75))
            self.label.setParent(self.parent())
            self.label.setPos(max(x0,min(x1,ax.range[1])),y1)
            self.plt.addItem(self.label)
        elif self.props['desc']=='':
            self.plt.removeItem(self.label)
            self.label=None
        else:
            self.label.setText(self.props['desc'])
            self.label.setColor(self.props['color'])
            self.label.setPos(max(x0,min(x1,ax.range[1])),y1)
    
    def set_props(self, props):
        self.props=props
        self.set_level()
        self.setPen(width=props['width'],color=props['color'],style=cfg.LINESTYLES[props['style']])
    
    def refresh(self):
        ext=self.parent().props['extension']
        ax=self.plt.getAxis('bottom')

        state=self.getState()
        x0=state['points'][0][0]
        x1=state['points'][1][0]

        if ext==cfg.RAYDIR['l']:
            x0=ax.range[0]
            state['points'][0][0]=x0
            self.setState(state)
        elif ext==cfg.RAYDIR['r']:
            x1=ax.range[1]
            state['points'][1][0]=x1
            self.setState(state)
        elif ext==cfg.RAYDIR['b']:
            x0=ax.range[0]
            x1=ax.range[1]
            state['points'][0][0]=x0
            state['points'][1][0]=x1
            self.setState(state)
        
        if self.label is not None:
            y1=state['points'][1][1]
            self.label.setPos(max(x0,min(x1,ax.range[1])),y1)
    
    def removal(self):
        self.parent().sigRayStatusUpdate.disconnect(self.set_level)
        self.parent().sigRemoval.disconnect(self.removal)
        self.plt.vb.sigStateChanged.disconnect(self.refresh) 
        self.plt.removeItem(self)
        self.plt.removeItem(self.label)

class FiboDialog(DTrendLineDialog):
    initials={'width': 1,'color': '#ff0000', 'style': cfg.DOTLINE}
    def __init__(self,*args,**kwargs):
        super().__init__(*args,exec_on=False,**kwargs)
        self.__class__.initials['color']='red' #override
        self.setup_extension()

class FiboTabsDialog(uitools.TabsDialog):
    level_props=dict(uitools.TabsDialog.level_props)
    def __init__(self,plt,item=None,**kwargs):
        level_props=dict(width=cfg.FIBOWIDTH,color=cfg.FIBOCOLOR,style=cfg.FIBOSTYLE)
        #set default color of levels at the foreground color
        level_props['color']=plt.graphicscolor
        super().__init__(FiboDialog,plt,wname='Fibonacci retracements',item=item,
            level_props=level_props,**kwargs)

def fibo_factory(base=pg.LineSegmentROI,dialog=FiboTabsDialog,clicks=2,
        preset_levels=(0.0,38.2,50.0,61.8,100.0)):
    class _Fibo(DrawItem,base):
        sigRemoval=QtCore.Signal()
        sigRayStatusUpdate=QtCore.Signal()
        sigTimeseriesChanged=QtCore.Signal(object)

        def __init__(self,plt,coords=chtl.zero2P(),**kwargs):
            super().__init__(plt,dialog=dialog,props=dict(width=cfg.FIBOLINEWIDTH,
                color=cfg.FIBOLINECOLOR,style=cfg.FIBOSTYLE),clicks=clicks,**kwargs)
            super(DrawItem,self).__init__(coords)
            if 'extension' not in self.props:
                self.props['extension']=cfg.RAYDIR['n']
            self.initialisation()
            pen=dict(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
            self.setPen(**pen)
            self.hoverPen=pg.functions.mkPen(**pen)#remove hover
            level_props=dict(width=cfg.FIBOWIDTH,color=cfg.FIBOCOLOR,style=cfg.FIBOSTYLE)
            self.props['levels']=[]
            for lvl in preset_levels:
                self.props['levels'].append(dict(show=True,value=lvl,desc=str(lvl),**level_props))
            #set metaprops in newly created (not saved) object
            if self.is_new and self.myref in self.mprops:
                self.props=dict(self.mprops[self.myref])
            #set default levels at the foreground color
            metalevels=self.mprops[self.myref]['levels'] if self.myref in self.mprops and 'levels' in self.mprops[self.myref] else None
            if metalevels is None:
                for lvl in self.props['levels']:
                    lvl['color']=self.plt.graphicscolor
            self.ray=self
            self.level_items=[]
            self.set_levels()
            
            self.sigRegionChanged.connect(self.set_levels)    
            self.context_menu=self.create_menu(ray_on=True)

            self.plt.sigMouseOut.connect(self.magnetize)

        def set_levels(self):
            #To avoid full levels deletion and restatement, calc and process only the difference
            
            dcl=[m for m in self.props['levels'] if m['show']==True] #show==True dict slice
            diff=len(dcl)-len(self.level_items)

            if diff>0:
                while diff!=0:
                    newitem=_Fiboline(parent_line=self)
                    self.level_items.append(newitem)
                    self.plt.addItem(newitem)
                    diff-=1
            else:
                while diff!=0:
                    itm=self.level_items.pop()
                    itm.removal()
                    diff+=1
            
            for i,item in enumerate(self.level_items):
                lvl=dcl[i]
                if lvl['show']:
                    item.set_props(lvl) 
        
        def repaint_ray(self):
            self.sigRayStatusUpdate.emit()

        def ts_change(self, ts):
            super().ts_change(ts)
            self.set_levels()

        def read_state(self):
            return self.state['points']

        def write_state(self):
            self.state['points']=self.xy
        
        def set_props(self,props):
            super().set_props(props)
            self.update_menu()
            self.set_levels()
        
        def right_clicked(self,ev):
            super().right_clicked(ev,tseries=self.timeseries,dtxy=self.dtxy)

        def removal(self):
            self.sigRemoval.emit()
            self.sigRegionChanged.disconnect(self.set_levels)
            self.plt.sigMouseOut.disconnect(self.magnetize)   
            self.plt.removeItem(self)
    return _Fibo

_DrawFibo=fibo_factory()

class DrawFibo(_DrawFibo):
    def __init__(self, plt, coords=chtl.zero2P(), **kwargs):
        super().__init__(plt, coords, **kwargs)
        self.context_menu=self.create_menu(description='Fibo',ray_on=True)

class FiboExtDialog(DTrendLineDialog):
    initials={'width': 1,'color': '#ff0000', 'style': cfg.DOTLINE}
    def __init__(self,*args,exec_on=False,dtxy=chtl.zero2P(),wname=None,**kwargs):
        super().__init__(*args,exec_on=False,dtxy=dtxy,**kwargs)
        self.__class__.initials['color']='red' #override
        self.setup_extension()
        self.dtx.append(None)
        self.dtxs.append(None)
        self.dte.append(None)
        self.dtx[2]=dtxy[2][0]
        self.dtxs[2] = datetime.datetime.fromtimestamp(self.dtx[2])
        self.yv2=dtxy[2][1]

        label0=QtWidgets.QLabel('Datetime 3: ')
        self.dte[2]=QtWidgets.QDateTimeEdit()
        self.dte[2].setDateTime(self.dtxs[2])
        self.dte[2].setDisplayFormat('dd.MM.yyyy hh:mm')
        self.layout.addWidget(label0,self.order,0)
        self.layout.addWidget(self.dte[2],self.order,1)
        self.dte[2].dateTimeChanged.connect(lambda *args: self.update_dt(2))

        label1=QtWidgets.QLabel('Value 3: ')
        pbox=QtWidgets.QDoubleSpinBox()
        pbox.setDecimals(self.item.precision)
        pbox.setSingleStep(pow(10,-self.item.precision))
        pbox.setMaximum(self.yv2*100)
        pbox.setValue(self.yv2)
        self.layout.addWidget(label1,self.order,3)
        self.layout.addWidget(pbox,self.order,4)
        pbox.valueChanged.connect(lambda *args: setattr(self,'yv2',pbox.value()))
        self.order+=1

        if exec_on:
            self.setWindowTitle(wname)
            self.embedded_db()
            self.exec()

    @property
    def dtxy(self):
        return [[self.dtx[0],self.yv0],[self.dtx[1],self.yv1],[self.dtx[2],self.yv2]]

class FiboExtTabsDialog(uitools.TabsDialog):
    levels_props=dict(uitools.TabsDialog.level_props)
    def __init__(self,plt,item=None,**kwargs):
        level_props=dict(width=cfg.FIBOWIDTH,color=cfg.FIBOCOLOR,style=cfg.FIBOSTYLE)
        #set default color of levels at the foreground color
        level_props['color']=plt.graphicscolor
        super().__init__(FiboExtDialog,plt,wname='Fibonacci extensions',item=item,
            level_props=level_props,**kwargs)

_DrawFiboExt=fibo_factory(base=AltPolyLine,dialog=FiboExtTabsDialog,clicks=3,
        preset_levels=(61.8,100.0,161.8))

class DrawFiboExt(_DrawFiboExt):
    def __init__(self, plt, coords=chtl.zero2P(), **kwargs):
        super().__init__(plt, coords, **kwargs)
        self.context_menu=self.create_menu(description='Fibo Extension',ray_on=True)
    
    def magnetize(self, hls=3):
        return super().magnetize(hls)

    def set_levels(self):
        if len(self.getState()['points'])==self.clicks: #to ensure the second segment spawn before the fibolines
                                                #and workaround pg bug
            return super().set_levels()
    
    def ts_change(self, ts):
        DrawItem.ts_change(self,ts)
        self.setSelected(self.selected)
        self.set_levels()

    def left_clicked(self, ev):
        return AltPolyLine.left_clicked(self,ev)

class _ChannelBaseline(DrawTrendLine):
    def __init__(self,*args,parent_line=None,**kwargs):
        super().__init__(*args, **kwargs)
        self.is_persistent=False
        handles=self.getHandles()
        for i,hd in enumerate(handles):
            hd.mouseDragEvent=self.mouseDragEvent
            hd.disconnectROI(self)
            if i==1:
                hPen=QtCore.Qt.NoPen
                hd.pen=hPen
                hd.currentPen=hPen
                hd.hoverPen=hPen

        self.setParent(parent_line)
        props=self.parent().get_props()
        self.set_props(props)
        self.ray_sync()

        if self.parent().is_new:
            self._x,self._y=None,None
            self.plt.scene().sigMouseMoved.connect(self.setup_baseline)
        else:
            self.translatable=False

        # turn off self.change to fix datetime updating on the item's position changes
        self.change=True
        self.sigRegionChangeStarted.disconnect(self.change_state)
        self.change_state=lambda *args: None

        # override ts change
        self.plt.subwindow.plt.sigTimeseriesChanged.disconnect(self.ts_change)
        self.parent().sigTimeseriesChanged.connect(self.ts_change)
        
        self.parent().sigDeltasUpdated.connect(self.sync_with_parent)
        self.parent().sigRemoval.connect(self.removal)
        self.parent().sigPropsChanged.connect(self.set_props)
        self.parent().sigRayStatusUpdate.connect(self.ray_sync)

    def setup_baseline(self,ev):
        xy=self.plt.vb.mapSceneToView(ev)
        x=xy.x()
        y=xy.y()
        if self._x is None and self._y is None:
            self._x=x
            self._y=y
            #move the anchor to the segment's end point
            self.translate(self.parent().relative_pos)
            self.plt.scene().sigMouseClicked.connect(self.finish_baseline_setup)
        else:
            dx=x-self._x
            dy=y-self._y
            self.translate(dx,dy)
            self._x=x
            self._y=y
    
    def finish_baseline_setup(self):
        self.plt.scene().sigMouseMoved.disconnect(self.setup_baseline)
        self.plt.scene().sigMouseClicked.disconnect(self.finish_baseline_setup)
        del self._x
        del self._y

    def sync_with_parent(self,deltas):
        self.state['pos']=Point(0.0,0.0)
        #anchor point stationary, only the second point is moving when rotating the channel:
        self.state['points'][0]+=deltas['pos']
        self.state['points'][1]+=-deltas['points'][0]+deltas['points'][1]+deltas['pos']
        self.setState(self.state)
        self.xy=self.state['points']
        self.xy_ticks_to_times()
    
    def set_props(self,props):
        super().set_props(props)
        try:
            self.dtxy[0]=props['anchor_dt']
            self.xy_times_to_ticks()
            state=self.getState()
            self.xy[1]=self.xy[0]+self.parent().relative_pos
            state['points']=self.xy
            self.setState(state)
            #restore hotfix to avoid reset of self.dtxy[0] on self.setState() above after restore
            if not self.parent().is_new:
                self.dtxy[0]=props['anchor_dt']
        except Exception:
            pass
    
    def ts_change(self, ts, relpos):
        self.timeseries=ts
        self.xy_times_to_ticks()
        state=self.getState()
        state['points'][0]=self.xy[0]
        state['points'][1]=self.xy[0]+relpos
        self.setState(state)
        
    def right_clicked(self, ev):
        return self.parent().right_clicked(ev)

    def left_clicked(self,ev):
        super().left_clicked(ev)
        try:
            self.parent().set_selected(self.translatable)
        except Exception:
            pass
    
    def ray_sync(self):
        self.props['extension']=self.parent().props['extension']
        self.repaint_ray()
    
    def hoverEvent(self, ev):
        if ev.isExit() and self.translatable==False:#fix post-restore non-disappearance bug
            for hd in self.getHandles():
                hd.hide()
        super().hoverEvent(ev)
    
    def magnetize(self):
        super().magnetize(hls=1)#magnetize only the first handle
        state=self.getState()
        state['points'][1]=state['points'][0]+self.parent().relative_pos
        self.setState(state)

    def removal(self):
        self.plt.removeItem(self)
        self.plt.removeItem(self.ray)

class _ChannelParallel(DrawTrendLine):
    def __init__(self, pvalue, *args,parent_line=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.pvalue=pvalue
        self.setSelected(False)
        self.translatable=False
        self.is_persistent=False
        for hd in self.getHandles():
            hd.disconnectROI(self)
        self.setParent(parent_line)
        #Disconnect from mouse interactions
        self.mouseDragHandler=None
        self.mouseClickEvent=lambda *args: None
        self.mouseDragEvent=lambda *args: None
        self.hoverEvent=lambda *args: None
        self.ray.mouseClickEvent=lambda *args: None
        self.ray.mouseDragEvent=lambda *args: None
        self.ray.hoverEvent=lambda *args: None
        self.left_clicked=lambda *args: None
        self.right_clicked=lambda *args: None

        self.set_parallel()
        self.ray_sync()

        self.plt.subwindow.plt.sigTimeseriesChanged.disconnect(self.ts_change)
        self.parent().sigRemoval.connect(self.removal)
        self.parent().sigRayStatusUpdate.connect(self.ray_sync)
        self.parent().sigPropsChanged.connect(self.ray_sync) #required as 'extension' prop is not a part of the 'level_props' list in LeveLRow class

        self.parent().sigRegionChanged.connect(self.set_parallel)
        self.parent().sigRegionChangeFinished.connect(self.set_parallel)
        self.parent().baseline.sigRegionChanged.connect(self.set_parallel)
        self.parent().baseline.sigRegionChangeFinished.connect(self.set_parallel)

    def set_parallel(self):
        parent_state=self.parent().getState()
        ppos=parent_state['pos']
        ppoints=parent_state['points']
        parent_points=[ppoints[0]+ppos,ppoints[1]+ppos]
        baseline_state=self.parent().baseline.getState()
        bpos=baseline_state['pos']
        bpoints=baseline_state['points']
        baseline_points=[bpoints[0]+bpos,bpoints[1]+bpos]
        points=[]
        points.append(parent_points[0]+(self.pvalue/100)*(baseline_points[0]-parent_points[0]))
        points.append(parent_points[1]+(self.pvalue/100)*(baseline_points[1]-parent_points[1]))
        self.state=self.getState()
        self.state['points']=points
        self.setState(self.state)
    
    def ray_sync(self):
        self.props['extension']=self.parent().props['extension']
        self.repaint_ray()
    
    def set_props(self, props):
        self.pvalue=props['value']
        self.set_parallel()
        super().set_props(props)
    
    def removal(self):
        self.parent().sigRemoval.disconnect(self.removal)
        self.parent().sigRayStatusUpdate.disconnect(self.ray_sync)
        self.parent().sigPropsChanged.disconnect(self.ray_sync) #required as 'extension' prop is not a part of the 'level_props' list in LeveLRow class

        self.parent().sigRegionChanged.disconnect(self.set_parallel)
        self.parent().sigRegionChangeFinished.disconnect(self.set_parallel)
        self.parent().baseline.sigRegionChanged.disconnect(self.set_parallel)
        self.parent().baseline.sigRegionChangeFinished.disconnect(self.set_parallel)
        
        self.plt.removeItem(self.ray)
        self.plt.removeItem(self)

class DChannelDialog(DTrendLineDialog):
    initials=dict(DTrendLineDialog.initials)
    initials['anchor_dt']=anchor_dt=None
    def __init__(self, *args, tseries=None,exec_on=False, anchor=[0,0], **kwargs):
        super().__init__(*args, tseries=tseries,exec_on=False, **kwargs)
        self.state_dict['anchor_dt']=self.__class__.anchor_dt
        self.setup_extension()
        self.dtx.append(None)
        self.dtxs.append(None)
        self.dte.append(None)
        self.dtx[2]=anchor[0]
        self.dtxs[2] = datetime.datetime.fromtimestamp(self.dtx[2])
        self.yv2=anchor[1]

        label0=QtWidgets.QLabel('Datetime 3: ')
        self.dte[2]=QtWidgets.QDateTimeEdit()
        self.dte[2].setDateTime(self.dtxs[2])
        self.dte[2].setDisplayFormat('dd.MM.yyyy hh:mm')
        self.layout.addWidget(label0,self.order,0)
        self.layout.addWidget(self.dte[2],self.order,1)
        self.dte[2].dateTimeChanged.connect(lambda *args: self.update_dt(2))

        label1=QtWidgets.QLabel('Value 3: ')
        pbox=QtWidgets.QDoubleSpinBox()
        pbox.setDecimals(self.item.precision)
        pbox.setSingleStep(pow(10,-self.item.precision))
        pbox.setMaximum(self.yv2*100)
        pbox.setValue(self.yv2)
        self.layout.addWidget(label1,self.order,3)
        self.layout.addWidget(pbox,self.order,4)
        pbox.valueChanged.connect(lambda *args: setattr(self,'yv2',pbox.value()))
        self.order+=1

        if exec_on==True:
            self.embedded_db()
            self.exec()

    def update_item(self, **kwargs):
        self.item.sigRegionChanged.disconnect(self.item.deltas_update)#to block anchor pos change unless explicit
        self.__class__.anchor_dt=(self.dtx[2],self.yv2)
        super().update_item(**kwargs)
        
        self.item._state=self.item.state #workaround to block after-dialog baseline move
        blp=self.item.baseline.state['points']
        blp[1]=blp[0]+self.item.relative_pos
        self.item.baseline.setState(self.item.baseline.state) #re-position baseline if relative_pos changed
        self.item.sigRegionChanged.connect(self.item.deltas_update)#reconnect after dialog

class DChannelTabsDialog(uitools.TabsDialog):
    def __init__(self,plt,item=None,**kwargs):
        level_props=dict(desc_on=False,width=cfg.FIBOWIDTH,color=cfg.FIBOCOLOR,style=cfg.FIBOSTYLE)
        #set default color of levels at the foreground color
        level_props['color']=plt.graphicscolor
        super().__init__(DChannelDialog,plt,wname='Channel',item=item,level_props=level_props,**kwargs)

class DrawChannel(DrawTrendLine):
    sigDeltasUpdated=QtCore.Signal(object)
    sigRemoval=QtCore.Signal()
    sigPropsChanged=QtCore.Signal(object)
    sigRayStatusUpdate=QtCore.Signal()
    sigTimeseriesChanged=QtCore.Signal(object,object)   

    def __init__(self, plt, coords=chtl.zero2P(), levels=None,**kwargs):
        super().__init__(plt, coords=coords, dialog=DChannelTabsDialog,**kwargs)
        self._state=dict(self.state) #to keep record of the pre-event state
        #set default levels
        level_props=dict(width=cfg.FIBOWIDTH,color=cfg.FIBOCOLOR,style=cfg.FIBOSTYLE)
        self.props['levels']=[]
        for lvl in [50.0]:
            self.props['levels'].append(dict(show=False,value=lvl,desc_on=False,removable=False,**level_props))
        #set metaprops in newly created (not saved) object
        if self.is_new and self.myref in self.mprops:
            self.props=dict(self.mprops[self.myref])
        #reset/remove anchor_dt that earlier propogated to the metaprops variable:
        try: self.props.pop('anchor_dt')
        except Exception:pass
        #set default level (50.0) at foreground color
        metalevels=self.mprops[self.myref]['levels'] if self.myref in self.mprops and 'levels' in self.mprops[self.myref] else None
        if metalevels is None:
            for lvl in self.props['levels']:
                lvl['color']=self.plt.graphicscolor
        if levels is not None:
            self.props['levels']=levels
        self.level_items=[]
        if self.is_new==False: #used when sourced from saved state file
            if metalevels is not None:
                self.props['levels']=metalevels
            self.setup_lines()
            self.baseline.setSelected(False)
        self.context_menu=self.create_menu(ray_on=True,description='Channel')

        self.sigRegionChanged.connect(self.deltas_update)
    
    def setup_mouseclicks(self, mouseClickEvent):
        super().setup_mouseclicks(mouseClickEvent)
        if self.is_new and self.click_count==self.clicks:
            self.setup_lines()    
    
    def setup_lines(self):
        self.baseline=_ChannelBaseline(self.plt,coords=self.xy,parent_line=self)
        self.plt.addItem(self.baseline)
        self.set_levels()#must be set after the baseline
        self._state=dict(self.state)

    @property
    def deltas(self):
        d0=self.state['points'][0]-self._state['points'][0]
        d1=self.state['points'][1]-self._state['points'][1]
        dpoints=[d0,d1]
        dpos=self.state['pos']-self._state['pos']
        dlts=dict(self.state)
        dlts['pos']=dpos
        dlts['points']=dpoints
        self._state=dict(self.state)
        return dlts
    
    def deltas_update(self):
        if self.change:
            self.sigDeltasUpdated.emit(self.deltas)
        else: #to ensure correct _self.state reset
            self._state=self.state

    def mouse_update(self): #to ensure correct _self.state reset in sigRangeChangeFinished()
        if hasattr(self,'_state'):
            self._state['pos']=Point(0.0,0.0)
        super().mouse_update()        
        
    @property
    def relative_pos(self):
        state=self.getState()
        return state['points'][1]-state['points'][0]

    def save_props(self):
        self.change_state() # to ensure that the state is not lost on
        self.deltas_update() # saves and restores
        bdtxy0=self.baseline.dtxy[0]
        if isinstance(bdtxy0,Point):
            self.props['anchor_dt']=[bdtxy0.x(),bdtxy0.y()]
        else:
            self.props['anchor_dt']=bdtxy0
        return super().save_props()

    def set_props(self, props):
        super().set_props(props)
        self.set_levels()
        self.sigPropsChanged.emit(props)

    def right_clicked(self, ev):
        super(DrawTrendLine,self).right_clicked(ev,anchor=self.baseline.dtxy[0],tseries=self.timeseries,
            dtxy=self.dtxy)
        if self.maction==self.ray_left_act or self.maction==self.ray_right_act:
            self.sigRayStatusUpdate.emit()

    def left_clicked(self,ev):
        super().left_clicked(ev)
        self.set_baseline_selected(self.translatable)

    def set_baseline_selected(self,s):
        try:
            self.baseline.translatable=s
            self.baseline.setSelected(s)
            self.baseline.ray.setMovable(s)
        except Exception:
            pass
    
    def set_selected(self, s):
        self.set_baseline_selected(s)
        return super().set_selected(s)

    def set_levels(self):
        #To avoid full levels deletion and restatement, calc and process only the difference
        
        dcl=[m for m in self.props['levels'] if m['show']==True] #show==True dict slice
        diff=len(dcl)-len(self.level_items)

        if diff>0:
            while diff!=0:
                newitem=_ChannelParallel(0.0,self.plt,parent_line=self)
                self.level_items.append(newitem)
                self.plt.addItem(newitem)
                diff-=1
        else:
            while diff!=0:
                itm=self.level_items.pop()
                itm.removal()
                del itm.ray
                del itm
                diff+=1
        
        for i,item in enumerate(self.level_items):
            lvl=dcl[i]
            if lvl['show']:
                item.set_props(lvl)    

    def ts_change(self, ts):
        self.sigRegionChanged.disconnect(self.deltas_update)
        super().ts_change(ts)
        self._state=dict(self.state)
        self.sigRegionChanged.connect(self.deltas_update)
        self.sigTimeseriesChanged.emit(ts,self.relative_pos)

    def removal(self):
        self.sigRemoval.emit()
        super().removal()

class _PRay(AltInfiniteLine): #Pitchfork ray class
    def __init__(self, *args, parent=None,**kwargs):
        super().__init__(*args, **kwargs)
        self.extension=cfg.RAYDIR['r']
        self.setSelected(False)
        self.translatable=False
        self.is_persistent=False
        self.setParent(parent)
        #Disconnect from mouse interactions
        self.hoverEvent=lambda *args: None
        self.evpos=lambda ev: self.mapToView(ev.pos())
        
        self.parent().sigPropsChanged.connect(self.set_props)

    def mouseDragEvent(self, ev):
        return self.parent().mouseDragEvent(ev)
    
    def left_clicked(self,ev):
        return self.parent().left_clicked(ev)

    def right_clicked(self,ev):
        return self.parent().right_clicked(ev)

class _Pitchfork:
    def __init__(self,parent) -> None:
        self.parent=parent
        self.plt=self.parent.plt
        self.prays=[]
        xy=self.xy()
        pangle=self.pangle()
        for pt in xy:
            pray=_PRay(self.plt,parent=self.parent,pos=pt,angle=pangle)
            self.prays.append(pray)
            self.plt.addItem(pray)
    
        self.parent.sigRegionChanged.connect(self.refresh)

    def xy(self):
        pstate=self.parent.getState()
        ppos=pstate['pos']
        ppoints=pstate['points']
        while len(ppoints)<self.parent.clicks:#stub for restore initialisation
            ppoints.append(Point(0.0,0.0))
        xy=[]
        for pt in ppoints:
            xy.append(pt+ppos)
        return xy
    
    def pangle(self): #pitchfork angle
        xy=self.xy()
        dxy=xy[1]+(xy[2]-xy[1])/2-xy[0]
        return math.degrees(math.atan2(dxy.y(),dxy.x()))

    def refresh(self):
        xy=self.xy()
        if len(xy)==self.parent.clicks: #to ensure 2 legs and workaround pg getState() bug
            pangle=self.pangle()
            for i,pray in enumerate(self.prays):
                pray.setPos(xy[i])
                pray.setAngle(pangle)
    
    def removal(self):
        for pray in self.prays:
            self.plt.removeItem(pray)

class DrawPitchfork(DrawItem,AltPolyLine):
    sigPropsChanged=QtCore.Signal(object)
    def __init__(self,plt,coords=chtl.zero2P(),clicks=3,**kwargs):
        dlg=lambda *args,**kwargs: FiboExtDialog.__call__(*args,exec_on=True,
            wname='Pitchfork',**kwargs)
        super().__init__(plt,dialog=dlg,clicks=clicks,**kwargs)
        super(DrawItem,self).__init__(coords)
        self.initialisation()
        self.set_transparency()
        self.setZValue(-10)
        self.is_draw=False #to exclude the body of the roi from valid selectable areas and leave only the segments as such areas
        self.pfork=None
        self.context_menu=self.create_menu(description='Pitchfork')

        if not self.is_new:
            self.set_pitchfork()

        self.sigRegionChangeFinished.connect(self.nullify_pos)
        self.plt.sigMouseOut.connect(self.magnetize)

    def setup_mousemoves(self, mouseMoveEvent):
        super().setup_mousemoves(mouseMoveEvent)
        if self.click_count==2 and self.pfork is None:
            self.set_pitchfork()
            self.sigPropsChanged.emit(self.props)

    def set_transparency(self):
        transparent=QtGui.QColor(QtCore.Qt.transparent)
        self.setPen(color=transparent)
        self.hoverPen.setColor(transparent)

    def set_props(self,props):
        try:
            props.pop('extension')
        except Exception:
            pass
        super().set_props(props)
        self.set_transparency()
        self.sigPropsChanged.emit(props)

    def set_pitchfork(self):
        self.pfork=_Pitchfork(self)

    def nullify_pos(self):
        state=self.getState()
        ppos=state['pos']
        if ppos!=Point(0.0,0.0):
            ppoints=state['points']
            ps=[ppoints[0]+ppos,ppoints[1]+ppos]
            state['points']=ps
            state['pos']=Point(0.0,0.0)
            self.setState(state)
    
    def left_clicked(self, ev):
        if not self.contains(ev.pos()):
            return super().left_clicked(ev)

    def right_clicked(self,ev):#full override is simpler
        if not self.contains(ev.pos()):
            super().right_clicked(ev,tseries=self.timeseries,dtxy=self.dtxy)
    
    def ts_change(self, ts):
        super().ts_change(ts)
        self.setSelected(self.selected)
    
    def mouseDragEvent(self, ev):
        if not self.contains(ev.pos()):
            super().mouseDragEvent(ev)

    def magnetize(self, hls=3):
        return super().magnetize(hls)

    def removal(self):
        self.pfork.removal()
        del self.pfork
        super().removal()

class CrossHair:
    def __init__(self,plt):
        wd=cfg.CROSSHAIR_WIDTH
        self.vLine = pg.InfiniteLine(angle=90, pen=pg.mkPen('w',width=wd), movable=False)
        self.hLine = pg.InfiniteLine(angle=0, pen=pg.mkPen('w',width=wd), movable=False)
        self.textX = pg.TextItem(anchor=(0,0.75))
        self.textY = pg.TextItem(anchor=(1,0.75))
        self.textOHLC=pg.TextItem(anchor=(0,0.25))

        clr=plt.foregroundcolor
        for line in self.vLine,self.hLine:
            line.setPen(color=clr,width=wd)
        for txt in self.textX,self.textY,self.textOHLC:
            txt.setColor(clr)

        plt.addItem(self.vLine, ignoreBounds=True)
        plt.addItem(self.hLine, ignoreBounds=True)
        plt.addItem(self.textX, ignoreBounds=True)
        plt.addItem(self.textY, ignoreBounds=True)
        plt.addItem(self.textOHLC, ignoreBounds=True)

        self.ax=plt.getAxis('bottom')
        self.ay=plt.getAxis('right')

        self.plt=plt
        self.pre=chtl.precision(self.plt.chartitem.symbol)
        
        try: self.refresh()
        except Exception: pass

        self.plt.lc_thread.sigLastCandleUpdated.connect(self.refresh_lc)
        self.plt.vb.sigStateChanged.connect(self.refresh)
        self.plt.sigTimeseriesChanged.connect(self.refresh)
        self.plt.scene().sigMouseMoved.connect(self.refresh)
    
    def refresh_lc(self):
        ts=self.plt.chartitem.timeseries
        x=self.plt.mapped_xy[0]
        dtx=chtl.ticks_to_times(ts,x)
        if int(dtx)>=ts.times[-1]:
            self.refresh()

    def refresh(self):
        ts=self.plt.chartitem.timeseries
        tf=ts.timeframe
        x=self.plt.mapped_xy[0]
        y=self.plt.mapped_xy[1]
        self.vLine.setPos(x)
        self.hLine.setPos(y)
        x0=self.ax.range[0]
        x1=self.ax.range[1]
        y0=self.ay.range[0]
        y1=self.ay.range[1]    
        self.textX.setPos(x,y0)
        dtxs,ind=chtl.screen_to_plot(ts,x)

        if tf>=cfg.PERIOD_D1:
            self.textX.setText(dtxs.strftime("%d %b'%y"))
            self.textX.setFontSize(cfg.D_FONTSIZE)
        else:
            self.textX.setText(dtxs.strftime("%d %b'%y %H:%M"))
            self.textX.setFontSize(cfg.D_FONTSIZE)
        self.textY.setPos(x1,y)
        self.textY.setText("{:.{pr}f}".format(y,pr=self.pre))
        self.textY.setFontSize(cfg.D_FONTSIZE)

        try:           
            self.textOHLC.setPos(x0,y1)
            self.textOHLC.setText("O:{:.{pr}f}".format(ts.opens[ind], pr=self.pre)+
            " H:{:.{pr}f}".format(ts.highs[ind], pr=self.pre)+
            " L:{:.{pr}f}".format(ts.lows[ind],pr=self.pre)+
            " C:{:.{pr}f}".format(ts.closes[ind],pr=self.pre))
            self.textOHLC.setFontSize(cfg.D_FONTSIZE)
        except Exception:
            pass

    def __del__(self):
        self.plt.removeItem(self.vLine)
        self.plt.removeItem(self.hLine)
        self.plt.removeItem(self.textX)
        self.plt.removeItem(self.textY)
        self.plt.removeItem(self.textOHLC)

class PriceLine:
    def __init__(self,plt):
        self.plt=plt
        clr=self.plt.chartprops[cfg.pricelinecolor]
        self.hLine = pg.InfiniteLine(angle=0, pen=pg.mkPen(color=clr,width=cfg.PRICELINE_WIDTH), movable=False)
        self.hLine.setZValue(-10)
        plt.addItem(self.hLine, ignoreBounds=True)
        self.textY = pg.TextItem(anchor=(1,0.75))
        self.textY.setColor(clr)
        plt.addItem(self.textY, ignoreBounds=True)
        self.ax=plt.getAxis('bottom')
        self.pre=chtl.precision(self.plt.chartitem.symbol)
        self.refresh()
        
        self.plt.sigChartPropsChanged.connect(self.update_props)
        self.plt.lc_thread.sigLastCandleUpdated.connect(self.refresh)
        self.plt.vb.sigStateChanged.connect(self.refresh)
        self.plt.sigTimeseriesChanged.connect(self.refresh)

    def refresh(self):
        ts=self.plt.chartitem.timeseries
        y=ts.closes[-1]
        self.hLine.setPos(y)
        x1=self.ax.range[1]   
        self.textY.setPos(x1,y)
        
        txt="{:.{pr}f}".format(y,pr=self.pre)
        self.textY.setText(txt)
        self.textY.setFontSize(cfg.D_FONTSIZE)

    def update_props(self,props):
        clr=props[cfg.pricelinecolor]
        self.hLine.setPen(color=clr,width=cfg.PRICELINE_WIDTH)
        self.textY.setColor(clr)

    def __del__(self):
        try:
            self.plt.removeItem(self.hLine)
            self.plt.removeItem(self.textY)
            del self.hLine
            del self.textY
        except Exception:
            pass

class AltGrid(pg.GridItem):
    def __init__(self, plt,pen='default'):
        super().__init__(pen, textPen=None)
        self.plt=plt
        self.setTickSpacing(x=[None,None],y=[None,None])
        self.plt.addItem(self)

class AltPlotWidget(pg.PlotWidget):
    sigDeletePreviousThread=QtCore.Signal()
    sigTimeseriesChanged=QtCore.Signal(object)
    sigMouseOut=QtCore.Signal()
    sigChartPropsChanged=QtCore.Signal(object)
    def __init__(self, mwindow=None, subwindow=None,chartitem=None, draw_mode=None, crosshair_enabled=False, 
            plotID=None,chartprops=cfg.D_CHARTPROPS,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.plotID=chtl.nametag() if plotID is None else plotID
        self.description=''
        self.mwindow=mwindow
        self.subwindow=subwindow
        self.chartitem=chartitem #candle/bar/line item
        self.symbol=None if chartitem is None else chartitem.symbol
        self.charttype=None if chartitem is None else chartitem.charttype
        self.timeframe=None if chartitem is None else chartitem.timeframe
        self.precision=None if chartitem is None else chtl.precision(chartitem.symbol)
        self.vb=self.getViewBox()
        self.pitm=self.getPlotItem()
        self.clicks=1
        self.draw_mode=draw_mode
        self.crosshair_enabled=crosshair_enabled
        self.crosshair_item=None
        self.chartprops=dict(chartprops)
        if self.chartprops!=cfg.CHARTPROPS:
            self.set_chartprops()
        self.priceline_enabled=False
        self.grid_enabled=False
        self.item_in_progress=None
        self.mapped_xy=chtl.zero1P() #to track the mouse point in mouse_moved()
        self.hovered_items=None
        self.lc_thread=None
        self.lc_item=None

        self.setMenuEnabled(False) #flat disable right-click menu,check manuals for disabling specific options

        # self.scene() is a pyqtgraph.GraphicsScene.GraphicsScene.GraphicsScene
        self.scene().sigMouseClicked.connect(self.mouse_clicked)    
        self.scene().sigMouseMoved.connect(self.mouse_moved)
        self.scene().sigMouseHover.connect(self.mouse_hover)
        try: #does not work for main plot, only for dockplots
            self.subwindow.plt.sigTimeseriesChanged.connect(self.ts_change)
        except Exception:
            pass

        self.hideAxis('left')
        self.showAxis('right')

    @property
    def foregroundcolor(self):
        return chtl.pgclr_to_hex(self.chartprops[cfg.foreground])
    
    @property
    def graphicscolor(self):
        return chtl.pgclr_to_hex(self.chartprops[cfg.graphicscolor])

    def link_chartitem(self,item,lc_item=None):
        self.chartitem=item
        self.symbol=item.symbol
        self.charttype=item.charttype
        self.timeframe=item.timeframe
        self.precision=chtl.precision(item.symbol)
        self.lc_item=lc_item
        ci=item
        ts=ci.timeseries
        self.sigDeletePreviousThread.emit()
        try: 
            self.lc_thread.wait()
        except Exception:
            pass
        del self.lc_thread
        self.lc_thread=NewThread(self,symbol=ci.symbol,timeframe=ci.timeframe,timecut=ts.timecut,
            indexcut=ts.indexcut)
        self.lc_thread.start()
        self.lc_thread.sigLastCandleUpdated.connect(self.redraw_lc)
        self.lc_thread.sigInterimCandleUpdated.connect(self.append_inc)            
    
    def ts_change(self,ts):
        if self.chartitem.timeseries is not ts:
            self.chartitem=self.subwindow.plt.chartitem

    def mouseReleaseEvent(self, ev): #override to ensure that sigMouseRelease is emitted
        self.sigMouseOut.emit()
        super().mouseReleaseEvent(ev)

    def mouse_clicked(self, mouseClickEvent):
        if self.draw_mode is None:
            if mouseClickEvent.button()==QtCore.Qt.MouseButton.MiddleButton:
                self.cross_hair()
            nodrawhit=True #unselect draw items if clicked to empty space
            if self.hovered_items is not None:
                for itm in self.hovered_items:
                    if chtl.item_is_draw(itm):
                        nodrawhit=False
                        break
            if nodrawhit:
                for itm in self.listItems():
                    if isinstance(itm,DrawItem) or isinstance(itm,AltInfiniteLine):
                        itm.set_selected(False)
        else:
            mapped_xy=Point(self.vb.mapSceneToView(mouseClickEvent.scenePos()))
            for dk in self.subwindow.docks:
                dockplt=dk.widgets[0]
                if dockplt is not self:
                    dockplt.draw_mode=None
                    if chtl.OBJ_IS('InfiniteLine',self.draw_mode):
                        dockplt.item_in_progress.removal()
                        dockplt.item_in_progress=None            
    
            if chtl.OBJ_IS('ROI',self.draw_mode): #items requiring 2 or more clicks - for initiation and finalisation
                xy=[mapped_xy,mapped_xy]
                itm=self.draw_mode(self.subwindow.plt,xy,dockplt=self,caller='mouse_clicked')
                self.draw_mode=None
            else: #items requiring only 1 click
                self.item_in_progress=None
                self.draw_mode=None
        
    def mouse_moved(self, mouseMoveEvent):
        self.mapped_xy=Point(self.vb.mapSceneToView(mouseMoveEvent))
        if self.draw_mode!=None: 
            if chtl.OBJ_IS('InfiniteLine',self.item_in_progress):
                self.item_in_progress.removal()
                self.item_in_progress=self.draw_mode(self,self.mapped_xy)
                self.addItem(self.item_in_progress)
    
    def mouse_hover(self, items):
        self.hovered_items=list(items)

    def draw_act(self, action):
        self.draw_mode=action
        if chtl.OBJ_IS('InfiniteLine',self.draw_mode):
            self.item_in_progress=self.draw_mode(self)
        for dk in self.subwindow.docks:
            dockplt=dk.widgets[0]
            if dockplt.draw_mode is None:
                dockplt.draw_act(action)

    def cross_hair(self):
        if self.crosshair_enabled:
            try:
                del self.crosshair_item
                self.crosshair_item=None
            except Exception: pass
        else:
            self.crosshair_item=CrossHair(self)
                    
        self.crosshair_enabled = not self.crosshair_enabled
    
    def export_act(self):
        self.scene().contextMenuItem=self.vb
        self.scene().showExportDialog()
    
    def copy_item_act(self,copyline=False):
        for itm in self.listItems():
            if isinstance(itm,DrawItem) and itm.translatable and itm.is_persistent:
                itm.set_selected(False)
                if copyline:
                    if isinstance(itm,DrawChannel) or isinstance(itm,DrawFibo):
                        newitm=DrawTrendLine(self)
                    elif isinstance(itm,DrawPitchfork):
                        xy=itm.pfork.xy()
                        points=(xy[0],xy[1]+(xy[2]-xy[1])/2)
                        newitm=DrawTrendLine(self,coords=points)
                        newitm.props['extension']=cfg.RAYDIR['r']
                    else:
                        newitm=itm.__class__(self)
                else:
                    newitm=itm.__class__(self)
                self.addItem(newitm)
                if not copyline or not isinstance(itm,DrawPitchfork):
                    try:newitm.set_dt(itm.save_dt())
                    except Exception:pass
                try:newitm.set_props(itm.save_props())
                except Exception:pass
                try: newitm.repaint_ray()
                except Exception:pass
                vr=self.viewRange()
                rn=[x*cfg.COPY_DIST for x in [vr[0][1]-vr[0][0],vr[1][1]-vr[1][0]]]
                newitm.translate(0,rn[1],None)
  
    def select_all_act(self):
        for itm in self.listItems():
            if (isinstance(itm,DrawItem) or isinstance(itm,AltInfiniteLine)) and itm.is_persistent:
                itm.set_selected(True)

    def deselect_all_act(self):
        for itm in self.listItems():
            if (isinstance(itm,DrawItem) or isinstance(itm,AltInfiniteLine)) and itm.is_persistent:
                itm.set_selected(False)

    def delete_act(self):
        for itm in self.listItems():
            if (isinstance(itm,DrawItem) and itm.is_persistent and itm.translatable) or \
                (isinstance(itm,AltInfiniteLine) and itm.is_persistent and itm.movable):
                itm.item_hide(persistence_modifier=False)
    
    def undo_act(self):
        for itm in self.listItems():
            if isinstance(itm,DrawProps) and not itm.isVisible() and itm.parent() is None:
                itm.item_replicate()
                itm.removal()

    def priceline_act(self):
        if self.priceline_enabled==False:
            self.priceline=PriceLine(self)
            self.priceline_enabled=True
        else:
            del self.priceline
            self.priceline_enabled=False

    def grid_act(self):
        if self.grid_enabled==False:
            self.grid=AltGrid(self)
            self.grid_enabled=True
        else:
            self.removeItem(self.grid)
            del self.grid
            self.grid_enabled=False

    def remove_item(self,itm):
        try:
            itm.removal()
        except Exception:
            self.removeItem(itm)
        finally:
            pass
        del itm

    def redraw_chartitem(self,item,start=None,end=None): #redraw chartitem
        if item!=None:
            ci=item
            ts=ci.timeseries
            symbol=ci.symbol
            ct=ci.charttype
            self.removeItem(item)
            item=tmss.PlotTimeseries(symbol,ct,ts=ts,session=self.mwindow.session,
                fetch=self.mwindow.fetch,start=start,end=end,chartprops=self.chartprops)
            self.addItem(item)
        return item
        # self.vb.update()
    
    def redraw_lc(self): #update last_candle
        if self.chartitem!=None:
            ts=self.chartitem.timeseries
            ts.update_lc(self.lc_thread.lc)
            self.lc_item=self.redraw_chartitem(self.lc_item,start=-1)

    def append_inc(self,inc):
        if self.chartitem!=None and self.lc_thread.inc!=None:
            # passed from NewThread's self.inc, [:-1] to ignore last candle 
            # and leave for consideration interims only (typically a single candle)
            # [1:] to remove index number and leave time and ohlc only:
            for c in inc['data'][:-1]:
                self.chartitem.timeseries.replace_candle(c[1:])
                self.chartitem=self.redraw_chartitem(self.chartitem)
            
    def symb_change(self):
        symb=self.eline.text().strip().upper() #strip of spaces and capitalize
        chtl.set_chart(self,symbol=symb)

        self.subwindow.setFocus()
        
        self.eline.returnPressed.disconnect(self.symb_change)
        self.subwindow.sigAltSubWindowClosing.disconnect(self.mwindow.win_close_sig_func)
        self.mwindow.sigEscapePressed.disconnect(self.mwindow.win_close_sig_func)
        self.wnd_eline.close()
        self.mwindow.mdi.removeSubWindow(self.wnd_eline)
        del self.eline
        del self.wnd_eline

    def set_chartprops(self, props=None,meta=False):
        cs=self.chartprops
        if props is not None:
            for key in props:
                cs[key]=props[key]
            if cs[cfg.font] is None:
                cs[cfg.font]=self.mwindow.app.font().family()
            elif isinstance(cs[cfg.font],QtGui.QFont):
                cs[cfg.font]=cs[cfg.font].family()
            if cs[cfg.fontsize] is None:
                cs[cfg.fontsize]=self.mwindow.app.font().pointSize()
        if meta:
            self.mwindow.props['chartprops']=cs
        if self.chartprops is not None:
            self.setBackground(cs[cfg.background])
            font=QtGui.QFont()
            for axis in [self.getAxis('bottom'),self.getAxis('right')]:
                axis.setPen(color=cs[cfg.foreground])
                axis.setTextPen(color=cs[cfg.foreground])
                if cs[cfg.font] is not None:
                    font.setFamily(cs[cfg.font])
                    axis.setTickFont(font)
                if cs[cfg.fontsize] is not None:
                    font.setPointSize(cs[cfg.fontsize])
            self.mwindow.window_act('Refresh')
        if self is self.subwindow.plt:
            for dk in self.subwindow.docks[1:]: #slice to exclude the plt itself and avoid infinite loop
                dk.widgets[0].set_chartprops(props=self.chartprops)
            self.sigChartPropsChanged.emit(self.chartprops)

class NewThread(QtCore.QThread):
    sigLastCandleUpdated=QtCore.Signal()
    sigInterimCandleUpdated=QtCore.Signal(object)
    def __init__(self,plt,symbol=cfg.D_SYMBOL,timeframe=cfg.D_TIMEFRAME,
            timecut=0,indexcut=0,*args,**kwargs) -> None:
        super().__init__(*args,**kwargs)
        self.sb=symbol
        self.tf=timeframe
        self.fromdt=timecut
        self.tcc=indexcut
        self.inc=None
        self.plt=plt
        self.subwindow=self.plt.subwindow
        self.mwindow=self.plt.mwindow
        self.fetch=self.mwindow.fetch
        self.tmr=self.mwindow.props['timer']
        self.session=self.mwindow.session
        self.lc=self.fetch.fetch_lc(self.session,self.sb,self.tf)
        self.prev_lc=self.lc
        #to ensure no candle data loss on initiation:
        self.data_request()
    
    def data_request(self):
        self.lc=self.fetch.fetch_lc(self.session,self.sb,self.tf)
        if self.lc!=self.prev_lc:
            if self.lc is not None and self.lc['data'] is not None:
                lct=self.lc['data'][-1][1]
                if self.prev_lc is None or self.prev_lc['data'] is None:
                    self.prev_lc=self.lc
                else:
                    prev_lct=self.prev_lc['data'][-1][1]
                    if lct>prev_lct:
                        self.prev_lc=self.lc                
                        todt=time.time()
                        self.inc=self.fetch.fetch_data(session=self.session, symbol=self.sb,fromdt=self.fromdt,todt=todt,
                                timeframe=self.tf,indexcut=self.tcc)
                        if self.inc!=None:
                            prev_fromdt=self.fromdt
                            self.fromdt=self.inc['data'][-1][1]
                            self.tcc+=(self.fromdt-prev_fromdt)//self.tf
                            self.sigInterimCandleUpdated.emit(self.inc)
            self.sigLastCandleUpdated.emit()

    #override
    def run(self):
        def dr():
            self.data_request()
                       
        def closure():
            if hasattr(self,'timer'):
                self.timer.stop() #stop QTimer
            self.quit() #quit QThread

        if cfg.DYNAMIC_QUERYING==True:
            self.timer = QtCore.QTimer()
            self.timer.moveToThread(self)
            self.timer.timeout.connect(dr)    
            self.timer.start(self.tmr)
        self.mwindow.sigMainWindowClosing.connect(closure)
        self.subwindow.sigAltSubWindowClosing.connect(closure)
        self.plt.sigDeletePreviousThread.connect(closure)
        # self.loop=QtCore.QEventLoop()
        # self.loop.exec()
        super().run()

