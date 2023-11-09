import PySide6
from PySide6 import QtWidgets,QtCore,QtGui
import pyqtgraph as pg
from pyqtgraph.dockarea import *
import json, requests, os, datetime

import api #be sure to leave it for eval() purposes
import cfg
import timeseries as tmss, timeseries
from qtd_proto import Ui_MainWindow
import drawings as drws, drawings
import charttools as chtl,charttools
import uitools
import studies as stds, studies
import labelings as lbls,labelings
import fetcher as ftch,fetcher
import styles

import overrides as ovrd, overrides

from _debugger import *

APW=drws.AltPlotWidget

class AltSubWindow(QtWidgets.QMdiSubWindow):
    sigAltSubWindowClosing=QtCore.Signal()
    def __init__(self, plt=None,profiles=[cfg.D_PROFILE]):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon(f'{cfg.CORE_ICON}'))
        self.plt=plt
        self.is_persistent=True
        self.profiles=profiles
        self.delete_from_profile=True
        self.dock_area=DockArea()
        self.setWidget(self.dock_area)
        self.docks=[]
        self.docks.append(Dock('0'))
        self.docks[0].hideTitleBar()
        self.dock_area.addDock(self.docks[0],'bottom')
        if plt is not None:
            self.set_plot(self.plt)
        self.windowStateChanged.connect(self.mbw_change)

    #workaround to address maximized buttons illigebility in "Darker"
    def mbw_change(self): 
        mbw=self.maximizedButtonsWidget()
        if mbw is not None and self.plt.mwindow.props['theme']=='Darker':
            mbw.setStyleSheet("background-color: "+styles.darker_mbw)    

    def set_plot(self,plt):
        self.plt=plt
        self.docks[0].addWidget(plt)
        self.docks[0].setStretch(self.size().width(),self.size().height())
        if len(self.docks)>1:
            i=1
            for dk in self.docks[1:]:
                self.process_dock(dk,'bottom',self.docks[i-1])
                i+=1

    def add_plot(self):
        ln=len(self.docks)
        self.docks.append(Dock(str(ln)))
        self.docks[ln].setStretch(self.size().width(),self.size().height()*cfg.D_DOCKHEIGHT)
        self.process_dock(self.docks[-1])
    
    def remove_plot(self,dockplt):
        dkplt=dockplt.parent().parent()#dockplt's dock
        self.docks.remove(dkplt)
        dkplt.close()#close the dock window

    def process_dock(self,dk, prev_dk=None):
        prev_dk=self.docks[-2] if prev_dk is None else prev_dk
        dockplt=drws.AltPlotWidget(mwindow=self.plt.mwindow,subwindow=self,
            chartitem=self.plt.chartitem,chartprops=dict(self.plt.chartprops))                
        dk.addWidget(dockplt)
        self.dock_area.addDock(dk,'bottom',prev_dk)
        dk.hideTitleBar()
        dockplt.vb.setXLink(self.plt.vb)
        dockplt.getAxis('bottom').hide()

    def close(self,delete_from_profile=True):
        self.delete_from_profile=delete_from_profile
        super().close()

    def closeEvent(self,event):
        self.sigAltSubWindowClosing.emit()
        mwindow=self.plt.mwindow
        if self.delete_from_profile==True:
            ap=mwindow.profiles[0]
            if cfg.DELETED_PROFILE not in self.profiles:
                self.profiles.append(cfg.DELETED_PROFILE)
            self.profiles.remove(ap)
        else:
            self.delete_from_profile==True
        
        if self.profiles==[]:
                for record in mwindow.pstate:
                    if record['subwindow plotID']==self.plt.plotID:
                        mwindow.pstate.remove(record)
        else:
            mwindow.save_subw_states(subwindow=self)
                    
        self.mdiArea().removeSubWindow(self)
        return super().closeEvent(event)

class EntryLine(QtWidgets.QMdiSubWindow):
    def __init__(self,area, text=None) -> None:
        super().__init__()
        self.area=area
        self.is_persistent=False
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        widget=QtWidgets.QWidget()
        self.eline=QtWidgets.QLineEdit()
        self.eline.setPlaceholderText(text)
        layout=QtWidgets.QGridLayout()
        widget.setLayout(layout)
        layout.addWidget(self.eline,0,0)
        self.setWidget(widget)

class MDIWindow(QtWidgets.QMainWindow):
    sigMainWindowClosing=QtCore.Signal()
    sigMainWindowVariablesUpdate=QtCore.Signal() #signal accross all subws such as Experts on/off
    sigAcctDataChanged=QtCore.Signal()
    sigEscapePressed=QtCore.Signal()
    def __init__(self,profiles=cfg.D_PROFILES,application=None,fetch=None):
        super().__init__()
        self.pstate=[] #total record of all plots (state of profiles)
        self.profiles=profiles
        self.props=cfg.D_METAPROPS
        self.app=application
        self.fetch=fetch
        self.sigAcctDataChanged.connect(self.fetch.reload_acct)

    #UI initialization       
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.mdi = QtWidgets.QMdiArea()
        self.setCentralWidget(self.mdi)
        self.mdi.setActivationOrder(QtWidgets.QMdiArea.ActivationHistoryOrder)
        self.palet=self.app.palette()
        self.set_theme() #sets default theme on first launch

        self.session=requests.Session()
       
        #initialise internet connection status message       
        self.message_connection_status=QtWidgets.QLabel()
        self.message_connection_status.setText(cfg.NO_CONNECTION_MESSAGE)
        self.ui.statusbar.addWidget(self.message_connection_status)       
        self.fetch.sigConnectionStatusChanged.connect(self.connection_status)

        # self.sc_copy_item = QtWidgets.QShortcut(QtWidgets.QKeySequence('Ctrl+C'), self)
        # self.sc_copy_item.activated.connect(self.copy_item_act)

        # self.sc_select_all = QtWidgets.QShortcut(QtWidgets.QKeySequence('Ctrl+A'), self)
        # self.sc_select_all.activated.connect(self.select_all_act)

        # self.sc_deselect_all = QtWidgets.QShortcut(QtWidgets.QKeySequence('Esc'), self)
        # self.sc_deselect_all.activated.connect(self.deselect_all_act)

        # self.sc_delete = QtWidgets.QShortcut(QtWidgets.QKeySequence('Del'), self)
        # self.sc_delete.activated.connect(self.delete_act)
    
        # self.sc_undo = QtWidgets.QShortcut(QtWidgets.QKeySequence('Ctrl+Z'), self)
        # self.sc_undo.activated.connect(self.undo_act)

        def click_action(func,*args,**kwargs): 
            aw=self.mdi.activeSubWindow()
            if aw is None:
                return None
            elif hasattr(aw,'plt'):
                apt=aw.plt
                return func(apt,*args,**kwargs)
            else:
                return None 
        #File
        self.ui.actionNew.triggered.connect(lambda *args: self.window_act("New"))
        self.ui.actionOpen.triggered.connect(lambda *args: self.window_act('Open'))
        self.ui.actionSave_As.triggered.connect(lambda *args: self.window_act('Save As'))
        self.ui.actionOffline.triggered.connect(lambda *args: self.window_act('Offline'))
        self.ui.actionLogin.triggered.connect(lambda *args: self.window_act('Login'))
        #Edit
        self.ui.actionCopy.triggered.connect(self.copy_item_act)
        self.ui.actionCopy_Line.triggered.connect(lambda *args: self.copy_item_act(copyline=True))
        self.ui.actionSelect_All.triggered.connect(self.select_all_act)
        self.ui.actionDeselect.triggered.connect(self.deselect_all_act)
        self.ui.actionDelete.triggered.connect(self.delete_act)
        self.ui.actionUndo_Delete.triggered.connect(self.undo_act)
        #Chart
        self.ui.actionPrice_Line.triggered.connect(lambda *args: click_action(APW.priceline_act))
        self.ui.actionSymbol.triggered.connect(lambda *args: self.window_act("Symbol"))
        self.ui.actionDescription.triggered.connect(lambda *args: self.window_act("Description"))
        self.ui.actionTimeframe.triggered.connect(lambda *args: self.window_act("Timeframe"))
        self.ui.actionGrid.triggered.connect(lambda *args: click_action(APW.grid_act))
        self.ui.actionRefresh.triggered.connect(lambda *args: self.window_act('Refresh'))
        self.ui.actionChartProperties.triggered.connect(lambda *args: click_action(uitools.ChartPropDialog))
        #Insert
        self.ui.actionAverage_True_Range.triggered.connect(lambda *args:click_action(stds.ATRDialog))
        self.ui.actionBollinger_Bands.triggered.connect(lambda *args:click_action(stds.BBDialog))
        self.ui.actionMACD.triggered.connect(lambda *args: click_action(stds.MACDDialog))
        self.ui.actionMoving_Average.triggered.connect(lambda *args: click_action(stds.MADialog))
        self.ui.actionRelative_Strength_Index.triggered.connect(lambda *args: click_action(stds.RSITabsDialog))
        self.ui.actionStochastic.triggered.connect(lambda *args: click_action(stds.StochTabsDialog))
        #Tools
        self.ui.actionUser_Apps.triggered.connect(lambda *args: uitools.TreeSubWindow.__call__(self))
        self.ui.actionHistory.triggered.connect(lambda *args: self.window_act('History'))
        self.ui.actionSettings.triggered.connect(lambda *args: uitools.SettingsDialog.__call__(self))
        #Window
        self.ui.actionTile.triggered.connect(lambda *args: self.window_act("Tile"))
        self.ui.actionCascade.triggered.connect(lambda *args: self.window_act("Cascade"))
        self.ui.actionTabbed_View.triggered.connect(lambda *args: self.window_act("TabbedView"))
        self.ui.actionStatus_Bar.triggered.connect(lambda *args: self.window_act("StatusBar"))
        self.ui.actionAbout.triggered.connect(lambda *args: self.window_act("About"))
        self.ui.actionLicense.triggered.connect(lambda *args: self.window_act("License"))

    #Accessories   
        self.ui.actionCrossHair.triggered.connect(lambda *args: click_action(APW.cross_hair))
        self.ui.actionExport.triggered.connect(lambda *args: self.window_act('Export'))
        self.ui.actionMagnet.triggered.connect(lambda *args: self.window_act('Magnet'))

    #Experts
        self.ui.actionExperts.triggered.connect(lambda *args: self.window_act('Experts'))

    #CBL chartitem
        self.ui.actionBarChart.triggered.connect(lambda *args: self.window_act("Bar"))
        self.ui.actionCandleChart.triggered.connect(lambda *args: self.window_act("Candle"))
        self.ui.actionLineChart.triggered.connect(lambda *args: self.window_act("Line"))
    #Timeframes
        self.ui.actionMN.triggered.connect(lambda *args: self.window_act("MN"))
        self.ui.actionW1.triggered.connect(lambda *args: self.window_act("W1"))
        self.ui.actionD1.triggered.connect(lambda *args: self.window_act("D1"))
        self.ui.actionH4.triggered.connect(lambda *args: self.window_act("H4"))
        self.ui.actionH1.triggered.connect(lambda *args: self.window_act("H1"))
        self.ui.actionM30.triggered.connect(lambda *args: self.window_act("M30"))
        self.ui.actionM15.triggered.connect(lambda *args: self.window_act("M15"))
        self.ui.actionM5.triggered.connect(lambda *args: self.window_act("M5"))
        self.ui.actionM1.triggered.connect(lambda *args: self.window_act("M1"))

        self.combo_tf=QtWidgets.QComboBox()
        self.ui.toolBarForTimeframes.addWidget(self.combo_tf)
        self.combo_tf.insertItems(1,["MN","H12","H8","H6","H3","H2","M10","M4","M2"])
        self.combo_tf.insertSeparator(1)
        self.combo_tf.insertSeparator(7)
        self.combo_tf.activated.connect(lambda *args: self.window_act(self.combo_tf.currentText()))        
    #Drawings and other
        self.ui.actionDrawTrendLine.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawTrendLine))
        self.ui.actionDrawVerLine.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawVerLine))
        self.ui.actionDrawHorLine.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawHorLine))
        self.ui.actionDrawChannel.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawChannel))
        self.ui.actionDrawPitchfork.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawPitchfork))
        self.ui.actionDrawFibo.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawFibo))
        self.ui.actionDrawFiboExt.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawFiboExt))
        self.ui.actionDrawEllipse.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawEllipse))
        self.ui.actionDrawRectangle.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawRectangle))
        self.ui.actionElliott_Impulse.triggered.connect(lambda *args: click_action(APW.draw_act,lbls.DrawElliottImpulse))
        self.ui.actionElliott_Correction.triggered.connect(lambda *args: click_action(APW.draw_act,lbls.DrawElliottCorrection))
        self.ui.actionElliott_Extended_Correction.triggered.connect(lambda *args: click_action(APW.draw_act,lbls.DrawElliottExtendedCorrection))
        self.ui.actionDraw_Text.triggered.connect(lambda *args:click_action(lbls.DrawText,caller='click_action'))
        self.ui.actionDraw_Label.triggered.connect(lambda *args:click_action(lbls.DrawLabel,caller='click_action'))
        self.ui.actionDrawPolyline.triggered.connect(lambda *args:click_action(APW.draw_act,drws.DrawPolyLine))
        self.ui.actionDrawArrow.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawArrow))
        self.ui.actionDrawPolyArrow.triggered.connect(lambda *args: click_action(APW.draw_act,drws.DrawPolyArrow))

        self.ui.actionEmpty_Profile_Bin.triggered.connect(self.empty_profile_bin)

    #Restore
        try:
            with open(cfg.DATA_STATES_DIR+cfg.WINDOW_STATE_FLNM,'r') as fwin:
                wind=fwin.read()
                wind=json.loads(wind)
                self.resize(*wind['window size'])
                self.move(*wind['window position'])
                prfs=wind['profiles'] #to ensure [default] and [deleted] are intact
                if len(prfs)>1:
                    self.profiles=prfs
                props=wind['props'] 
                self.props=props #props need to be assigned before subwindows to ensure that non-item props (like magnet)
                                    #are available before when subwindows are processed
                if 'Offline' in self.props:
                    self.fetch.offline_mode=self.props['Offline']
                #hide hidden toolbars/status bar
                self.widgets_init()
                self.set_theme()
                #--------------------
                with open(cfg.DATA_STATES_DIR+cfg.PROFILE_STATE_FLNM, 'r') as fpr:
                    ps=fpr.read()
                    ps=json.loads(ps)
                    if isinstance(ps,list):
                        self.pstate=ps
                    self.open_subw(self.pstate)
                #--------------------
                for key,val in props.items():# item props need to be processed after subwindows 
                                                #to ensure that they are not reset by the subwindows
                    if isinstance(val,dict):
                        for wd in props[key]:
                            try:
                                eval(key).props[wd]=props[key][wd]
                            except Exception:
                                pass
        except Exception:
            pass

    #Toggles
        if 'magnet' in self.props and self.props['magnet'] is True:
            self.ui.actionMagnet.setChecked(True)
        if 'experts_on' in self.props and self.props['experts_on'] is True:
            self.ui.actionExperts.setChecked(True)
        if 'tabbed_view' in self.props and self.props['tabbed_view'] is True:
            self.ui.actionTabbed_View.setChecked(True)
            self.toggle_tabbed_view(True)
        if 'hidden' in self.props and self.ui.statusbar.objectName() in self.props['hidden']:
            self.toggle_status_bar(False)
        else:
            self.toggle_status_bar(True)
        if 'Offline' in self.props and self.props['Offline'] is True:
            self.ui.actionOffline.setChecked(True)

    #Profiles
        #add profile
        self.profile_eline=QtWidgets.QLineEdit()
        self.profile_eline.setFrame(True)
        self.add_profile=QtWidgets.QWidgetAction(None)
        self.add_profile.setDefaultWidget(self.profile_eline)
        self.ui.menuAdd_Profile.addAction(self.add_profile)
        self.profile_eline.returnPressed.connect(lambda *args: self.add_profile_func(self.profile_eline.text()))
        #set profile
        self.set_box=QtWidgets.QComboBox()
        self.set_box.insertItems(1,self.profiles)
        self.set_box.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.set_pract=QtWidgets.QWidgetAction(None) 
        self.set_pract.setDefaultWidget(self.set_box)
        self.ui.menuSet_Profile.addAction(self.set_pract)
        self.set_box.activated.connect(lambda *args: self.set_profile_func(self.set_box.currentText()))

        self.set_box1=QtWidgets.QComboBox()
        self.set_box1.insertItems(1,self.profiles)
        self.set_box1.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.ui.toolBarForAccessories.addWidget(self.set_box1)
        self.set_box1.activated.connect(lambda *args: self.set_profile_func(self.set_box1.currentText()))
        self.set_box1.setToolTip('Profiles')
        
        #add/restore chart to profile
        self.chart_to_profile_box=QtWidgets.QComboBox()
        self.chart_to_profile_box.insertItems(1,self.ch_profiles())
        self.chart_to_profile_box.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.chtop_pract=QtWidgets.QWidgetAction(None) 
        self.chtop_pract.setDefaultWidget(self.chart_to_profile_box)
        self.ui.menuAdd_Restore_Chart_to_Profile.addAction(self.chtop_pract)
        self.chart_to_profile_box.activated.connect(lambda *args: self.chart_to_profile_func(self.chart_to_profile_box.currentText()))
        #remove profile
        self.rm_box=QtWidgets.QComboBox()
        self.rm_box.insertItems(1,self.rm_profiles())
        self.rm_box.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        self.rm_pract=QtWidgets.QWidgetAction(None)
        self.rm_pract.setDefaultWidget(self.rm_box)
        self.ui.menuRemove_Profile.addAction(self.rm_pract)
        self.rm_box.activated.connect(lambda *args: self.rm_profile_func(self.rm_box.currentText()))

        self.sc_api={}
        self.update_api_shortcuts()

        self.setWindowTitle(cfg.PROGRAM_NAME)
    
        # self.sc_test=QtWidgets.QShortcut(QtWidgets.QKeySequence('L'), self)
        # self.sc_test.activated.connect(self.foo)
    
    #create persistent object for lambda *args: api.invoker() with arguments for
    #update_api_shortcuts()
    class _Invoke: 
        def __init__(self,mdi,fname,fpath,shortcut=None) -> None:
            self.mdi=mdi
            self.fname=fname
            self.fpath=fpath
            self.shortcut=shortcut
        
        def inv(self):
            return lambda *args: api.invoker(self.mdi,self.fname,self.fpath,shortcut=self.shortcut)

    def update_api_shortcuts(self):
        for pth,sc in self.sc_api.items():
            try: sc.activated.disconnect()
            except Exception: pass
            sc.setParent(None)
            del sc
        self.sc_api={}
        dr=cfg.APP_DIR
        for root, dirs, files in os.walk(dr):
            for filename in files:
                if filename[-3:]=='.py':
                    fpath=os.path.relpath(os.path.join(root, filename))
                    with open(fpath,'r') as f:
                        for line in f:
                            if (s:='PQshortcut=') in (l:=line.replace(' ','')):
                                l=l.strip(s).strip('\n').strip('"').strip("'")
                                self.sc_api[fpath]=QtGui.QShortcut(QtGui.QKeySequence(l), self)
                                a=self._Invoke(self.mdi,filename,fpath,shortcut=l)
                                self.sc_api[fpath].activated.connect(a.inv())
                                
    def connection_status(self,s):
        if s:
            self.message_connection_status.setText(cfg.CONNECTION_MESSAGE)
        else:
            self.message_connection_status.setText(cfg.NO_CONNECTION_MESSAGE)
    
    def toggle_tabbed_view(self,s):
        self.ui.actionTabbed_View.setChecked(s)
        if s:
            self.mdi.setViewMode(QtWidgets.QMdiArea.TabbedView)
            self.mdi.setTabShape(QtWidgets.QTabWidget.Triangular)
            self.mdi.setTabsClosable(True)
            self.mdi.setTabsMovable(True)
        else:
            self.mdi.setViewMode(QtWidgets.QMdiArea.SubWindowView)
    
    def toggle_status_bar(self,s):
        self.ui.actionStatus_Bar.setChecked(s)
        if s:
            self.ui.statusbar.show()
        else:
            self.ui.statusbar.hide()

    def copy_item_act(self,copyline=False):
        if (asw:=self.mdi.activeSubWindow()) is not None:
            for dk in asw.docks:
                dk.widgets[0].copy_item_act(copyline=copyline)

    def select_all_act(self):
        if (asw:=self.mdi.activeSubWindow()) is not None:
            for dk in asw.docks:
                dk.widgets[0].select_all_act()
    
    def deselect_all_act(self):
        if isinstance(asw:=self.mdi.activeSubWindow(),AltSubWindow):
            for dk in asw.docks:
                dk.widgets[0].deselect_all_act()
        self.sigEscapePressed.emit()
    
    def delete_act(self):
        if (asw:=self.mdi.activeSubWindow()) is not None:
            for dk in asw.docks:
                dk.widgets[0].delete_act()
    
    def undo_act(self):
        if (asw:=self.mdi.activeSubWindow()) is not None:
            for dk in asw.docks:
                dk.widgets[0].undo_act()

    def rm_profiles(self): #list of profiles that can be removed
        rmp=[]
        for prf in self.profiles: #copy self.profiles to rmp
            rmp.append(prf)
        if rmp[0] not in cfg.D_PROFILES:
                rmp.pop(0)
        rmp.remove(cfg.D_PROFILE)
        rmp.remove(cfg.DELETED_PROFILE)
        return rmp
    
    def ch_profiles(self):
        a=self.rm_profiles()
        if self.profiles[0]!=cfg.D_PROFILE:
            a.append(cfg.D_PROFILE)
        return a

    def set_profile_func(self,name):
        self.save_subw_states()
        for subw in self.mdi.subWindowList():
            if isinstance(subw,AltSubWindow):
                subw.close(delete_from_profile=False)
            else:
                subw.close()
        self.profiles_reorder()
        self.profiles.remove(name)
        self.profiles.insert(0,name)
        self.comboboxes_refresh()
        self.open_subw(self.pstate)       

    def add_profile_func(self,name):
        self.ui.menuChart.close()
        mestitle='Add profile'

        for pr in self.profiles:
            if pr==name:
                uitools.simple_message_box(mestitle,f"Profile '{name}' already exists",QtWidgets.QMessageBox.Warning)
                return
        
        self.profiles_reorder()
        self.profiles.insert(0,name)
        self.comboboxes_refresh()
        for subw in self.mdi.subWindowList():
            if isinstance(subw,AltSubWindow):
                subw.profiles.append(name)
        self.profile_eline.clear()
        self.save_subw_states()
        uitools.simple_message_box(mestitle,f"Profile '{name}' has been added",QtWidgets.QMessageBox.Information)

    def chart_to_profile_func(self,name):
        self.ui.menuChart.close()
        mestitle='Add/Restore chart to profile'

        subw=self.mdi.activeSubWindow()
        if subw is None:
            uitools.simple_message_box(mestitle,f"No chart has been selected",QtWidgets.QMessageBox.Warning)
            return
        
        subwtitle=subw.windowTitle()

        for pr in subw.profiles:
            if pr==name:
                uitools.simple_message_box(mestitle,f"Chart '{subwtitle}' is already in profile '{name}'",QtWidgets.QMessageBox.Warning)
                return
        
        subw.profiles.append(name)
        if self.profiles[0]==cfg.DELETED_PROFILE:
            subw.profiles.remove(cfg.DELETED_PROFILE)
            subw.close()
        self.save_subw_states(subwindow=subw)
        uitools.simple_message_box(mestitle,f"Chart '{subwtitle}' has been added to profile '{name}'",QtWidgets.QMessageBox.Information)
    
    def rm_profile_func(self,name):
        self.ui.menuChart.close()
        text=f"Remove '{name}' from profiles?"
        rv=uitools.dialog_message_box(title='Remove profile',text=text,icon=QtWidgets.QMessageBox.Question,default_button=QtWidgets.QMessageBox.Cancel)
        if rv==QtWidgets.QMessageBox.Ok:
            self.profiles.remove(name)
            self.comboboxes_refresh()
            for record in self.pstate: #purge profile from pstate
                rsp=record['subwindow profiles']
                if name in rsp:
                    rsp.remove(name)
                    if cfg.DELETED_PROFILE not in rsp:
                        rsp.append(cfg.DELETED_PROFILE)
            for subw in self.mdi.subWindowList(): #purge profile from currently active subwindows
                if name in subw.profiles:
                    subw.profiles.remove(name)
                    if cfg.DELETED_PROFILE not in subw.profiles:
                        subw.profiles.append(cfg.DELETED_PROFILE)
        self.save_subw_states()

    def comboboxes_refresh(self):
        self.set_box.clear()
        self.set_box.insertItems(1,self.profiles)
        spr=self.ui.menuSet_Profile
        spr.removeAction(self.set_pract)#Workaround for correct resizing of the Set Profile menu
        spr.addAction(self.set_pract)

        self.set_box1.clear()
        self.set_box1.insertItems(1,self.profiles)
        
        self.chart_to_profile_box.clear()
        self.chart_to_profile_box.insertItems(1,self.ch_profiles())
        chapr=self.ui.menuAdd_Restore_Chart_to_Profile
        chapr.removeAction(self.chtop_pract)#Workaround for correct resizing of the Set Profile menu
        chapr.addAction(self.chtop_pract)
        
        self.rm_box.clear()
        self.rm_box.insertItems(1,self.rm_profiles())
        rpr=self.ui.menuRemove_Profile
        rpr.removeAction(self.rm_pract)#Workaround for correct resizing of the Set Profile menu
        rpr.addAction(self.rm_pract)
    
    def profiles_reorder(self):
        self.profiles.remove(cfg.D_PROFILE)
        self.profiles.remove(cfg.DELETED_PROFILE)
        self.profiles.sort()
        self.profiles.insert(0,cfg.D_PROFILE)
        self.profiles.append(cfg.DELETED_PROFILE)

    def empty_profile_bin(self):
        self.ui.menuChart.close()
        title='Empty profile bin'
        idle_message=lambda *args: uitools.simple_message_box(title=title,text=f'Nothing to do, profile {cfg.DELETED_PROFILE} is already empty',
                    icon=QtWidgets.QMessageBox.Information)
        todo=False
        for record in self.pstate:
            if 'subwindow profiles' in record:
                if cfg.DELETED_PROFILE in record['subwindow profiles']:
                    todo=True
                    break
        if todo==False or (self.profiles[0]==cfg.DELETED_PROFILE and self.mdi.subWindowList()==[]):
            idle_message()
            return

        rv=uitools.dialog_message_box(title=title,text=f"All charts in profile '{cfg.DELETED_PROFILE} will be removed forever",
                icon=QtWidgets.QMessageBox.Critical,default_button=QtWidgets.QMessageBox.Cancel)
        if rv==QtWidgets.QMessageBox.Ok:
            if self.profiles[0]==cfg.DELETED_PROFILE:
                for subw in self.mdi.subWindowList():
                    if subw!=None:            
                        subw.close()
            else:
                objs=[]
                for record in self.pstate:
                    if 'subwindow profiles' in record:
                        if cfg.DELETED_PROFILE in record['subwindow profiles']:
                            record['subwindow profiles'].remove(cfg.DELETED_PROFILE)
                            if record['subwindow profiles']==[]:
                                objs.append(record)
                for ob in objs:
                    self.pstate.remove(ob)
            uitools.simple_message_box(title=title,text=f'Profile {cfg.DELETED_PROFILE} has been cleared',icon=QtWidgets.QMessageBox.Information)

    def closeEvent(self, event):
        self.sigMainWindowClosing.emit()
        #to ensure experts are always off on opening:
        # self.props['experts_on']=False 
        
        for subw in self.mdi.subWindowList():
            if subw.is_persistent==True:
                try:
                    subw.plt.lc_thread.wait()
                except Exception:
                    pass
        
        #identify hidden widgets
        self.props['hidden']=[]
        for ch in self.children():
            if isinstance(ch,QtWidgets.QStatusBar) or isinstance(ch,QtWidgets.QToolBar):
                if ch.isHidden(): self.props['hidden'].append(ch.objectName())

        ws={'window size': self.size().toTuple(),'window position': self.pos().toTuple(),
            'profiles': self.profiles, 'props':self.props}
        with open(cfg.DATA_STATES_DIR+cfg.WINDOW_STATE_FLNM, 'w') as f:
            f.write(json.dumps(ws))

        self.save_subw_states()
        self.remove_garbage()
        
        with open(cfg.DATA_STATES_DIR+cfg.PROFILE_STATE_FLNM, 'w') as f:
            f.write(json.dumps(self.pstate))
        
        fls=os.listdir(cfg.DATA_SYMBOLS_DIR) #delete second timeframe files on closure
        for fl in fls:
            if '_S' in fl:
                os.remove(cfg.DATA_SYMBOLS_DIR+fl)
        
        return super().closeEvent(event)

    def save_subw_states(self,subwindow=None):
        if self.profiles[0]!=cfg.DELETED_PROFILE:
            def subwindow_record(subw):               
                if subw.is_persistent==True:
                    subw_dict={'subwindow type':type(subw).__name__}
                    if isinstance(subw,AltSubWindow):
                        plotID=subw.plt.plotID
                        desc=subw.plt.description
                        symbol=subw.plt.symbol
                        ct=subw.plt.charttype
                        tf=subw.plt.timeframe
                        subw_dict['subwindow plotID']=plotID
                        subw_dict['subwindow description']=desc
                        subw_dict['subwindow size'] = subw.size().toTuple()
                        subw_dict['subwindow position'] = subw.pos().toTuple()
                        subw_dict['subwindow is maximized'] = subw.isMaximized()
                        subw_dict['subwindow symbol'] = symbol
                        subw_dict['subwindow charttype'] = ct
                        subw_dict['subwindow timeframe'] = tf
                        subw_dict['subwindow profiles'] = subw.profiles

                        # x=subw.plt.getAxis('bottom').range
                        # y=subw.plt.getAxis('left').range
                        # subw_dict['subwindow Xrange']=x
                        # subw_dict['subwindow Yrange']=y
                        subw_dict['subwindow range']=subw.plt.viewRange()

                        subw_dict['subwindow docks']=len(subw.docks)
                        subw_dict['subwindow dockarea state']=subw.dock_area.saveState()

                        subw_dict['subwindow chartprops']=subw.plt.chartprops

                        #ensure that crosshair items are removed
                        if subw.plt.crosshair_enabled==True:
                            subw.plt.cross_hair()

                        item_states=[]
                        for dk in subw.docks:
                            dockplt=dk.widgets[0]
                            for item in dockplt.listItems():
                                itype=type(item).__name__
                                imodule=type(item).__module__
                                try:
                                    if item.is_persistent==True:
                                        istate=dict()
                                        istate['dock']=int(dk.title())
                                        istate['itype']=imodule+'.'+itype
                                        try: istate['dt']=item.save_dt() #store datetime data where applicable
                                        except Exception:pass
                                        try: istate['iprops']=dict(item.save_props())
                                        except Exception: pass
                                        # try:
                                        #     istate['istate']= item.saveState()
                                        # except Exception:
                                        #     istate['istate']=None
                                        item_states.append(istate)
                                except Exception:
                                    pass

                        subw_dict['item_states']=item_states
                        subw_dict['priceline_enabled']=subw.plt.priceline_enabled
                        subw_dict['grid_enabled']=subw.plt.grid_enabled

                        for record in self.pstate:
                            try:
                                if record['subwindow plotID']==plotID:
                                    self.pstate.remove(record)
                            except Exception:
                                pass
                        self.pstate.append(subw_dict)

                        return subw_dict
                    
                    elif isinstance(subw,uitools.TreeSubWindow):
                        subw_dict['subwindow size'] = subw.size().toTuple()
                        subw_dict['subwindow position'] = subw.pos().toTuple()
                        self.pstate.append(subw_dict)

            if subwindow is None:
                for ps in self.pstate: #to ensure no duplicate windows
                    if ps['subwindow type']=="TreeSubWindow":
                        self.pstate.remove(ps)
                        break
                for sw in self.mdi.subWindowList():
                    subwindow_record(sw)
            else:
                return subwindow_record(subwindow)

    def remove_garbage(self):
        for record in self.pstate:
            if 'subwindow profiles' in record and record['subwindow profiles']==[]:
                self.pstate.remove(record)
        
    def open_subw(self, pstates):
        psts=pstates
        for ps in psts:
            if ps['subwindow type']=='AltSubWindow':
                swps=ps['subwindow profiles']
                if self.profiles[0] in swps:
                    subw = AltSubWindow(profiles=swps)
                    plotID=ps['subwindow plotID']
                    plt = drws.AltPlotWidget(mwindow=self,subwindow=subw,plotID=plotID,
                        chartprops=ps['subwindow chartprops'])
                    subw.plt=plt
                    plt.description=ps['subwindow description']
                    symbol=ps['subwindow symbol']
                    charttype=ps['subwindow charttype']
                    timeframe=int(ps['subwindow timeframe'])
                    subw.setWindowTitle(symbol+","+cfg.tf_to_label(timeframe)+plt.description)

                    if self.profiles[0]==cfg.DELETED_PROFILE:
                        self.mdi.addSubWindow(subw)
                        subw.resize(250,25)
                        subw.show()
                        continue

                    self.mdi.addSubWindow(subw)
                    subw.resize(*ps['subwindow size']) 
                    subw.move(*ps['subwindow position'])            

                    item=self.cbl_plotter(plt,symbol=symbol,ct=charttype,tf=timeframe)
                    subw.set_plot(plt)

                    lendocks=ps['subwindow docks']
                    if lendocks>1:
                        for j in range(1,lendocks):
                            subw.add_plot()
                    subw.dock_area.restoreState(ps['subwindow dockarea state'])
                    item_states=ps['item_states']
                    for ist in item_states:
                        dockname=ist['dock']
                        dockplt=subw.docks[dockname].widgets[0]
                        if dockname==0:
                            item=eval(ist['itype'])(plt,caller='open_subw')
                        else:
                            item=eval(ist['itype'])(plt,dockplt=dockplt,
                                caller='open_subw')
                        if item not in dockplt.listItems():
                            dockplt.addItem(item)
                        # item.setState(ist['istate'])

                        try:item.set_dt(ist['dt']) #read datetime data where applicable
                        except Exception: pass
                        try: item.set_props(ist['iprops'])
                        except Exception:pass

                        if isinstance(item,drws.DrawItem):
                            item.set_selected(False)
                    sr=ps['subwindow range']
                    plt.setRange(xRange=sr[0],yRange=sr[1],padding=0)#to restore the scale of the plot

                    if ps['priceline_enabled']==True:
                        plt.priceline=drws.PriceLine(plt)
                        plt.priceline_enabled=True
                    
                    if ps['grid_enabled']==True:
                        plt.grid=drws.AltGrid(plt)
                        plt.grid_enabled=True
                    
                    if ps['subwindow is maximized']: subw.showMaximized()
                    else: subw.show()
            
            elif ps['subwindow type']=='TreeSubWindow':
                subw=uitools.TreeSubWindow(self)
                subw.resize(*ps['subwindow size'])
                subw.move(*ps['subwindow position'])
            
    #Plotter
    def cbl_plotter(self,plt,symbol=cfg.D_SYMBOL, ct=cfg.D_CHARTTYPE, tf=cfg.D_TIMEFRAME):
        tseries=tmss.Timeseries(session=self.session, fetch=self.fetch, symbol=symbol,
            timeframe=tf,count=self.props['count'])      
        lc_item=None
        if tseries.lc_complete==True:
            item=tmss.PlotTimeseries(symbol,ct,ts=tseries,session=self.session,
                fetch=self.fetch,chartprops=plt.chartprops)                
        else:
            item=tmss.PlotTimeseries(symbol,ct,ts=tseries,session=self.session,
                fetch=self.fetch,end=-1,chartprops=plt.chartprops)
            lc_item=tmss.PlotTimeseries(symbol,ct,ts=tseries,session=self.session,
                fetch=self.fetch,start=-1,chartprops=plt.chartprops)
        plt.link_chartitem(item,lc_item)
        xax=ovrd.AltDateAxisItem(item.times, item.last_tick, item.timeframe,chartprops=plt.chartprops)
        plt.setAxisItems({"bottom":xax})
        plt.subwindow.setWindowTitle(item.symbol+","+item.tf_label+plt.description)
        plt.addItem(item)
        if lc_item!=None:
            plt.addItem(lc_item)
        
        return item

    def range_setter(self,plt,item,last_tick=None,xcount=cfg.DX_COUNT, 
            xshift=cfg.DX_SHIFT,yzoom=cfg.DY_ZOOM):
        tf=item.timeframe
        XLast=item.last_tick if last_tick is None else last_tick
        plt.setXRange(XLast-xcount*tf,XLast+xshift*tf,padding=0)
        xl= int (XLast//tf)
        ymax=item.ymax(xl-xcount,xl)
        ymin=item.ymin(xl-xcount,xl)
        y_adj=(1-yzoom)*(ymax-ymin)/2
        plt.setYRange(ymin-y_adj,ymax+y_adj,padding=0)

    def window_act(self, action):    
            
        def cbl_replacer(self, plt, act):     
            try:
                for item in plt.listItems():# store states of drawing items
                    if chtl.item_is_draw(item):
                        try:
                            item.state=item.getState()
                        except Exception:
                            pass #print(f"The {item} item does not have a state")
                old_cbl_item=plt.chartitem
                old_tf=plt.chartitem.timeframe
                xax=plt.getAxis('bottom')
                xc =int((min(old_cbl_item.last_tick,xax.range[1])-xax.range[0])//old_tf)
                xs=int((max(old_cbl_item.last_tick,xax.range[1])-old_cbl_item.last_tick)//old_tf)                       
                
                timepoint=None
                if old_cbl_item.first_tick < xax.range[1] < old_cbl_item.last_tick: 
                    for x in range(len(old_cbl_item.times)): 
                        if xax.range[1]-old_cbl_item.ticks[x]<=old_tf:
                            timepoint=old_cbl_item.times[x]
                            break

                yax=plt.getAxis('left')

                ymax = old_cbl_item.ymax(xax.range[0],xax.range[1])
                ymin = old_cbl_item.ymin(xax.range[0],xax.range[1])
                yz=(ymax-ymin)/(yax.range[1]-yax.range[0])

                try:
                    if act in cfg.CHARTTYPES:
                        new_ct=act
                        new_tf=old_cbl_item.tf
                        new_sy=old_cbl_item.symbol
                    else:
                        new_ct=old_cbl_item.charttype
                        new_tf=cfg.TIMEFRAMES[act]
                        new_sy=old_cbl_item.symbol
                except Exception:
                    uitools.simple_message_box(text='Unknown action',info=QtWidgets.QMessageBox.Warning)
                    ##print('Unknown action')

                plt.removeItem(old_cbl_item)
                try:
                    plt.removeItem(plt.lc_item)
                except Exception:
                    pass
                
                new_cbl_item=self.cbl_plotter(plt,symbol=new_sy,ct=new_ct, tf=new_tf)
                
                if timepoint is None:
                    xl=new_cbl_item.last_tick                          
                else:
                    for x in range(len(new_cbl_item.ticks)):
                        if timepoint-new_cbl_item.times[x]<=new_tf:
                            xl=new_cbl_item.ticks[x]
                            break
    
                self.range_setter(plt,new_cbl_item,xl,xc,xs,yzoom=yz)
                
            except Exception:
                pass
                    
            if plt.crosshair_enabled==True:
                del plt.crosshair_item
                plt.crosshair_item=drws.CrossHair(plt)
               
            if plt.priceline_enabled==True:
                del plt.priceline
                plt.priceline=drws.PriceLine(plt)

            plt.sigTimeseriesChanged.emit(new_cbl_item.timeseries)

        if action=="...":
            pass

        if action == "Cascade":
            self.mdi.cascadeSubWindows()

        if action == "Tile":
            self.mdi.tileSubWindows()
        
        if action == "TabbedView":
            self.props['tabbed_view']=not self.props['tabbed_view']
            self.toggle_tabbed_view(self.props['tabbed_view'])
        
        if action == 'StatusBar':
            stb=self.ui.statusbar.objectName()
            if 'hidden' not in self.props:
                self.props['hidden']=[stb]
                self.toggle_status_bar(False)
            elif stb in self.props['hidden']:
                self.props['hidden'].remove(stb)
                self.toggle_status_bar(True)
            else:
                self.props['hidden'].append(stb)
                self.toggle_status_bar(False)
        
        if action=="New":
            if self.profiles[0]==cfg.DELETED_PROFILE:
                self.set_profile_func(cfg.D_PROFILE)
            subw=AltSubWindow(profiles=[self.profiles[0]])
            plt = drws.AltPlotWidget(mwindow=self,subwindow=subw,
                chartprops=self.props['chartprops'])
            
            item=None
            try:
                item=self.cbl_plotter(plt)
            except FileNotFoundError as e:
                for file in os.listdir(cfg.DATA_SYMBOLS_DIR):
                    fl=chtl.filename_to_symbol(file)
                    if fl is not None:
                        item=self.cbl_plotter(plt,symbol=fl[0],tf=fl[1])
                        break
            
            if item is None:
                txt="No timeseries data available.\nYou need to login or load data manually."
                uitools.simple_message_box(text=txt)
                return
            
            self.range_setter(plt,item)
            subw.set_plot(plt)
            subw.plt=plt
            self.mdi.addSubWindow(subw)
            subw.show()
            subw.setGeometry(subw.pos().x(),subw.pos().y(),600,400)
            self.save_subw_states()

        if action=='Open':
            if not os.path.isdir(f'{cfg.FILES_DIR}'):
                os.mkdir(f'{cfg.FILES_DIR}')
            fileName = QtWidgets.QFileDialog.getOpenFileName(self,"Open Chart", 
                f"{cfg.FILES_DIR}", f"Chart Files (*.json)",
                options=QtWidgets.QFileDialog.DontUseNativeDialog)
            fname=fileName[0]
            if fname!='':
                with open(fname, 'r') as fpr:
                    ps=fpr.read()
                    ps=json.loads(ps)
                    ps[0]['subwindow plotID']=chtl.nametag() #to ensure no conflicts with forked files 
                                                            #in other profiles such as deleted
                    ps[0]['subwindow profiles']=[self.profiles[0]]
                    if isinstance(ps,list):
                        self.open_subw(ps)

        if action=='Save As':
            subw=self.mdi.activeSubWindow()
            subw_state=self.save_subw_states(subw)
            subw_state['subwindow profiles']=[None]
            if not os.path.isdir(f'{cfg.FILES_DIR}'):
                os.mkdir(f'{cfg.FILES_DIR}')
            sb=subw.plt.symbol
            tf=cfg.tf_to_label(subw.plt.timeframe)
            ext='json'
            fileName = QtWidgets.QFileDialog.getSaveFileName(self,"Save Chart", 
                f"{cfg.FILES_DIR}/{sb}_{tf}_{chtl.nametag(11)}.{ext}", 
                f"Chart Files (*.{ext})",options=QtWidgets.QFileDialog.DontUseNativeDialog)
            fname=fileName[0]
            stj=json.dumps([subw_state])
            if fname!='':
                if fname[-len(ext)-1:]!=f'.{ext}':
                    fname=fname+f'.{ext}'
                with open(fname, 'w') as f:
                    f.write(stj)

        
        
        if action in ('Symbol','Description','Timeframe'):
            proceed=True
            for subw in self.mdi.subWindowList():
                if isinstance(subw,EntryLine):
                    uitools.simple_message_box(text='Only one entry window can be active at a time',icon=QtWidgets.QMessageBox.Warning)
                    ##print('Only one entry window can be active at a time')
                    proceed=False
                    break
            if proceed==True:
                try:
                    asw=self.mdi.activeSubWindow()
                    # asw.showNormal()
                    self.elw=EntryLine(self.mdi,action)
                    # self.win_close_sig_func=lambda *args: self.mdi.removeSubWindow(elw)
                    asw.sigAltSubWindowClosing.connect(self.win_close_sig_func)
                    self.sigEscapePressed.connect(self.win_close_sig_func)
                    self.mdi.addSubWindow(self.elw)
                    widg=asw.plt
                    self.elw.setGeometry(asw.pos().x()+widg.pos().x(),
                            asw.pos().y()+widg.pos().y(),200,50)
                    self.elw.show()
                    if action=='Symbol':
                        try:
                            asw.plt.subwindow=asw
                            asw.plt.wnd_eline=self.elw
                            asw.plt.eline=self.elw.eline        
                            self.elw.eline.returnPressed.connect(asw.plt.symb_change)                      
                        except Exception:
                            pass
                    else:
                        self.asw=asw
                        def prop_change():
                            it=self.asw.plt.chartitem
                            symb=it.symbol
                            tf_label=it.tf_label
                            prop=self.elw.eline.text()
                            if action=='Description':                               
                                desc=self.asw.plt.description='' if prop=='' else ':'+self.elw.eline.text()
                                self.asw.setWindowTitle(symb+","+tf_label+desc)
                            elif action=='Timeframe':
                                if prop.upper() in cfg.TIMEFRAMES:
                                    try:
                                        cbl_replacer(self,asw.plt,prop.upper())
                                    except Exception:
                                        uitools.simple_message_box(text='Invalid timeframe',icon=QtWidgets.QMessageBox.Warning)
                                        #print('Invalid timeframe')
                                else:
                                    uitools.simple_message_box(text='Invalid timeframe',icon=QtWidgets.QMessageBox.Warning)
                                    #print('Invalid timeframe')
                            self.asw.setFocus()
                            self.elw.eline.returnPressed.disconnect(prop_change)
                            asw.sigAltSubWindowClosing.disconnect(self.win_close_sig_func)
                            self.sigEscapePressed.disconnect(self.win_close_sig_func)
                            self.elw.close()
                            self.mdi.removeSubWindow(self.elw)
                            del self.elw
                            del self.asw
                        self.elw.eline.returnPressed.connect(prop_change)
                except Exception:
                    uitools.simple_message_box(text='Select chart window first',icon=QtWidgets.QMessageBox.Warning)
                    #print('Select chart window first')

        #############rerfesh block
        def refresh_plot(sw,tfname=None):
            try:
                tfn=cfg.tf_to_label(sw.plt.timeframe) if tfname is None else tfname          
                cbl_replacer(self, sw.plt, tfn)
            except Exception:
                pass

        if action=='Offline':
            if action in self.props:
                self.props[action]=not self.props[action]
            else:
                self.props[action]=True
            
            if self.fetch is not None:
                self.fetch.offline_mode=self.props[action]
                self.fetch.trigger()
            for sw in self.mdi.subWindowList():
                refresh_plot(sw)

        if action in cfg.TIMEFRAMES or action in cfg.CHARTTYPES:
            if (sw:=self.mdi.activeSubWindow()) is not None:
                refresh_plot(sw,tfname=action)
        
        if action=='Refresh':
            if (sw:=self.mdi.activeSubWindow()) is not None:
                refresh_plot(sw)

        if action=='History':
            plt=self.mdi.activeSubWindow().plt
            symbol=plt.symbol
            tflen=len(cfg.TIMEFRAMES)
            pbox=uitools.ProgressBox(name='History',text='Loading history',max=tflen-1)
            for i,tf in enumerate(cfg.TIMEFRAMES.values()):
                if tf!=cfg.PERIOD_MN:
                    hst=ftch.history(tf,symbol)
                    if hst is True:
                        pbox.setValue(i)
                        lbl=cfg.tf_to_label(tf)
                        pbox.setLabelText(f'Loading history: {symbol},{lbl}')
                    elif hst is False:
                       pass
                    else:
                        pbox.close()
                        uitools.simple_message_box(title='History',
                            text='Loading error: check connection and try again')
            
            refresh_plot(cfg.tf_to_label(plt.timeframe))
        ###############################################

        if action=='Login':
            uitools.LoginForm()
            self.sigAcctDataChanged.emit()
        
        if action=='Magnet':
            try:
                a=self.props['magnet']
                self.props['magnet']= not a
            except Exception:
                self.props['magnet']=True
        
        if action=='Export':
            from PIL import ImageGrab
            subw=self.mdi.activeSubWindow()
            pos_mdi=self.mapToGlobal(self.mdi.pos())
            pos_subw=subw.pos()
            size=subw.size()
            x=pos_mdi.x()+pos_subw.x()
            y=pos_mdi.y()+pos_subw.y()
            w=size.width()
            h=size.height()
            bbox=(x,y,x+w,y+h)
            image=ImageGrab.grab(bbox)
            image.show()
            if not os.path.isdir(f'{cfg.FILES_DIR}'):
                os.mkdir(f'{cfg.FILES_DIR}')
            sb=subw.plt.symbol
            tf=cfg.tf_to_label(subw.plt.timeframe)
            image.save(f'{cfg.FILES_DIR}/{sb}_{tf}_{chtl.nametag(11)}.png')
        
        if action=='Experts':
            self.props['experts_on']=not self.props['experts_on']
            self.sigMainWindowVariablesUpdate.emit()
        
        if action=="About":
            if chtl.is_linux():
                stm='Linux'
            elif chtl.is_windows():
                stm='Windows'
            else: 
                stm=''
            txt=f'Copyright \u00A9 pyqtrader 2022-{datetime.datetime.now().year}\n'
            txt=txt+f'System: {stm}\n'
            txt=txt+f'Version: {cfg.VERSION}'
            uitools.simple_message_box(title='About', text=txt)
        
        if action=="License":
            txt=open(f'{cfg.MAIN_DIR}LICENSE').read()
            uitools.simple_message_box(title='License',text=txt)
    
    def win_close_sig_func(self):
        maxzd=self.elw.isMaximized()
        self.mdi.removeSubWindow(self.elw)
        if maxzd: self.mdi.activeSubWindow().showMaximized() #to prevent 'maximized' status loss
        self.sigEscapePressed.disconnect(self.win_close_sig_func)
    
    def widgets_init(self):
        if self.props['hidden']!=[]:
            for ch in self.children():
                if isinstance(ch,QtWidgets.QToolBar) or isinstance(ch,QtWidgets.QStatusBar):
                    if ch.objectName() in self.props['hidden']: ch.hide()

    def set_theme(self):
        if self.props['theme']==cfg.THEMES['Light']:
            # self.app.setPalette(self.palet) #resets palette
            styles.set_light_theme(self)
        elif self.props['theme']==cfg.THEMES['Dark']:
            # self.app.setPalette(self.palet) #resets palette
            styles.set_dark_theme(self)
        elif self.props['theme']==cfg.THEMES['Darker']:
            # self.app.setPalette(self.palet) #resets palette
            styles.set_darker_theme(self)
        else:
            # self.app.setPalette(s:=self.app.style().standardPalette())
            self.app.setPalette(self.palet)
            self.mdi.setBackground(self.palet.base())

def mainexec():
    # from patcher import patcher
    # patcher()

    import sys
    from userfiles_packer import unpack
    # splash_ok=True
    # # try: import pyi_splash
    # except ImportError: splash_ok=False

    cwd=os.getcwd()
    sys.path.append(cwd)

    unpack()
    app = pg.mkQApp() #QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setWindowIcon(QtGui.QIcon(f'{cfg.CORE_ICON}'))
    
    ft=ftch.Fetcher()
    mdi = MDIWindow(application=app,fetch=ft)
    # if splash_ok:pyi_splash.close()
    mdi.show()
    app.exec()

if __name__ == "__main__":
    mainexec()