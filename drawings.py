import PySide6
from PySide6 import QtWidgets,QtCore,QtGui
import math, time, datetime
import numpy as np
import pyqtgraph as pg
from pyqtgraph import Point, ROI
from pyqtgraph.graphicsItems.TargetItem import TargetItem
import typing

import cfg
import overrides as ovrd, overrides
import timeseries as tmss, timeseries
from timeseries import dtPoint, dtCords
import charttools as chtl,charttools
import uitools
from fetcher import FetcherMT5


#debugging section
from _debugger import _print,_printcallers,_exinfo,_ptime,_c,_p,_pc,_pp,_fts

class DrawProps:
    def config_props(self,mwindow,props=None,caller=None):
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
    
    @property
    def raydir(self):
        return self.props.get('raydir',None)
    
    @raydir.setter
    def raydir(self,x):
        self.props['raydir']=x

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
    
    def update_props(self):
        self.set_props(self.props)
    
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
        if newitem not in self.plt.listItems():
            self.plt.addItem(newitem)
        if hasattr(newitem,'set_dtc'):
            newitem.set_dtc(self.get_dtc())
        if hasattr(newitem,'set_props'):
            newitem.set_props(self.save_props())
        if hasattr(newitem,'set_selected'):
            newitem.set_selected(True)

class DrawItem(DrawProps): #ROI generic abstract class
    sigHoverLeaveEvent=QtCore.Signal(object)
    def __init__(self,plt,dockplt=None,dialog=uitools.DrawPropDialog,clicks=2,
        props=None,caller=None, ray=None, menu_name=None):
        super().config_props(plt.mwindow,props=props,caller=caller)
        self.timeseries=plt.chartitem.timeseries
        self.plt=plt if dockplt is None else dockplt
        self.precision=self.plt.precision
        self.dialog=dialog
        self.hsz=cfg.HANDLE_SIZE
        self.clicks=clicks
        self.click_count=1 # the item initiates at the first click on the chart
        self.is_new=False #to inform derivative classes whether the item is new
        if self.color is None:
            self.color=self.plt.graphicscolor
        
        self.raydir=ray

        self.menu_name=menu_name
        self.context_menu=self.create_menu(description=menu_name) if menu_name else None

        self._dtc=dtCords.make(n=clicks).apply(dtPoint(ts=self.timeseries))

    def addHandle(self, *args, **kwargs): #imported module override (handle size)
            self.handleSize = self.hsz
            self.handlePen=self.plt.foregroundcolor
            self.handleHoverPen=self.handlePen
            super(DrawItem,self).addHandle(*args, **kwargs)

    def config_item(self):
        self.set_dtc(self.rawdtc,force=True)
        self.change=False #user drag state monitoring
        super(DrawItem,self).setZValue(0)
        
        self.setAcceptedMouseButtons(QtCore.Qt.MouseButton.LeftButton | QtCore.Qt.MouseButton.RightButton)
        
        # Below singal connections ensure that only mechanical (non-programmatic) 
        # changes are processed by mouse_update() function in order to avoid  changes of the 
        # cached dt values by non-mechanical functions such as ts_update().
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
    
    # Raw coordinates
    @property
    def rawdtc(self):
        # Should return dtCords (set of dtPoints) consisting of None, and raw x,y adjusted by the pos
        # set as property for brevity
        raise NotImplementedError('rawdtc is not implemented')

    def get_dtc(self):
                
        return self.rawdtc.fillnone(self._dtc)
    
    def save_dtc(self):

        return self.get_dtc().rollout()

    # Sets dt coordinates and returns True if the real position is to be updated and False otherwise
    def set_dtc(self, dtc : dtCords|dtPoint|list|tuple|None,force=False)->bool:
        '''
        Function serves as the single unified point of setting coordinates.
        Function 
        - sets position based on dtc if 1 or 3 pos args are given
        - sets dtc based on pos if 2 pos args are given
        - refreshes pos based on dtc where no args are given, eg. at timeseries change
        - processes JSON based saved data to restore position
        
        kwargs:
        - force: forces update of real position even where only raw coordinates are given.
        Default: False, to avoid updating real position where it is updated externally, eg. in __init__ or
        mouse_update().   if only raw coordinates are given and force is False, the attributes are updated 
        but the the real position is not.

        Returns True if the real position is updated and False otherwise
        ''' 
        c=dtc if type(dtc) in (dtCords,dtPoint) else dtCords([dtPoint(*dtp) for dtp in dtc])
 
        self._dtc=self._dtc.apply(c)                

        # dont set real position solely based on raw coords unless explicitly forced
        # to avoid idle real repositioning eg. on mouse_updates
        if force:
            update_pos=True
        elif type(c)==dtPoint:
                update_pos=(c.dt is not None or c.ts is not None)
        elif type(c)==dtCords:
            update_pos=(c.cords[0].dt is not None or c.cords[0].ts is not None)
        else:
            raise TypeError("Invalid input type")
      
        return update_pos

    def mouseClickEvent(self, ev):
        if ev.button()==QtCore.Qt.MouseButton.LeftButton:
            self.left_clicked(ev)
        elif ev.button()==QtCore.Qt.MouseButton.RightButton:
            self.right_clicked(ev)
        return super().mouseClickEvent(ev)
    
    def ts_change(self,ts):
        self.timeseries=ts
        self.set_dtc(dtPoint(ts=ts))
    
    def set_selected(self, s):
        self.translatable=s #translatable=movable
        self.setSelected(s)

    def mouse_update(self):
        raise NotImplementedError('mouse_update is not implemented')
                
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

    def create_menu(self,description=None):
        context_menu=QtWidgets.QMenu()
        if description is not None:
            context_menu.addSection(description)
        self.prop_act=context_menu.addAction('Properties')
        self.pushdown_act=context_menu.addAction('Push down')
        self.liftup_act=context_menu.addAction('Lift up')
        context_menu.addSeparator()
        self.rem_act=context_menu.addAction('Remove')
        if self.raydir:
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
        if self.raydir:
            if self.maction == self.ray_right_act:
                self.raydir=chtl.ray_mode(self.raydir,cfg.RAYDIR['r'])
                self.set_props(self.props)
            elif self.maction == self.ray_left_act:
                self.raydir=chtl.ray_mode(self.raydir,cfg.RAYDIR['l'])
                self.set_props(self.props)

    def update_menu(self):
        if self.raydir==cfg.RAYDIR['b']:
            self.ray_right_act.setChecked(True)
            self.ray_left_act.setChecked(True)
        elif self.raydir==cfg.RAYDIR['n']:
            self.ray_right_act.setChecked(False)
            self.ray_left_act.setChecked(False)
        elif self.raydir==cfg.RAYDIR['r']:
            self.ray_right_act.setChecked(True)
            self.ray_left_act.setChecked(False)
        elif self.raydir==cfg.RAYDIR['l']:
            self.ray_right_act.setChecked(False)
            self.ray_left_act.setChecked(True)
        else:
            self.ray_right_act.setChecked(False)
            self.ray_left_act.setChecked(False)

    def setup_mouseclicks(self,mouseClickEvent):
        if mouseClickEvent.button()==QtCore.Qt.MouseButton.LeftButton:
            xy=self.plt.mapped_xy #Point(self.plt.vb.mapSceneToView(mouseClickEvent.scenePos()))
            self.click_count+=1 # the function kicks in at the second click on chart
            
            # self.clicks==None is used for dynamic endpoint lists such as polylines. 
            if self.clicks is None or self.click_count<self.clicks:
                update_dtc=dtCords.make(n=self.clicks if self.clicks else self.click_count+1).set_cord(self.click_count-1,dtPoint(None,*xy))
                self.set_dtc(update_dtc,force=True)
                self.set_selected(True)
            else:
                update_dtc=dtCords.make(n=self.clicks).set_cord(self.click_count-1,dtPoint(None,*xy))
                self.set_dtc(update_dtc,force=True)
                self.plt.scene().sigMouseClicked.disconnect(self.setup_mouseclicks)
                self.set_selected(True)

    def setup_mousemoves(self,mouseMoveEvent):
        xy=Point(self.plt.vb.mapSceneToView(mouseMoveEvent))
        i=-1 if self.clicks is None else self.click_count # -1 for polyline
        if self.clicks is None or self.click_count<self.clicks:
            update_dtc=dtCords.make(n=len(self._dtc)).set_cord(i,dtPoint(None,*xy))
            self.set_dtc(update_dtc,force=True)
        else:
            self.plt.scene().sigMouseMoved.disconnect(self.setup_mousemoves)

    def magnetize(self) -> None:
        
        if not self.plt.mwindow.props['magnet'] or not self.translatable: 
            return
        
        mapper=lambda x: self.mapFromDevice(x)
        mp0=mapper(Point(0,0))
        if mp0 is None:
            return
        
        df=self.timeseries.data
        ticks=self.timeseries.ticks
        
        vect=mapper(Point(cfg.MAGNET_DISTANCE,cfg.MAGNET_DISTANCE))-mp0
        vect=Point(abs(vect.x()),abs(vect.y()))
        cnt=0
        r=self.rawdtc
        for cnt in range(len(r)):
            diff=np.abs(ticks-r.cords[cnt].x)
            closest_index=np.argmin(diff)
            if diff[closest_index]<vect.x():
                magbar=df.iloc[closest_index] #magnetized bar
                prices=magbar.loc['o':'c'].to_numpy()
                diff=abs(prices-r.cords[cnt].y)
                closest_price=np.argmin(diff)
                                        
                if diff[closest_price]<vect.y():
                    r.set_cord(cnt,dtPoint(None, ticks[closest_index],prices[closest_price]))
                    self.set_dtc(r,force=True)

        return

    def removal(self):
        self.plt.subwindow.plt.sigTimeseriesChanged.disconnect(self.ts_change)
        self.plt.removeItem(self)

class DTrendLineDialog(uitools.DrawPropDialog): 
    initials=dict(uitools.DrawPropDialog.initials)
    levels=None
    def __init__(self,*args, tseries=None,dtc=dtCords().zero(),exec_on=True,**kwargs):
        super().__init__(*args, **kwargs)
        if exec_on==True: #to isolate the class variable from subclasses
            self.setup_extension()
        self.tseries=tseries
        self.dt,self.dts=[None,None],[None,None]
        self.dte=[None,None]
        self.dt[0]=dtc.cords[0].dt
        self.dts[0] = datetime.datetime.fromtimestamp(self.dt[0])
        self.dt[1]= dtc.cords[1].dt
        self.dts[1] = datetime.datetime.fromtimestamp(self.dt[1])
        self.yv0=dtc.cords[0].y
        self.yv1=dtc.cords[1].y
        
        label0=QtWidgets.QLabel('Datetime 1: ')
        self.dte[0]=QtWidgets.QDateTimeEdit()
        self.dte[0].setDateTime(self.dts[0])
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
        self.dte[1].setDateTime(self.dts[1])
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
    def dtc(self):
        return [[self.dt[0],None,self.yv0],[self.dt[1],None,self.yv1]]

    def setup_extension(self):
        if 'raydir' in self.item.props:
            self.state_dict['raydir']=self.__class__.raydir=self.item.props['raydir']
        
    def update_dt(self,i):
        self.dts[i]=self.dte[i].dateTime()
        self.dt[i]=self.dts[i].toSecsSinceEpoch()
    
    def update_item(self,**kwargs):
        try:
            self.item.set_dtc(self.dtc)
        except IndexError:
            chtl.simple_message_box(title="Timeseries error", 
                text="Timeseries data is unavailable.\nEnsure that the specified times are open market times.")
        return super().update_item(**kwargs)

class DrawSegment(DrawItem,pg.LineSegmentROI):
    def __init__(self,plt,coords=chtl.zero2P(),dialog=DTrendLineDialog, **kwargs):
        super().__init__(plt,dialog=dialog,**kwargs)
        super(DrawItem,self).__init__(coords)
        self.config_item()
        pen=dict(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.setPen(**pen)
        self.hoverPen=pg.functions.mkPen(**pen)
        pen['style']=self.style
       
        # self.sigRegionChanged.connect(self.line_move)
        self.plt.sigMouseOut.connect(self.magnetize)

    @property
    def rawdtc(self):
        s=self.getState()
        pos=dtPoint(None, *s['pos'])
        p1=dtPoint(None, *s['points'][0])
        p2=dtPoint(None, *s['points'][1])
        dtc=dtCords([p1,p2])+pos
        return dtc 
    
    def set_dtc(self,*args,**kwargs) -> bool:
        update_pos=super().set_dtc(*args,**kwargs)
        
        if update_pos:
            state=self.getState()
            state['pos']=Point(0,0)
            state['points']=self._dtc.get_raw_points()
            self.setState(state)

        return update_pos

    def mouse_update(self):
        if self.change:
            self.set_dtc(self.rawdtc)
            self.change=False
    
    def right_clicked(self,ev):#full override is simpler
        dtc=self.get_dtc()
        super().right_clicked(ev,tseries=self.timeseries,dtc=dtc)

    def left_clicked(self,ev):
        super().left_clicked(ev)

    # For use within shape() function, can be made @staticmethod if need be
    # Sets a mouse interaction area of width b around a line with coordinates a1 and a2
    def _shaper(self, p: QtGui.QPainterPath, a1,a2,b):
        p.moveTo(a1+b)
        p.lineTo(a2+b)
        p.lineTo(a2-b)
        p.lineTo(a1-b)
        p.lineTo(a1+b)

        return p

class DrawTrendLine(DrawSegment):
    def __init__(self, *args, ray=cfg.RAYDIR['r'], menu_name='Trend Line', clicks=2,**kwargs):
        super().__init__(*args, ray=ray, menu_name=menu_name, clicks=clicks,**kwargs)
        self._cached_pos=None
        self._drawpoints=None
        
    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, self._antialias)
        p.setPen(self.currentPen)
        
        # Get the endpoints of the line segment
        h1 = self.endpoints[0].pos()
        h2 = self.endpoints[1].pos()

        top,bot=self.calculate_intersections(h1,h2)

        self._drawpoints=self.ray_points(h1,h2,top,bot,self.raydir)

        # Draw the line segm
        # ent extended to the top and bottom axes
        p.drawLine(*self._drawpoints)
    @staticmethod
    def ray_points(h1, h2, top, bottom, ray) -> typing.List[Point]:
        def remove_duplicates(pts):
            res=[]
            for p in pts:
                if p not in res:
                    res.append(p)
            if len(res)==1:
                res*=2
            elif len(res)>2:
                res=res[:2]
            
            if len(res)!=2:
                raise ValueError("Ray points error")     
            
            return res
        
        if ray is None or ray == cfg.RAYDIR['n']:
            points= [h1, h2]
        
        elif ray == cfg.RAYDIR['b']:
            points= [top, bottom]
        
        elif ray == cfg.RAYDIR['r']:
            #Select 2nd and 4th elements
            right_xlist=sorted([h1.x(), h2.x(), top.x(), bottom.x()])[1::2]            
            points = [point for point in [h1, h2, top, bottom] if point.x() in right_xlist]
            if len(points)>2:
                points=remove_duplicates(points)
        
        elif ray == cfg.RAYDIR['l']:
            #Select 1st and 3d elements
            left_xlist=sorted([h1.x(), h2.x(), top.x(), bottom.x()])[::2]  
            points = [point for point in [h1, h2, top, bottom] if point.x() in left_xlist]
            if len(points)>2:
                points=remove_duplicates(points)
        
        else:
            raise ValueError(f"Invalid value for 'ray' argument. Must be one of: None or {cfg.RAYDIR.values()}.")
        
        return points

    def calculate_intersections(self, h1, h2):
        # Get the view rectangle
        viewRect = self.viewRect()
        top_left = viewRect.topLeft()
        bottom_right = viewRect.bottomRight()

        # Calculate the intersection points with the top and bottom axes
        if (delta:=h2.y()-h1.y())==0:
            top_intersection=Point(top_left.x(),h1.y())
            bottom_intersection=Point(bottom_right.x(), h2.y())
        else:
            top_intersection = Point(h1.x() + (h2.x() - h1.x()) * (top_left.y() - h1.y()) / delta, top_left.y())
            bottom_intersection = Point(h1.x() + (h2.x() - h1.x()) * (bottom_right.y() - h1.y()) / delta, bottom_right.y())

        return top_intersection, bottom_intersection
    
    def boundingRect(self):
        # Ensure viewRect cache clearance upon position change
        # otherwise rendering breaks
        pos=self.getState()['pos']
        if pos!=self._cached_pos:
            self._cached_pos=pos
            self.viewTransformChanged()

        return self.viewRect() # return self.shape().boundingRect()

    # Similar to InfiniteLine, prevent infinite loop scrolls
    def dataBounds(self, axis, frac=1.0, orthoRange=None):
        if axis == 0:
            return None   ## x axis should never be auto-scaled
        else:
            return (0,0)
    
    def shape(self):
        p = QtGui.QPainterPath()
    
        # Ensure mouse interactions over the entire painted shape
        h1 = self._drawpoints[0] if self._drawpoints else self.endpoints[0].pos()
        h2 = self._drawpoints[1] if self._drawpoints else self.endpoints[1].pos()
        dh = h2-h1
        if dh.length() == 0:
            return p
        pxv = self.pixelVectors(dh)[1]
        if pxv is None:
            return p
            
        pxv *= 4
        
        p.moveTo(h1+pxv)
        p.lineTo(h2+pxv)
        p.lineTo(h2-pxv)
        p.lineTo(h1-pxv)
        p.lineTo(h1+pxv)
      
        return p
    
    def set_props(self, props)-> None:
        super().set_props(props)
        if self.raydir:
            self.update_menu()

class DrawTriPointItem(DrawTrendLine):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,clicks=3,**kwargs)
        self.addFreeHandle(self.endpoints[0].pos())
    
    @property
    def rawdtc(self):
        s=self.getState()
        pos=dtPoint(None, *s['pos'])
        cords=[dtPoint(None,*xy) for xy in s['points']]
        if(len(cords))==2:
            cords.append(cords[0])
        assert len(cords)==3
        dtc=dtCords(cords)+pos
        return dtc
    
    # native override
    def setState(self, state):
        ROI.setState(self, state)
        p1 = [state['points'][0][0]+state['pos'][0], state['points'][0][1]+state['pos'][1]]
        p2 = [state['points'][1][0]+state['pos'][0], state['points'][1][1]+state['pos'][1]]
        self.movePoint(self.getHandles()[0], p1, finish=False)
        self.movePoint(self.getHandles()[1], p2, finish=False)
        #overridden section
        if len(self.getHandles())==3:
            p3 = [state['points'][2][0]+state['pos'][0], state['points'][2][1]+state['pos'][1]]
            self.movePoint(self.getHandles()[2], p3) 

class DChannelDialog(DTrendLineDialog):
    initials=dict(DTrendLineDialog.initials)
    initials['anchor_dt']=anchor_dt=None
    def __init__(self, *args, tseries=None,exec_on=False, dtc=dtCords.make(n=3).zero(), **kwargs):
        super().__init__(*args, tseries=tseries,dtc=dtc,exec_on=False, **kwargs)
        self.state_dict['anchor_dt']=self.__class__.anchor_dt
        self.setup_extension()
        self.dt.append(None)
        self.dts.append(None)
        self.dte.append(None)
        self.dt[2]=dtc.cords[2].dt
        self.dts[2] = datetime.datetime.fromtimestamp(self.dt[2])
        self.yv2=dtc.cords[2].y

        label0=QtWidgets.QLabel('Datetime 3: ')
        self.dte[2]=QtWidgets.QDateTimeEdit()
        self.dte[2].setDateTime(self.dts[2])
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

    @property
    def dtc(self):
         return [[self.dt[0],None,self.yv0],[self.dt[1],None,self.yv1],[self.dt[2],None,self.yv2]]

    def update_item(self, **kwargs):
        super().update_item(**kwargs)
        
class DChannelTabsDialog(uitools.TabsDialog):
    def __init__(self,plt,item=None,**kwargs):
        level_props=dict(desc_on=False,width=cfg.FIBOWIDTH,color=cfg.FIBOCOLOR,style=cfg.FIBOSTYLE)
        #set default color of levels at the foreground color
        level_props['color']=plt.graphicscolor
        super().__init__(DChannelDialog,plt,item=item,level_props=level_props,**kwargs)


class DrawChannel(DrawTriPointItem):
    def __init__(self,*args,levels=None,**kwargs):
        super().__init__(*args, dialog=DChannelTabsDialog, menu_name='Channel', **kwargs)
        level_props=dict(width=cfg.FIBOWIDTH,color=cfg.FIBOCOLOR,style=cfg.FIBOSTYLE)
        self.props['levels']=[]
        for lvl in [50.0]:
            self.props['levels'].append(dict(show=False,value=lvl,desc_on=False,removable=False,**level_props))
        #set metaprops in newly created (not saved) object
        if self.is_new and self.myref in self.mprops:
            self.props=dict(self.mprops[self.myref])
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

        self._drawpoints=[None,None]
        
    @property
    def levels(self):
        return self.props.get('levels',None)
    
    def paint(self,p,*args):
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, self._antialias)
        p.setPen(self.currentPen)
        
        # Get the endpoints of the line segment
        h1 = self.endpoints[0].pos()
        h2 = self.endpoints[1].pos()

        top,bot=self.calculate_intersections(h1,h2)

        self._drawpoints[0]=self.ray_points(h1,h2,top,bot,self.raydir)
        
        # Calculate draw points of the channel parallel
        h3 = self.endpoints[2].pos()
        h4=h2+h3-h1
        top,bot=self.calculate_intersections(h3,h4)
        self._drawpoints[1]=self.ray_points(h3,h4,top,bot,self.raydir)
    
        # Draw the line segm
        p.drawLine(*self._drawpoints[0])
        
        # Draw the parallel
        p.drawLine(*self._drawpoints[1])

        # Paint levels if they exist:
        if self.levels:
            for level in self.levels:
                if level['show']:
                    l1=self._drawpoints[0][0]+(self._drawpoints[1][0]-self._drawpoints[0][0])*(level['value']/100)
                    l2=self._drawpoints[0][1]+(self._drawpoints[1][1]-self._drawpoints[0][1])*(level['value']/100)
                    pen=pg.mkPen(color=level['color'],width=level['width'],style=cfg.LINESTYLES[level['style']])
                    p.setPen(pen)
                    p.drawLine(l1,l2)

    def shape(self):
        p = QtGui.QPainterPath()
    
        # Ensure mouse interactions over the entire painted shape
        h1 = self._drawpoints[0][0] if self._drawpoints[0] else self.endpoints[0].pos()
        h2 = self._drawpoints[0][1] if self._drawpoints[0] else self.endpoints[1].pos()
        dh = h2-h1
        if dh.length() == 0:
            return p
        pxv = self.pixelVectors(dh)[1]
        if pxv is None:
            return p
            
        pxv *= 4
        
        p=self._shaper(p,h1,h2,pxv)

        # Add parallel to the shape to enable mouse interactions with the parallel
        if self._drawpoints[1]:
            h1=self._drawpoints[1][0]
            h2=self._drawpoints[1][1]
            p=self._shaper(p,h1,h2,pxv)

        return p

class DrawPitchfork(DrawTriPointItem):
    def __init__(self, *args,**kwargs):
        super().__init__(*args, ray=None, menu_name='Pitchfork',
            dialog=lambda *args,**kwargs: DChannelDialog(*args,exec_on=True,**kwargs), 
            **kwargs)
        
        self._drawpoints=[None,None,None]

    def paint(self,p,*args):
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, self._antialias)
        p.setPen(self.currentPen)
        
        # Get the endpoints of the line segment
        h1 = self.endpoints[0].pos()
        h2 = self.endpoints[1].pos()
        h3 = self.endpoints[2].pos()

        midpoint=h2+(h3-h2)/2
        vector=midpoint-h1

        top,bot=self.calculate_intersections(h2,h2+vector)
        self._drawpoints[0]=self.ray_points(h2,h2+vector,top,bot,cfg.RAYDIR['r'])
        
        top,bot=self.calculate_intersections(h3,h3+vector)
        self._drawpoints[1]=self.ray_points(h3,h3+vector,top,bot,cfg.RAYDIR['r'])
    
        # Extend the midpoint to the view edge
        midpoint=self._drawpoints[0][1]+(self._drawpoints[1][1]-self._drawpoints[0][1])/2

        # Draw sidelines
        p.drawLine(*self._drawpoints[0])
        p.drawLine(*self._drawpoints[1])
        # Draw midline
        p.drawLine(h1,midpoint)
        self._drawpoints[2]=(h1,midpoint) # for reuse in shape
    
    def shape(self):
        p = QtGui.QPainterPath()

        # Ensure mouse interactions over the entire painted shape
        h1 = self._drawpoints[0][0] if self._drawpoints[0] else self.endpoints[0].pos()
        h2 = self._drawpoints[0][1] if self._drawpoints[0] else self.endpoints[1].pos()
        dh = h2-h1
        if dh.length() == 0:
            return p
        pxv = self.pixelVectors(dh)[1]
        if pxv is None:
            return p
            
        pxv *= 4
        
        p=self._shaper(p,h1,h2,pxv)

        # Add the other parallel and midline to the shape to enable mouse interactions with them
        if self._drawpoints[1]:
            h1=self._drawpoints[1][0]
            h2=self._drawpoints[1][1]
            p=self._shaper(p,h1,h2,pxv)
        # midline
        if self._drawpoints[2]:
            h1=self._drawpoints[2][0]
            h2=self._drawpoints[2][1]
            p=self._shaper(p,h1,h2,pxv)

        return p

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


def fibo_factory(base=DrawSegment,dialog=FiboTabsDialog, menu_name='Fibo',
                 preset_levels=(0.0,38.2,50.0,61.8,100.0)):

    class _Fibo(base):
        def __init__(self,*args,**kwargs):
            super().__init__(*args, dialog=dialog, ray=cfg.RAYDIR['n'], menu_name=menu_name,
                props=dict(width=cfg.FIBOLINEWIDTH,color=cfg.FIBOLINECOLOR,style=cfg.FIBOSTYLE),
                **kwargs)

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

            self.update_menu() # ensure meta props ray persistence
            
            self._cached_pos=None
            self.marks = [] #list of text labels of the the fibo levels
            self.sigRegionChanged.connect(self.update_marks)
            self.plt.vb.sigTransformChanged.connect(self.update_marks) # ensure correct pos init of marks on saved chart re-opening

        @property
        def levels(self):
            return self.props.get('levels',None)
        
        def boundingRect(self):
            # Ensure viewRect cache clearance upon position change
            # otherwise rendering breaks
            pos=self.getState()['pos']
            if pos!=self._cached_pos:
                self._cached_pos=pos
                self.viewTransformChanged()

            return self.viewRect() # return self.shape().boundingRect()

        # Similar to InfiniteLine, prevent infinite loop scrolls
        def dataBounds(self, axis, frac=1.0, orthoRange=None):
            if axis == 0:
                return None   ## x axis should never be auto-scaled
            else:
                return (0,0)

        def paint(self, p, *args):
            super().paint(p, *args)

            p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, self._antialias)
            p.setPen(self.currentPen)

            self.paint_levels(p)

        def paint_levels(self,p):
            p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, self._antialias)
            p.setPen(self.currentPen)

            if self.levels:
                for level in self.levels:
                    if level['show']:
                        l1,l2=self.get_level_values(level['value'])
                        pen=pg.mkPen(color=level['color'],width=level['width'],style=cfg.LINESTYLES[level['style']])
                        p.setPen(pen)
                        p.drawLine(l1,l2)

        def get_level_values(self,value):

            rect=self.viewRect()
            xleft=rect.topLeft().x()
            xright=rect.bottomRight().x()
            ray=self.raydir

            h1=self.endpoints[0].pos()
            h2=self.endpoints[1].pos()
            dx=abs(h2.x()-h1.x())
            xpos=min(h1.x(),h2.x())
            dy=h1.y()-h2.y()
            ypos=h2.y()

            x0=xpos-dx/2 if ray==cfg.RAYDIR['r'] or ray==cfg.RAYDIR['n'] else xleft 
            x1=xpos+3*dx if ray==cfg.RAYDIR['l'] or ray==cfg.RAYDIR['n'] else xright
            y0=ypos+dy*value/100
            y1=y0
            
            return Point(x0,y0),Point(x1,y1)
        
        def update_marks(self):
            xright=self.viewRect().bottomRight().x()
            pos=self.getState()['pos']

            marks=self.marks.copy()
            for level in self.levels:
                for mark in marks:
                    text=mark.toPlainText()
                    if text==level['desc']:
                        if level['show']:
                            v=self.get_level_values(level['value'])
                            markpos=Point(max(v[0].x(),min(v[1].x(),xright)),v[1].y())+pos
                            mark.setPos(markpos)
                        else:
                            self.marks.remove(mark)
                            self.plt.removeItem(mark)
                        break
                    # If the required mark is not found, set it up
                else:
                    if level['show']:
                        v=self.get_level_values(level['value'])
                        self.marks.append(mark:=pg.TextItem(text=level['desc'],color=level['color'],anchor=(1,0.75)))
                        mark.setParent(self)
                        mark.setScale(0.9)
                        markpos=Point(max(v[0].x(),min(v[1].x(),xright)),v[1].y())+pos
                        mark.setPos(markpos)
                        self.plt.addItem(mark)

        # Remove unused or hidden marks
        def clear_marks(self):
            marks=self.marks.copy()
            for mark in marks:
                for level in self.levels:
                    if mark.toPlainText()==level['desc']:
                        mark.setColor(level['color'])
                        break
                else:
                    self.marks.remove(mark)
                    self.plt.removeItem(mark)

        def set_props(self,props):
            super().set_props(props)
            self.update_menu()
            self.update_marks()
            self.clear_marks()

        def removal(self):
            for mark in self.marks:
                self.plt.removeItem(mark)
            return super().removal()
    
    return _Fibo

_DrawFibo=fibo_factory()
# Ensure that eval() works on re-opening of saved charts
class DrawFibo(_DrawFibo):
    pass

class FiboExtDialog(DTrendLineDialog):
    initials={'width': 1,'color': '#ff0000', 'style': cfg.DOTLINE}
    def __init__(self,*args,exec_on=False,dtc=dtCords.make(n=3).zero(),wname=None,**kwargs):
        super().__init__(*args,exec_on=False,dtc=dtc,**kwargs)
        self.__class__.initials['color']='red' #override
        self.setup_extension()
        self.dt.append(None)
        self.dts.append(None)
        self.dte.append(None)
        self.dt[2]=dtc.cords[2].dt
        self.dts[2] = datetime.datetime.fromtimestamp(self.dt[2])
        self.yv2=dtc.cords[2].y

        label0=QtWidgets.QLabel('Datetime 3: ')
        self.dte[2]=QtWidgets.QDateTimeEdit()
        self.dte[2].setDateTime(self.dts[2])
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
    def dtc(self):
        return [[self.dt[0],self.yv0],[self.dt[1],self.yv1],[self.dt[2],self.yv2]]

class FiboExtTabsDialog(uitools.TabsDialog):
    levels_props=dict(uitools.TabsDialog.level_props)
    def __init__(self,plt,item=None,**kwargs):
        level_props=dict(width=cfg.FIBOWIDTH,color=cfg.FIBOCOLOR,style=cfg.FIBOSTYLE)
        #set default color of levels at the foreground color
        level_props['color']=plt.graphicscolor
        super().__init__(FiboExtDialog,plt,wname='Fibonacci extensions',item=item,
            level_props=level_props,**kwargs)


_DrawFiboExt=fibo_factory(base=DrawTriPointItem,dialog=FiboExtTabsDialog, menu_name='Fibo Ext',
        preset_levels=(61.8,100.0,161.8))

class DrawFiboExt(_DrawFiboExt):
    
    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, self._antialias)
        p.setPen(self.currentPen)

        h1 = self.endpoints[0].pos()
        h2 = self.endpoints[1].pos()
        h3 = self.endpoints[2].pos()

        p.drawLine(h1,h2)
        p.drawLine(h2,h3)

        self.paint_levels(p)

    def get_level_values(self,value):

            rect=self.viewRect()
            xleft=rect.topLeft().x()
            xright=rect.bottomRight().x()
            ray=self.raydir

            h1=self.endpoints[0].pos()
            h2=self.endpoints[1].pos()
            h3=self.endpoints[2].pos()
            if h3==h1: h3=h2 # fixing animation on initial setup by mouse-clicks
            
            dx=abs(h3.x()-h1.x())
            xpos=h3.x()
            dy=h2.y()-h1.y()
            ypos=h3.y()

            x0=xpos-dx if ray==cfg.RAYDIR['r'] or ray==cfg.RAYDIR['n'] else xleft 
            x1=xpos+2*dx if ray==cfg.RAYDIR['l'] or ray==cfg.RAYDIR['n'] else xright
            y0=ypos+dy*value/100
            y1=y0
            
            return Point(x0,y0),Point(x1,y1)
    
    def shape(self):
        p = QtGui.QPainterPath()
    
        h1 = self.endpoints[0].pos()
        h2 = self.endpoints[1].pos()
        h3 = self.endpoints[2].pos()
        dh = h2-h1
        if dh.length() == 0:
            return p
        pxv = self.pixelVectors(dh)[1]
        if pxv is None:
            return p
            
        pxv *= 4
        
        p=self._shaper(p,h1,h2,pxv)
        p=self._shaper(p,h2,h3,pxv)

        return p

class DrawRuler(DrawSegment):
    def __init__(self, *args,**kwargs):
        super().__init__(*args, menu_name='Ruler', **kwargs)
        super().set_props(dict(color='r'))
        self.tag=pg.TextItem(text="Text",color='r',anchor=(0.5,1))
        self.plt.addItem(self.tag)

        self.sigRegionChanged.connect(self.ruler_tag)
        self.plt.vb.sigStateChanged.connect(self.ruler_tag)
        self.plt.vb.sigTransformChanged.connect(self.ruler_tag)

    def ruler_tag(self):
        state=self.getState()
        pos=state['pos']
        points=state['points']
        delta=points[1]-points[0]
        self.tag.setPos(pos+points[1])
        bars=int(delta[0]//self.timeseries.timeframe)
        pips=(delta[1])*chtl.to_pips(self.timeseries.symbol)
        self.tag.setText(f"Pips: {pips:.1f}\nBars: {str(bars)}")
    
    def set_props(self,props):
        if 'color' in props:
            self.tag.setColor(props['color'])
        return super().set_props(props)
    
    def item_hide(self,**kwargs):
        self.tag.hide()
        super().item_hide(**kwargs)
    
    def item_show(self):
        self.tag.show()
        super().item_show()

    def removal(self):
        self.plt.removeItem(self.tag)
        return super().removal()

# Draws items whose position is defined by pos and size
class DrawSimpleItem(DrawItem):
    def __init__(self,plt,coords=chtl.zero2P(),**kwargs):
        pos=coords[0]
        size=[coords[1][0]-coords[0][0],coords[1][1]-coords[0][1]]
        super().__init__(plt,dialog=uitools.DrawPropDialog,**kwargs)
        super(DrawItem,self).__init__(pos,size)
        self.config_item()
        pen=dict(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.setPen(**pen)
        self.hoverPen=pg.functions.mkPen(**pen)

    @property
    def rawdtc(self):
        s=self.getState()
        pos=dtPoint(None, *s['pos'])
        size=dtPoint(None, *s['size'])
        return dtCords([pos,pos+size])

    def set_dtc(self, *args,**kwargs):
        update_pos=super().set_dtc(*args,**kwargs)
        if update_pos:
            self.setPos(self._dtc.get_pos())
            self.setSize(self._dtc.get_size())
        
        return update_pos

    def right_clicked(self, ev,**kwargs):
        return super().right_clicked(ev,exec_on=True,**kwargs)
    
    def ts_change(self,ts):
        self.timeseries=ts
        self.set_dtc(dtPoint(ts=ts))
    
    def mouse_update(self):#override over segment rois
        if self.change:
            self.set_dtc(self.rawdtc)
            self.change=False

class DrawRectangle(DrawSimpleItem,pg.RectROI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, menu_name='Rectangle', **kwargs)    

class DrawEllipse(DrawSimpleItem,pg.EllipseROI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, menu_name='Ellipse', **kwargs) 
    
    def save_props(self):
        a=super().save_props()
        a['angle']=self.getState()['angle']
        return a
    
    def set_props(self, props):   
        if 'angle' in props:
            self.setAngle(props.pop('angle'))
        return super().set_props(props)

# InfiniteLine generic abstract class
class AltInfiniteLine(DrawProps,pg.InfiniteLine):
    def __init__(self,plt,*args,dockplt=None,dialog=uitools.DrawPropDialog,
        props=None,caller=None,**kwargs):
        super().config_props(plt.mwindow,props=props,caller=caller)
        super(DrawProps,self).__init__(*args,**kwargs)
        self.plt=plt if dockplt is None else dockplt
        self.color=self.plt.chartprops[cfg.foreground] if self.color is None else self.color
        pen=dict(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.setPen(**pen)
        self.hoverPen=pg.functions.mkPen(**pen)
        self.precision=self.plt.precision
        self.timeseries=plt.chartitem.timeseries
        self._dtp=dtPoint(ts=self.timeseries) # positional data object with dt attribute cached
        self.dialog=dialog
        self.raydir=self.props.get('raydir',None) 
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

    def mouse_update(self):
        raise NotImplementedError("mouse_update is not implemented")

    def mouse_dragged(self):
        try:
            self.mouse_update()
        except Exception:
            pass
    
    def get_dtc(self):
        '''
        Function serves as the single point of getting coordinates.
        Function returns dt and pos as a tuple
        '''
        c=dtPoint(None,*self.getPos()).fillnone(self._dtp) # sets dt from self._dtp instead of None
        
        return c

    def save_dtc(self):
        '''
        Function transforms get_dtc() into a JSON representation
        to save to disk
        '''
        
        return self.get_dtc().rollout()
    
    def set_dtc(self, dtpos, force=False) -> bool:
        '''
        Function serves as the single unified point of setting coordinates.
        Function accepts dtx and *pos as an unpacked tuple argument,
        and processes them depending on the number of args elements given.
        - sets position based on dtx of 1 or 3 pos args are given
        - sets dtx based on pos if 2 pos args are given
        - refreshes pos based on dtx where no args are given, eg. at timeseries change
        - processes JSON based saved data to restore position
        
        kwargs:
        - force: forces update of real position even where only raw coordinates (getPos()) are given.
        Default: False, to avoid updating real position where it is updated externally, eg. in __init__ or
        mouse_update().  Only attributes are updated and not the real position if only raw coordinates
        are given and force is False.

        Returns True if the real position is updated and False otherwise
        ''' 
        c=dtpos if type(dtpos) == dtPoint else dtPoint(*dtpos)
            
        self._dtp=self._dtp.apply(c) #update dtc

        # dont setPos solely based on getPos coords unless explicitly forced
        # to avoid idle setPos eg. on mouse_updates
        update_pos=(c.dt is not None or c.ts is not None) or force
        if update_pos:  
            self.setPos([self._dtp.x,self._dtp.y])

        return update_pos
    
    def mouse_area(self,x):
        x0=self.getPos()[0]
        if self.raydir==cfg.RAYDIR['n']:
            return False
        elif self.raydir==cfg.RAYDIR['r']:
            return True if x>=x0 else False
        elif self.raydir==cfg.RAYDIR['l']:
            return True if x<=x0 else False
        elif self.raydir==cfg.RAYDIR['b']:
            return True
        else:
            return True
    
    def yvalue(self,x):
        x0,y0=self.getPos()
        return y0 if self.angle==90 else y0+(x-x0)*math.tan(math.radians(self.angle))
    
    def xvalue(self,y):
        x0,y0=self.getPos()
        return x0 if self.angle==0 else x0+(y-y0)/math.tan(math.radians(self.angle))

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

    def magnetize(self) -> dtPoint|None:

        if not self.movable or not self.plt.mwindow.props['magnet']:
            return None
        
        mapper=lambda x: self.mapFromDevice(x)
        mp0=mapper(Point(0,0))
        if mp0 is None:
            return None
        
        df=self.timeseries.data
        ticks=self.timeseries.ticks

        pts=self.getPos()
        
        vect=mapper(Point(cfg.MAGNET_DISTANCE,cfg.MAGNET_DISTANCE))-mp0
        vect=Point(abs(vect.x()),abs(vect.y()))
        diff=np.abs(ticks-pts[0])#initialize minimum x axis distance from the base point
        closest_index=np.argmin(diff)
        if diff[closest_index]<vect.x():
            magbar=df.iloc[closest_index] #magnetized bar
            prices=magbar.loc['o':'c'].to_numpy()
            diff=np.abs(prices-pts[1])
            closest_price=np.argmin(diff) 
            if diff[closest_price]<vect.y():
                xy=dtPoint(None,int(ticks[closest_index]),prices[closest_price])
                self.set_dtc(xy,force=True)
                return xy
        return None #if xy is not returned, return None

    def removal(self):
        self.plt.removeItem(self)

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
        self.item.set_dtc(dtPoint(self.dtx))
        return super().update_item(**kwargs)
    
    def reset_defaults(self):
        super().reset_defaults()
        self.__class__.color = self.item.plt.foregroundcolor
        self.set_values()

class DrawVerLine(AltInfiniteLine):
    def __init__(self,plt,pos=[0,0],dialog=DVLineDialog,**kwargs):
        super().__init__(plt,pos,angle=90,dialog=dialog,**kwargs)
        self.context_menu=self.create_menu(description='Vertical Line')

        self.ay=self.plt.getAxis('right')
        self.textX = pg.TextItem(anchor=(0,1))
        self.textX.setParent(self)
        self.textX.setColor(self.color)
        self.set_dtc(self.get_dtc())
        self.refresh()
        self.plt.addItem(self.textX, ignoreBounds=True)

        self.plt.vb.sigStateChanged.connect(self.refresh)
        self.plt.subwindow.plt.sigTimeseriesChanged.connect(self.ts_change)

    def set_dtc(self, *args,**kwargs):
        r=super().set_dtc(*args,**kwargs)
        self.refresh()
        return r

    def mouse_update(self):
        self.set_dtc(dtPoint(None,*self.getPos()))

    def ts_change(self,ts):
        self.timeseries=ts
        self.set_dtc(dtPoint(ts=ts))

    # Refreshes the vertical line's text label.
    def refresh(self)-> None:
        ts=self.timeseries
        tf=ts.timeframe

        # get candle datetime in the current timeframe:
        # raw coords dpPoint applied to an empty dtPoint with the current timeseries
        c=dtPoint(ts=ts).apply(dtPoint(None,*self.getPos()))
        dtx = datetime.datetime.fromtimestamp(c.dt)
       
        y0=self.ay.range[0]    
        self.textX.setPos(c.x,y0)

        if tf>=cfg.PERIOD_D1:
            self.textX.setText(dtx.strftime("%d %b'%y"))
            self.textX.setFontSize(cfg.D_FONTSIZE)
        else:
            self.textX.setText(dtx.strftime("%d %b'%y %H:%M"))
            self.textX.setFontSize(cfg.D_FONTSIZE)
    
    def set_props(self, props):
        super().set_props(props)
        self.textX.setColor(self.color)
    
    def right_clicked(self,ev):
        super().right_clicked(ev,tseries=self.timeseries,dtxval=self.get_dtc().dt)
    
    def removal (self):
        self.plt.removeItem(self.textX)
        super().removal()

class DHLineDialog(DVLineDialog):
    initials=dict(DVLineDialog.initials)
    def __init__(self, *args, yval=0.0, **kwargs):
        super().__init__(*args, exec_on=False,**kwargs)
        self.setWindowTitle('Horizontal Line')
        self.state_dict['raydir']=self.__class__.raydir=self.item.raydir
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
        self.item.set_dtc(dtPoint(self.dtx,None,self.yv))
        return super(DVLineDialog,self).update_item(**kwargs) #equivalent to AltInfiniteLine.update_item()

class DrawHorLine(AltInfiniteLine):
    def __init__(self,plt,pos=[0,0],dialog=DHLineDialog,**kwargs):
        super().__init__(plt,pos,angle=0,dialog=dialog,**kwargs)
        self.target=None

        self.ax=self.plt.getAxis('bottom')
        self.textY = pg.TextItem(anchor=(1,0.75))
        self.textY.setParent(self)
        self.textY.setColor(self.color)
        self.textY.setFontSize(cfg.D_FONTSIZE)  

        # not required as init_magnetize happens to initialize self._dtp, but leave for reliability:
        self.set_dtc(self.get_dtc()) 
        self.refresh()
        self.movable=True
        self.plt.addItem(self.textY, ignoreBounds=True)

        self.plt.vb.sigStateChanged.connect(self.refresh)
        self.plt.subwindow.plt.sigTimeseriesChanged.connect(self.ts_change)
        if self.caller!='open_subw': #fast way to magnetize on initiation
            self.plt.sigMouseOut.connect(self.init_magnetize) 

    def set_dtc(self, *args,**kwargs):
        r=super().set_dtc(*args, **kwargs)
        self.refresh()
        return r

    def init_magnetize(self):
        self.mouse_update()
        self.plt.sigMouseOut.disconnect(self.init_magnetize)
    
    def mouse_update(self):
        
        dtpos=self.magnetize()
        if dtpos is None:
            self.set_dtc(dtPoint(None,self.plt.mapped_xy[0],self.get_dtc().y))
        
        if self.target is not None:
            self.target.setPos(self.getPos()) #to avoid y-axis de-synch with the line
        else:
            self.set_target()

    def ts_change(self,ts):
        self.timeseries=ts
        self.ax=self.plt.getAxis('bottom') #update axis on timeframe change
        self.set_dtc(dtPoint(ts=ts))

    # Refreshes the horizontal line's text label and target item.
    def refresh(self):
        c=self.get_dtc()
        if self.target is not None:
            self.target.setPos(c.x,c.y)
        else:
            self.set_target()
        x1=self.ax.range[1]
        self.textY.setPos(x1,c.y)
        self.textY.setText(f"{c.y:.{self.precision}f}")
    
    def set_target(self):
        clr=self.color
        self.target=TargetItem(movable=False,symbol='o',size=3,pen=clr,hoverPen=clr)
        self.target.setParent(self)
        self.target.setPos(*self.getPos())
        self.plt.addItem(self.target, ignoreBounds=True)
        
    def create_menu(self):
        context_menu=super().create_menu(description='Horizontal Line')
        self.raydir=cfg.RAYDIR['b'] if self.raydir is None else self.raydir
        self.ray_act=QtGui.QAction('Ray')
        self.ray_act.setCheckable(True)
        context_menu.insertAction(self.prop_act,self.ray_act)
        return context_menu
    
    def left_clicked(self, ev):
        evp=self.mapToView(ev.pos())
        if self.mouse_area(evp.x()):
            return super().left_clicked(ev)

    def right_clicked(self, ev,**kwargs):
        c=self.get_dtc()
        self.ray_act.setChecked(True if self.raydir==cfg.RAYDIR['r'] else False)
        super().right_clicked(ev,tseries=self.timeseries,dtxval=c.dt,
            yval=c.y,**kwargs)
        if self.maction == self.ray_act:
            if self.raydir!=cfg.RAYDIR['r']:
                self.raydir=cfg.RAYDIR['r']
                self.set_props(self.props)
            else:
                self.raydir=cfg.RAYDIR['b']
                self.set_props(self.props)
    
    def get_props(self):
        a=super().get_props()
        a['raydir']=self.raydir
        return a
    
    def set_props(self,props):
        super().set_props(props)
        self.target.setPen(self.color)
        self.target.setHoverPen(self.color)
        self.textY.setColor(self.color)
        self.raydir=props.get('raydir',cfg.RAYDIR['b'])

    def paint(self, p, *args):#override of the parent function
        if self.raydir is None:
            return super().paint(p, *args) #ordinary paint if no raydir is used
        
        if self.raydir==cfg.RAYDIR['n']: 
            return #no paint if neither direction
        
        if self.raydir==cfg.RAYDIR['r']:
            rgt=self._endPoints[1]
            self._endPoints=(0,rgt)

        elif self.raydir==cfg.RAYDIR['l']:
            lft=self._endPoints[0]
            self._endPoints=(lft,0)

        elif self.raydir==cfg.RAYDIR['b']:
            if not (self._endPoints[0] and self._endPoints[1]): #check whether any endpoint is 0
                self._computeBoundingRect() #if so, reset self._endPoints
        else:
            uitools.simple_message_box(text='Unrecognized ray direction',
                icon=QtWidgets.QMessageBox.Warning)
            #print(f'{self.raydir} Unrecognized ray direction')
        
        return super().paint(p, *args)

    def removal(self):
        self.plt.removeItem(self.textY)
        self.plt.removeItem(self.target)
        super().removal()


class DrawPolyLine(DrawSegment):
    def __init__(self,*args,**kwargs):
        super().__init__(*args, menu_name="Polyline", clicks=None,
                         dialog=lambda *a,**k: uitools.DrawPropDialog(*a,exec_on=True,**k), 
                         **kwargs)
        if self.is_new:
            self.plt.scene().sigMouseClicked.connect(self.completion)

    @property
    def rawdtc(self):
        s=self.getState()
        pos=dtPoint(None, *s['pos'])
        cords=[dtPoint(None,*xy) for xy in s['points']]
        dtc=dtCords(cords)+pos
        return dtc

    def completion(self,ev):
        if ev.button()==QtCore.Qt.MouseButton.RightButton:
            self.set_dtc(self.rawdtc) # refresh dt coordinates
            self.plt.scene().sigMouseClicked.disconnect(self.setup_mouseclicks)
            self.plt.scene().sigMouseMoved.disconnect(self.setup_mousemoves)
            self.plt.scene().sigMouseClicked.disconnect(self.completion)
            self.is_new=False
            self.translatable=True
            self.setSelected(True)

    # native override
    def setState(self, state):
        if len(self.getHandles())==2:
            super().setState(state)
        else:
            ROI.setState(self, state)
            for i,v in enumerate(self.getHandles()[:-1]):
                p = [state['points'][i][0]+state['pos'][0], state['points'][i][1]+state['pos'][1]]
                self.movePoint(v, p, finish=False)
   
            p = [state['points'][-1][0]+state['pos'][0], state['points'][-1][1]+state['pos'][1]]
            self.movePoint(self.getHandles()[-1], p) 
    
    def set_dtc(self, dtc, **kwargs):
        
        if type(dtc) in (dtCords,list):
            l=len(dtc)
            assert (l>=len(self.getHandles())), "argument length is too short in set_dtc()"

            # Adds new segments on mouse clicks and on saved re-open
            if l>2 and l>len(self.getHandles()):
                l-=len(self.getHandles())
                xy=self.endpoints[-1].pos()
                # apply() order is important, adds timeseries and then calculates dt on the basis of xy
                new_segments_dtc=dtCords.make(n=l).apply(dtPoint(ts=self.timeseries).apply(dtPoint(None,*xy)))         
                self._dtc.adjoin(new_segments_dtc) 
                for _ in range(l):
                    self.addFreeHandle(xy)

        return super().set_dtc(dtc, **kwargs)
    
    def paint(self, p, *args):
        p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, self._antialias)
        p.setPen(self.currentPen)

        points = [ep.pos() for ep in self.endpoints]  # Extract positions of endpoints

        if points:  # Check if there are any points
            p.drawPolyline(points)

    def shape(self):
        p = QtGui.QPainterPath()
    
        # Ensure mouse interactions over the entire painted shape
        h1 = self.endpoints[0].pos()
        h2 = self.endpoints[1].pos()
        dh = h2-h1
        if dh.length() == 0:
            return p
        pxv = self.pixelVectors(dh)[1]
        if pxv is None:
            return p
            
        pxv *= 4
        
        p.moveTo(h1+pxv)
        p.lineTo(h2+pxv)
        p.lineTo(h2-pxv)
        p.lineTo(h1-pxv)
        p.lineTo(h1+pxv)
      
        if len(self.endpoints)>2:
            for i, ep in enumerate(self.endpoints[1:-1]):
                h1=ep.pos()
                h2=self.endpoints[i+2].pos() # next endpoint after ep, i+2 because the list is sliced 
                p=self._shaper(p,h1,h2,pxv)

        return p
    
    def right_clicked(self,ev):
        if not self.is_new:
            return DrawItem.right_clicked(self,ev)

class DrawArrow(DrawSegment):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,menu_name="Arrow",**kwargs)
        self.setPen(width=self.width,color=self.color,style=cfg.LINESTYLES[self.style])
        self.arrow=pg.ArrowItem(angle=self.ang, tipAngle=30, baseAngle=-30, headLen=10, 
            tailLen=None, brush=self.arcolor, pen={'width':self.width,'color':self.arcolor})
        self.arrow.setPos(*self.rawdtc.get_raw_points()[1])
        self.plt.addItem(self.arrow)

        self.sigRegionChanged.connect(self.arrow_refresh)
        self.plt.vb.sigStateChanged.connect(self.arrow_refresh)
        self.plt.vb.sigTransformChanged.connect(self.arrow_refresh)

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
        self.arrow.setPos(*self.rawdtc.get_raw_points()[1])
        self.arrow.setStyle(angle=self.ang)
    
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
        self.arrow.setPos(*self.rawdtc.get_raw_points()[1])
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
        self.lct=self.plt.lc_thread
        self.pre=chtl.precision(self.plt.chartitem.symbol)
        
        try: self.refresh()
        except Exception: pass

        if self.lct is not None:
            self.lct.sigLastCandleUpdated.connect(self.refresh_lc)
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

        if self.lct is not None:
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
        self.lc_thread=NewThread(self,symbol=ci.symbol,timeframe=ci.timeframe)
        self.lc_thread.start()
        self.lc_thread.sigLastCandleUpdated.connect(self.redraw_lc)
        self.lc_thread.sigInterimCandlesUpdated.connect(self.append_inc)            
    
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
            no_draw_hit=True #unselect draw items if clicked to empty space
            if self.hovered_items is not None:
                for itm in self.hovered_items:
                    if chtl.item_is_draw(itm):
                        no_draw_hit=False
                        break
            if no_draw_hit:
                for itm in self.listItems():
                    if hasattr(itm,"is_draw") and itm.is_draw is True:
                        itm.set_selected(False)
        else:
            mapped_xy=Point(self.vb.mapSceneToView(mouseClickEvent.scenePos()))
            for dk in self.subwindow.docks:
                dockplt=dk.widgets[0]
                if dockplt is not self:
                    dockplt.draw_mode=None
                    if issubclass(self.draw_mode,AltInfiniteLine):
                        dockplt.item_in_progress.removal()
                        dockplt.item_in_progress=None            
    
            if issubclass(self.draw_mode,pg.ROI) or hasattr(self.draw_mode,'multiclick'): #items requiring 2 or more clicks - for initiation and finalisation
                xy=[mapped_xy,mapped_xy]
                itm=self.draw_mode(self.subwindow.plt,xy,dockplt=self,caller='mouse_clicked')
                self.draw_mode=None
            else: #items requiring only 1 click
                self.item_in_progress=None
                self.draw_mode=None
        
    def mouse_moved(self, mouseMoveEvent):
        self.mapped_xy=Point(self.vb.mapSceneToView(mouseMoveEvent))
        if self.draw_mode!=None: 
            if isinstance(self.item_in_progress, AltInfiniteLine):
                self.item_in_progress.removal()
                self.item_in_progress=self.draw_mode(self,self.mapped_xy)
                self.addItem(self.item_in_progress)
    
    def mouse_hover(self, items):
        self.hovered_items=list(items)

    def draw_act(self, action):
        self.draw_mode=action
        if issubclass(self.draw_mode, AltInfiniteLine):
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
                        points=itm.get_dtc().get_raw_points()[:2]
                        newitm=DrawTrendLine(self,coords=points)
                    elif isinstance(itm,DrawPitchfork):
                        xy=itm.get_dtc().get_raw_points()
                        points=(Point(*xy[0]),Point(*xy[1])+(Point(*xy[2])-Point(*xy[1]))/2)
                        newitm=DrawTrendLine(self,coords=points)
                        newitm.props['raydir']=cfg.RAYDIR['r']
                    else:
                        newitm=itm.__class__(self)
                        try:newitm.set_dtc(itm.save_dtc())
                        except Exception:pass
                else:
                    newitm=itm.__class__(self)
                    try:newitm.set_dtc(itm.save_dtc())
                    except Exception:pass

                self.addItem(newitm)
                try:
                    props=itm.save_props()
                    if isinstance(itm, DrawPitchfork) and isinstance(newitm,DrawTrendLine):
                        props['raydir']=cfg.RAYDIR['r']
                    newitm.set_props(props)
                except Exception:
                    pass
                vr=self.viewRange()
                rn=[x*cfg.COPY_DIST for x in [vr[0][1]-vr[0][0],vr[1][1]-vr[1][0]]]
                newitm.translate(0,rn[1],None)
  
    def select_all_act(self):
        for itm in self.listItems():
            if hasattr(itm,"is_persistent") and itm.is_persistent and hasattr(itm,"is_draw") and itm.is_draw:
                itm.set_selected(True)

    def deselect_all_act(self):
        for itm in self.listItems():
            if hasattr(itm, "is_persistent") and itm.is_persistent and hasattr(itm,"is_draw") and itm.is_draw:
                itm.set_selected(False)

    def delete_act(self):
        for itm in self.listItems():
            if isinstance(itm,DrawItem): 
                if itm.is_persistent and itm.translatable:
                    itm.item_hide(persistence_modifier=False)
            elif isinstance(itm,AltInfiniteLine): 
                if itm.is_persistent and itm.movable:
                    itm.item_hide(persistence_modifier=False)
            elif isinstance(itm,DrawProps) and itm.is_persistent and hasattr(itm, "is_selected") and itm.is_selected:
                itm.item_hide(persistence_modifier=False)

    def undo_act(self):
        for itm in self.listItems():
            if isinstance(itm,DrawProps) and not itm.isVisible() and hasattr(itm,"parent") and itm.parent() is None:
                itm.item_replicate()
                itm.removal()
            elif hasattr(itm,"multiclick") and not itm.isVisible():
                itm.item_show()

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
        if self.chartitem is not None and self.lc_thread.lc is not None:
            ts=self.chartitem.timeseries
            ts.update_ts(self.lc_thread.lc)
            self.lc_item=self.redraw_chartitem(self.lc_item,start=-1)

    def append_inc(self):
        if self.chartitem!=None and self.lc_thread.incs!=None:
            # passed from NewThread's self.incs, [:-1] to ignore last candle 
            # and leave for consideration interims only (typically a single candle):
            interim_candles=self.lc_thread.incs['data'][:-1]
            self.chartitem.timeseries.update_ts(dict(data=interim_candles,complete=None))
            self.chartitem=self.redraw_chartitem(self.chartitem)
            
    def symb_change(self):
        symb=self.eline.text().strip().upper() #strip of spaces and capitalize
        fetch=self.mwindow.fetch

        if isinstance(fetch,FetcherMT5):
            symb=fetch.get_best_symbol_match(symb)
        
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
    sigInterimCandlesUpdated=QtCore.Signal()
    def __init__(self,plt,symbol=cfg.D_SYMBOL,timeframe=cfg.D_TIMEFRAME,*args,**kwargs) -> None:
        super().__init__(*args,**kwargs)
        self.sb=symbol
        self.tf=timeframe
        self.incs=None
        self.plt=plt
        self.subwindow=self.plt.subwindow
        self.mwindow=self.plt.mwindow
        self.fetch=self.mwindow.fetch
        self.tmr=self.mwindow.props['timer']
        self.session=self.mwindow.session
        self.lc=self.get_lc()
        self.prev_lc=self.lc
        #to ensure no candle data loss on initiation:
        self.data_request()
    
    def get_lc(self):
        return self.fetch.fetch_lc(self.session,self.sb,self.tf)

    def lc_has_changed(self):
        # if both lc and previous lc are None, then return False
        if self.lc is None and self.prev_lc is None:
            return False
        # if one of self.lc or self.prev_lc is None and the other is not, return True
        elif not (self.lc and self.prev_lc):
            return True
        
        # if both lc and previos lc are not None, continue:
        if self.lc['complete']!=self.prev_lc['complete']:
            return True
        
        if self.lc['data'].equals(self.prev_lc['data']):
            return False
        else:
            return True

    def data_request(self):
        self.lc=self.get_lc()
        if self.lc_has_changed():
            if self.lc is not None:
                lct=self.lc['data'].t.iloc[-1]
                if self.prev_lc is None:
                    self.prev_lc=self.lc
                else:
                    prev_lct=self.prev_lc['data'].t.iloc[-1]
                    if lct>prev_lct:
                        self.prev_lc=self.lc                
                        todt=int(time.time())
                        self.incs=self.fetch.fetch_data(session=self.session, symbol=self.sb,fromdt=prev_lct,todt=todt,
                                timeframe=self.tf)
                        if self.incs!=None:
                            self.sigInterimCandlesUpdated.emit()
            self.sigLastCandleUpdated.emit()

    #override
    def run(self):
        def dr():
            self.data_request()
                       
        # def closure():
        #     if hasattr(self,'timer'):
        #         self.timer.stop() #stop QTimer
        #     self.quit() #quit QThread

        # This formulation of closure() avoids inter-thread conflicts and related warnings:
        def closure():
            if hasattr(self,'timer'):
                from PySide6.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(self.timer, "stop", Qt.ConnectionType.AutoConnection)
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

