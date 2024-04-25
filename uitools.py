import PySide6
from PySide6 import QtWidgets,QtGui,QtCore
import cfg
import charttools as chtl, charttools
import fetcher as ftch

#debugging section
from _debugger import _print, _printcallers,  _exinfo, _p, _pc,_c

def simple_message_box(title=None,text='Notification',icon=None):
        mbox=QtWidgets.QMessageBox()
        mbox.setWindowTitle(title)
        mbox.setText(text)
        if icon!=None:
            mbox.setIcon(icon)
        mbox.exec()

def dialog_message_box(title,text,icon=QtWidgets.QMessageBox.NoIcon,
        default_button=QtWidgets.QMessageBox.Cancel,
        action_button=QtWidgets.QMessageBox.Ok):
    msgBox=QtWidgets.QMessageBox()
    msgBox.setText(text)
    msgBox.setIcon(icon)
    msgBox.setWindowTitle(title)
    msgBox.setStandardButtons( action_button | default_button)
    msgBox.setDefaultButton(default_button)
    return msgBox.exec()

class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

class QVLine(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)

class ColorButton(QtWidgets.QPushButton):
    def __init__(self,*args,dialog=None,item=None,btncolor=None,**kwargs) -> None:
        super().__init__(*args,**kwargs)
        self.dialog=dialog
        self.item=item
        if dialog!=None:
            self.btncolor=dialog.color
        else:
            self.btncolor=btncolor
        self.setAutoDefault(False)
        self.colord=QtWidgets.QColorDialog()
        self.colord.setOptions(QtWidgets.QColorDialog.DontUseNativeDialog)
        if btncolor!=None:
            self.setStyleSheet(f"background-color: {self.btncolor}")
        self.clicked.connect(self.set_color)
    
    def update_color(self,clr):
        self.btncolor=clr
        self.setStyleSheet(f"background-color: {clr}")

    def set_color(self):
        cd=self.colord.exec()
        if cd==1:
            self.btncolor=self.colord.selectedColor().name()
            self.setStyleSheet(f"background-color: {self.btncolor}")
            if self.item is not None:
                self.item.setPen(color=self.btncolor)
            if self.dialog is not None:
                self.dialog.color=self.btncolor

class EmbeddedDialogBox(QtWidgets.QWidget):
    def __init__(self,*buttons,default_button=None) -> None:
        super().__init__()
        def caps(b):
            if b=='Ok':
                return 'OK'
            else:
                return b
        
        pmap=QtWidgets.QStyle.StandardPixmap
        self.btn=[]
        layout=QtWidgets.QHBoxLayout()
        i=0
        for b in buttons:
            self.btn.append(QtWidgets.QPushButton(caps(b)))
            pixmapi = getattr(pmap,f'SP_Dialog{b}Button')
            icon = self.style().standardIcon(pixmapi)
            self.btn[i].setIcon(icon)
        
            if default_button==i:
                self.btn[i].setAutoDefault(True)
            else:
                self.btn[i].setAutoDefault(False)

            layout.addWidget(self.btn[i])
            i+=1
        
        self.setLayout(layout)
        self.show()

class PropDialog(QtWidgets.QDialog):
    period=cfg.D_STUDYPERIOD
    shift=0
    width=cfg.D_STUDYWIDTH
    mode=cfg.D_STUDYMODE
    color=cfg.D_STUDYCOLOR
    initials=dict(period=period,shift=shift,width=width,mode=mode,
        color=color)
    def __init__(self, plt,item=None,ItemType=None,ts=None,props_on=None,order=0):
        self.props_on=dict(period=True,shift=False, width=True,
            mode=False,color=True)
        if props_on is not None:
            for key in props_on:
                self.props_on[key]=props_on[key]
        self.state_dict={}
        for key in self.props_on:
            if self.props_on[key]==True:
                self.state_dict[key]=getattr(self.__class__,key)
            else:
                try:
                    delattr(self.__class__,key)
                    del self.__class__.initials[key]
                except Exception:
                    pass
                
        if item is not None:
            for att in ('width','color','shift'):
                try: #width, color or shift attr may be absent in specific classes
                    setattr(self.__class__,att,getattr(item,att))
                except Exception:
                    pass
            if chtl.item_is_study(item):
                for key in item.funkvars:
                    setattr(self.__class__,key,item.funkvars[key])
        super().__init__()
        self.plt=plt
        self.item=item
        self.ItemType=ItemType
        if ts is None:
            try:
                self.ts=self.plt.chartitem.timeseries
            except Exception:
                pass
        else:
            self.ts=ts
        #self.state_dict is a collection of the class attributes, modify as needed in each
        #individual class       
 
        self.layout=QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        
        label0=QtWidgets.QLabel('Period: ')
        self.pbox=QtWidgets.QSpinBox()
        self.pbox.setMaximum(cfg.D_STUDYPERIODMAX)
        self.pbox.setMinimum(1)
        
        label1=QtWidgets.QLabel('Shift: ')
        self.shbox=QtWidgets.QSpinBox()
        self.shbox.setMinimum(-99)        

        label2 = QtWidgets.QLabel('Width: ')
        self.wbox=QtWidgets.QDoubleSpinBox()
        self.wbox.setSingleStep(0.1)
        self.wbox.setMinimum(0.1)
        self.wbox.setDecimals(1)        
        
        label3=QtWidgets.QLabel('Mode: ')
        self.modebox=QtWidgets.QComboBox()
        self.modebox.insertItems(1,cfg.D_STUDYMODELIST)
        
        label4=QtWidgets.QLabel('Color: ')
        self.clrbtn=ColorButton("",dialog=self.__class__)

        self.set_values()
        self.order=order
        if self.props_on['period']==True:
            self.layout.addWidget(label0,self.order,0)
            self.layout.addWidget(self.pbox,self.order,1)
            self.pbox.textChanged.connect(lambda *args: setattr(self.__class__,'period',self.pbox.value()))
            self.order+=1
        if self.props_on['shift']==True:
            self.layout.addWidget(label1,self.order,0)
            self.layout.addWidget(self.shbox,self.order,1)
            self.shbox.textChanged.connect(lambda *args: setattr(self.__class__,'shift',self.shbox.value()))
            self.order+=1
        if self.props_on['width']==True:
            self.layout.addWidget(label2,self.order,0)
            self.layout.addWidget(self.wbox,self.order,1)
            self.wbox.textChanged.connect(lambda *args: setattr(self.__class__,'width',self.wbox.value()))
            self.order+=1
        if self.props_on['mode']==True:
            self.layout.addWidget(label3,self.order,0)
            self.layout.addWidget(self.modebox,self.order,1)
            self.modebox.currentTextChanged.connect(lambda *args: setattr(self.__class__,'mode',self.modebox.currentText()))
            self.order+=1
        if self.props_on['color']==True: #color signals are connected separately via color box 
            self.layout.addWidget(label4,self.order,0)
            self.layout.addWidget(self.clrbtn,self.order,1)
            self.order+=1
    
    def set_values(self):
        if self.props_on['period']==True:
            self.pbox.setValue(cfg.D_STUDYPERIOD if self.__class__.period is None else self.__class__.period)
        if self.props_on['shift']==True:
            self.shbox.setValue(0 if self.__class__.shift is None else self.__class__.shift)
        if self.props_on['width']==True:
            self.wbox.setValue(cfg.D_STUDYWIDTH if self.__class__.width is None else self.__class__.width)
        if self.props_on['mode']==True:
            self.modebox.setCurrentText(cfg.D_STUDYMODE if self.__class__.mode is None else self.__class__.mode)
        if self.props_on['color']==True:
            self.clrbtn.setStyleSheet(f"background-color: {self.__class__.color}")
    
    def reset_defaults(self):
        for key in self.__class__.initials:
            setattr(self.__class__,key,self.__class__.initials[key])
        self.set_values()

    def embedded_db(self,makeitem=True):
        if makeitem:
            self.edb=EmbeddedDialogBox('Reset','Apply','Cancel','Ok',default_button=2)
            self.layout.addWidget(self.edb,self.order,0,1,0)
            self.edb.btn[0].clicked.connect(self.reset_defaults)
            self.edb.btn[2].clicked.connect(self.close)
            if self.item is None:
                self.edb.btn[1].clicked.connect(lambda *args: self.make_item(self.plt,_close=False,**self.state_dict)) 
                self.edb.btn[3].clicked.connect(lambda *args: self.make_item(self.plt,_close=True,**self.state_dict))
            else:           
                self.edb.btn[1].clicked.connect(lambda *args: self.update_item(_close=False))
                self.edb.btn[3].clicked.connect(lambda *args: self.update_item(_close=True))
        else:
            self.edb=EmbeddedDialogBox('Reset','Apply','Cancel','Ok',default_button=2)
            self.layout.addWidget(self.edb,self.order,0,1,0)
            self.edb.btn[0].clicked.connect(self.reset_defaults)
            self.edb.btn[2].clicked.connect(self.close)          
            self.edb.btn[1].clicked.connect(lambda *args: self.update_item(_close=False))
            self.edb.btn[3].clicked.connect(lambda *args: self.update_item(_close=True))
    
    def make_item(self,plt,_close=True,levels=None,**kwargs):
        self.item=self.ItemType(plt,**kwargs)
        a=self.state_dict_update()
        if levels is not None:
            a['levels']=levels
        self.item.set_props(state=a)
        if _close==True:
            self.close()
        else:
            try:
                self.edb.btn[1].clicked.disconnect()
                self.edb.btn[3].clicked.disconnect()
                self.edb.btn[1].clicked.connect(lambda *args: self.update_item(_close=False))
                self.edb.btn[3].clicked.connect(lambda *args: self.update_item(_close=True))  
            except Exception:
                pass
        return self.item

    def update_item(self,_close=True,levels=None):
        a=self.state_dict_update()
        if levels is not None:
            a['levels']=levels
        self.item.set_props(state=a)
        if _close==True:
            self.close()
        return self.item
    
    def state_dict_update(self):
        for key in self.state_dict:
            prop=getattr(self.__class__,key)
            if prop is not None:
                self.state_dict[key]=prop
        return self.state_dict

class DrawPropDialog(PropDialog):
    initials=dict(PropDialog.initials)
    initials['style']=style=cfg.D_STYLE
    initials['color']=color=cfg.D_COLOR
    def __init__(self,*args,style_on=True,exec_on=False,**kwargs):
        props_on=dict(period=False)
        super().__init__(*args,props_on=props_on,**kwargs)
        self.state_dict['style']=self.__class__.style=self.item.style
        self.__class__.initials['color']=self.plt.graphicscolor

        label0=QtWidgets.QLabel('Style: ')
        self.stylebox=QtWidgets.QComboBox()
        self.stylebox.insertItems(1,chtl.dict_to_keys(cfg.LINESTYLES))
        self.stylebox.setCurrentText(self.__class__.style)

        if style_on==True:
            self.layout.addWidget(label0,self.order,0)
            self.layout.addWidget(self.stylebox,self.order,1)
            self.stylebox.currentTextChanged.connect(lambda *args: setattr(self.__class__,'style',self.stylebox.currentText()))
            self.order+=1
        
        if exec_on==True:
            self.embedded_db()
            self.exec()
    
    def embedded_db(self):
        return super().embedded_db(makeitem=False)

    def set_values(self):
        try:
            self.stylebox.setCurrentText(cfg.D_STYLE if self.__class__.style is None else self.__class__.style)
        except Exception:
            pass
        return super().set_values()
    
    def update_item(self,_close=True,levels=None):
        a=self.state_dict_update()
        if levels is not None:
            a['levels']=levels
        self.item.set_props(a)
        if _close==True:
            self.close()
        return self.item    

class PropDialogWithFreeze(PropDialog):
    initials=dict(PropDialog.initials)
    initials['freeze']=freeze=cfg.D_STUDYFREEZE
    def __init__(self, *args,item=None,props_on=None,**kwargs):
        pps_on=dict(period=True, shift=True, width=True, mode=True, color=True)
        if props_on is not None:
            for key in props_on:
                pps_on[key]=props_on[key]
        if item is not None:
            setattr(self.__class__,"freeze",getattr(item,"freeze"))
        super().__init__(*args,item=item,props_on=pps_on,**kwargs)
        self.state_dict['freeze']=self.__class__.freeze

        label=QtWidgets.QLabel('Freeze y-axis: ')
        self.freezebox=QtWidgets.QCheckBox()
        self.freezebox.setCheckState(QtCore.Qt.Checked if self.__class__.freeze else QtCore.Qt.Unchecked)
        self.layout.addWidget(label,self.order,0)
        self.layout.addWidget(self.freezebox,self.order,1)
        self.freezebox.stateChanged.connect(lambda *args: setattr(self.__class__,'freeze',
            True if self.freezebox.checkState()==QtCore.Qt.Checked else False))
        self.order+=1

    def reset_defaults(self):
        super().reset_defaults()
        if self.__class__.freeze==True:
            self.freezebox.setCheckState(QtCore.Qt.Checked)
        else:
            self.freezebox.setCheckState(QtCore.Qt.Unchecked)

class LevelRow(QtWidgets.QWidget):
    sigRemoveLevelRow=QtCore.Signal(object)
    def __init__(self,show=True,value=None,desc=None,width=1.0,style=None,color=None,
        desc_on=True,removable=True):
        super().__init__()
        self.desc_on=desc_on
        self.removable=removable
        self.layout=QtWidgets.QHBoxLayout()
        self.eldict=dict(showbox=QtWidgets.QCheckBox(),valueline=QtWidgets.QLineEdit(),descline=QtWidgets.QLineEdit(),
            widthbox=QtWidgets.QDoubleSpinBox(), stylebox=QtWidgets.QComboBox(),colorbut=ColorButton(btncolor=color),
            rembut=QtWidgets.QPushButton())
        self.eldict['showbox'].setCheckState(QtCore.Qt.Checked if show==True else QtCore.Qt.Unchecked)
        self.eldict['valueline'].setValidator(QtGui.QDoubleValidator())
        wbox=self.eldict['widthbox']
        wbox.setSingleStep(0.1)
        wbox.setDecimals(1) 
        stbox=self.eldict['stylebox']
        stbox.insertItems(1,chtl.dict_to_keys(cfg.LINESTYLES))
        stbox.setCurrentText(style)

        if value is None:
            self.eldict['valueline'].setPlaceholderText('Value')
        else:
            value=str(value)
            self.eldict['valueline'].setText(value)
        
        if desc_on==False:
            self.eldict.pop('descline')
        else:
            if desc is None:
                self.eldict['descline'].setPlaceholderText('Description')
            else:
                self.eldict['descline'].setText(desc)
        
        wbox=self.eldict['widthbox']
        if width is not None:
            self.eldict['widthbox'].setValue(width)
        if removable==False:
            self.eldict.pop('rembut')
            self.eldict['rembut']=QtWidgets.QLabel()
        for key in self.eldict:
            self.layout.addWidget(self.eldict[key])
        if removable==True:
            pmap=QtWidgets.QStyle.StandardPixmap
            pixmapi = getattr(pmap,f'SP_DialogCloseButton')
            icon = self.style().standardIcon(pixmapi)
            self.eldict['rembut'].setIcon(icon)
            self.eldict['rembut'].clicked.connect(self.remove)
        self.state_dict={}
        self.state_dict_update()
        self.setLayout(self.layout)

    def state_dict_update(self):
        shs=self.eldict['showbox'].checkState()
        self.state_dict['show']=True if shs==QtCore.Qt.Checked else False
        vas=self.eldict['valueline'].text()
        try:
            v=float(vas)
        except Exception:
            v=0.0
        self.state_dict['value']=v
        if self.desc_on==True:
            self.state_dict['desc']=self.eldict['descline'].text()
        self.state_dict['width']=self.eldict['widthbox'].value()
        self.state_dict['style']=self.eldict['stylebox'].currentText()
        self.state_dict['color']=self.eldict['colorbut'].btncolor
        self.state_dict['desc_on']=self.desc_on
        self.state_dict['removable']=self.removable
        return self.state_dict
    
    def remove(self):
        self.sigRemoveLevelRow.emit(self)

class LevelTable(QtWidgets.QWidget):
    sigLevelTableResized=QtCore.Signal(int)
    def __init__(self,preset_levels=None,**kwargs) -> None:
        super().__init__()
        self.kwargs=kwargs
        self.state_list=[]
        self.layout=QtWidgets.QVBoxLayout()
        self.addbut=QtWidgets.QPushButton()
        self.addbut.setText('Add')
        self.layout.addWidget(self.addbut)
        if preset_levels is not None:
            for lvl in preset_levels:
                entry=LevelRow(**lvl)
                self.layout.addWidget(entry)
                entry.sigRemoveLevelRow.connect(self.remove_entry)
        self.setLayout(self.layout)
        self.addbut.clicked.connect(self.add_entry)
    
    def add_entry(self):
        entry=LevelRow(**self.kwargs)
        self.layout.addWidget(entry)
        self.resize(self.sizeHint())
        entry.sigRemoveLevelRow.connect(self.remove_entry)
        self.sigLevelTableResized.emit(1)

    def remove_entry(self,entry):
        entry.setParent(None)
        entry.sigRemoveLevelRow.disconnect(self.remove_entry)
        del entry
        self.resize(self.sizeHint())
        self.sigLevelTableResized.emit(-1)
    
    def state_list_update(self):
        cnt=self.layout.count()
        self.state_list=[]
        for i in range(cnt):
            wid=self.layout.itemAt(i).widget()
            if wid.__class__==LevelRow:
                self.state_list.append(wid.state_dict_update())
        return self.state_list

class PropTabs(QtWidgets.QTabWidget):
    def __init__(self,tabs):
        super().__init__()
        for name in tabs:
            self.addTab(tabs[name],name)
            if tabs[name].__class__==LevelTable:
                tabs[name].sigLevelTableResized.connect(self.refresh)
        self.wsize=self.sizeHint()

    def refresh(self,dir):
        self.wsize.setHeight(self.wsize.height()+50*dir)
        self.resize(self.wsize)

class TabsDialog(QtWidgets.QDialog):
    level_props=dict(width=cfg.LEVELS_WIDTH,color=cfg.D_COLOR,style=cfg.D_LEVELSTYLE)
    def __init__(self,PropD,*args,ItemType=None, wname=None,item=None, preset_levels=None,
        level_props=None,**kwargs):
        super().__init__()
        if wname is not None:
            self.setWindowTitle(wname)
        self.properties=PropD(*args,item=item,**kwargs)
        self.plt=self.properties.plt
        self.ts=self.properties.ts
        self.item=item
        self.ItemType=ItemType
        if level_props is None:
            self.level_props=self.__class__.level_props
        else:
            self.level_props=level_props
        if preset_levels is None:
            if item is not None and 'levels' in item.props:
                preset_levels=item.props['levels']
            else:
                preset_levels=[]
        self.level_table=LevelTable(preset_levels=preset_levels,**self.level_props)
        
        self.tabs=dict(Properties=self.properties,Levels=self.level_table)
        ptabs=PropTabs(tabs=self.tabs)
        layout=QtWidgets.QVBoxLayout()
        layout.addWidget(ptabs)
        self.edb=EmbeddedDialogBox('Reset','Apply','Cancel','Ok',default_button=2)
        layout.addWidget(self.edb)
        self.edb.btn[0].clicked.connect(self.reset_defaults)
        self.edb.btn[2].clicked.connect(self.close)
        if item is None:
            self.edb.btn[1].clicked.connect(lambda *args: self.make_item(_close=False))
            self.edb.btn[3].clicked.connect(lambda *args: self.make_item(_close=True))
        else:           
            self.edb.btn[1].clicked.connect(lambda *args: self.update_item(_close=False))
            self.edb.btn[3].clicked.connect(lambda *args: self.update_item(_close=True))
        self.setLayout(layout)
        self.exec()

    def reset_defaults(self):
        self.properties.reset_defaults()
    
    def make_item(self,_close=False):
        self.item=self.properties.make_item(self.plt,_close=False,
            levels=self.level_table.state_list_update(),**self.properties.state_dict)
        if _close==True:
            self.close()
        else:
            self.edb.btn[1].clicked.disconnect()
            self.edb.btn[3].clicked.disconnect()
            self.edb.btn[1].clicked.connect(lambda *args: self.update_item(_close=False))
            self.edb.btn[3].clicked.connect(lambda *args: self.update_item(_close=True))

    def update_item(self,_close=False):
        self.properties.update_item(_close=False,
            levels=self.level_table.state_list_update())
        if _close==True:
            self.close()

class ElliottPropDialog(PropDialog):
    initials=dict(PropDialog.initials)
    initials['style']=style=cfg.D_EISTYLE
    initials['fontsize']=fontsize=cfg.D_ELSIZE
    initials['color']=color=cfg.D_COLOR
    initials['labeldict']=labeldict=cfg.ELLIOTT_IMPULSE
    def __init__(self,*args,style_on=True,exec_on=True,title='Elliott Impulse',**kwargs):
        props_on=dict(period=False,width=False)
        super().__init__(*args,props_on=props_on,order=2,**kwargs)
        self.setWindowTitle(title)
        self.state_dict['style']=self.__class__.style=self.item.style
        self.state_dict['fontsize']=self.__class__.fontsize=self.item.fontsize
        self.state_dict['labeldict']=self.__class__.labeldict=self.item.labeldict

        label0=QtWidgets.QLabel('Style: ')
        self.stylebox=QtWidgets.QComboBox()
        self.stylebox.insertItems(1,chtl.dict_to_keys(self.labeldict))
        self.stylebox.setCurrentText(self.__class__.style)

        label1=QtWidgets.QLabel('Size: ')
        self.sizebox=QtWidgets.QSpinBox()
        self.sizebox.setMinimum(1)  
        self.sizebox.setValue(self.__class__.fontsize)

        self.order=0
        if style_on==True:
            self.layout.addWidget(label0,self.order,0)
            self.layout.addWidget(self.stylebox,self.order,1)
            self.stylebox.currentTextChanged.connect(lambda *args: setattr(self.__class__,'style',self.stylebox.currentText()))
            self.order+=1
        self.layout.addWidget(label1,self.order,0)
        self.layout.addWidget(self.sizebox,self.order,1)
        self.sizebox.textChanged.connect(lambda *args: setattr(self.__class__,'fontsize',self.sizebox.value()))
        self.order+=1

        if exec_on==True:
            self.order+=1
            self.embedded_db(makeitem=False)
            self.exec()
    
    def set_values(self):
        try:
            self.stylebox.setCurrentText(cfg.D_EISTYLE if self.__class__.style is None else self.__class__.style)
        except Exception:
            pass
        try:
            self.sizebox.setValue(cfg.D_ELSIZE if self.__class__.fontsize is None else self.__class__.fontsize)
        except Exception:
            pass
        return super().set_values()
    
    def update_item(self,_close=True,levels=None):
        a=self.state_dict_update()
        if levels is not None:
            a['levels']=levels
        self.item.set_props(a)
        if _close==True:
            self.close()
        return self.item

class DrawTextDialog(PropDialog):
    initials=dict(PropDialog.initials)
    initials['text']=text=None
    initials['font']=font=None
    initials['fontsize']=fontsize=None
    initials['anchX']=anchX=None
    initials['anchY']=anchY=None
    def __init__(self,*args, exec_on=True,order=5,title='Text',**kwargs):
        
        label0=QtWidgets.QLabel('Text: ')
        self.textbox=QtWidgets.QLineEdit()

        label1=QtWidgets.QLabel('Font: ')
        self.fontbox=QtWidgets.QFontComboBox()

        label2=QtWidgets.QLabel('Font fontsize: ')
        self.fontsizebox=QtWidgets.QSpinBox()

        label3=QtWidgets.QLabel('Anchor X: ')
        label4=QtWidgets.QLabel('Anchor Y: ')
        def anchb(a):
            a.setSingleStep(0.01)
            a.setMinimum(0.00)
            a.setMaximum(1.00)
            a.setDecimals(2)
        self.anchXbox=QtWidgets.QDoubleSpinBox()
        anchb(self.anchXbox)
        self.anchYbox=QtWidgets.QDoubleSpinBox()
        anchb(self.anchYbox)
            
        props_on=dict(period=False,width=False)
        super().__init__(*args, order=order, props_on=props_on,**kwargs)
        self.setWindowTitle(title)
        self.state_dict['text']=self.__class__.text=self.item.text
        self.state_dict['fontsize']=self.__class__.fontsize=self.item.fontsize

        fnt=self.item.font
        if isinstance(fnt,str):
            fnt=QtGui.QFont(fnt)
        self.state_dict['font']=self.__class__.font=fnt

        self.state_dict['anchX']=self.__class__.anchX=self.item.anchX
        self.state_dict['anchY']=self.__class__.anchY=self.item.anchY

        self.order=0
        self.layout.addWidget(label0,self.order,0)
        self.layout.addWidget(self.textbox,self.order,1)
        self.textbox.textChanged.connect(lambda *args: setattr(self.__class__,'text',self.textbox.text()))
        self.order+=1
        self.layout.addWidget(label1,self.order,0)
        self.layout.addWidget(self.fontbox,self.order,1)
        self.fontbox.currentFontChanged.connect(lambda *args: setattr(self.__class__,'font',self.fontbox.currentFont()))
        self.order+=1
        self.layout.addWidget(label2,self.order,0)
        self.layout.addWidget(self.fontsizebox,self.order,1)
        self.fontsizebox.textChanged.connect(lambda *args: setattr(self.__class__,'fontsize',self.fontsizebox.text()))
        self.order+=1
        self.layout.addWidget(label3,self.order,0)
        self.layout.addWidget(self.anchXbox,self.order,1,QtCore.Qt.AlignLeft)
        self.anchXbox.textChanged.connect(lambda *args: setattr(self.__class__,'anchX',self.anchXbox.value()))
        self.order+=1
        self.layout.addWidget(label4,self.order,0)
        self.layout.addWidget(self.anchYbox,self.order,1,QtCore.Qt.AlignLeft)
        self.anchYbox.textChanged.connect(lambda *args: setattr(self.__class__,'anchY',self.anchYbox.value()))
        self.order+=1

        if exec_on==True:
            self.order+=1
            self.set_values()
            self.embedded_db()
            self.exec()

    def set_values(self):
        scl=self.__class__
        if scl.text is not None:
            self.textbox.setText(scl.text)
        if scl.font is not None:
            self.fontbox.setCurrentFont(scl.font)
        if scl.fontsize is not None:
            self.fontsizebox.setValue(int(scl.fontsize))
        if scl.color is not None:         
            self.clrbtn.setStyleSheet(f"background-color: {scl.color}")
        if scl.anchX is not None:        
            self.anchXbox.setValue(float(scl.anchX))
        if scl.anchY is not None:        
            self.anchYbox.setValue(float(scl.anchY))

    def update_item(self,_close=True,levels=None):
        a=self.state_dict_update()
        self.item.set_props(a)
        if _close==True:
            self.close()
        return self.item
    
    # def embedded_db(self): #override without reset button
    #     self.edb=EmbeddedDialogBox('Apply','Cancel','Ok',default_button=1)
    #     self.layout.addWidget(self.edb,self.order,0,1,0)
    #     self.edb.btn[1].clicked.connect(self.close)          
    #     self.edb.btn[0].clicked.connect(lambda *args: self.update_item(_close=False))
    #     self.edb.btn[2].clicked.connect(lambda *args: self.update_item(_close=True))
    
    def reset_defaults(self):
        self.__class__.anchX=0.5
        self.__class__.anchY=0.5
        self.set_values()

class LoginForm(QtWidgets.QDialog):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('Login')
        from importlib.machinery import SourceFileLoader
        self.acct=SourceFileLoader(cfg.ACCT_FILE,cfg.DATA_DIR+cfg.ACCT_FILE).load_module()
        self.api,self.id,self.url='','',''
        self.layout=QtWidgets.QVBoxLayout()
        self.setGeometry(QtCore.QRect(0,0,500,150))
        self.setLayout(self.layout)
        
        label0=QtWidgets.QLabel('API Key:')
        line0=QtWidgets.QLineEdit()
        try:
            line0.setText(self.acct.API_KEY)
            self.api=self.acct.API_KEY
        except:
            pass
        line0.textChanged.connect(lambda *args: setattr(self,'api',line0.text()))
        label1=QtWidgets.QLabel('Account ID:')
        line1=QtWidgets.QLineEdit()
        try:
            line1.setText(self.acct.ACCOUNT_ID)
            self.id=self.acct.ACCOUNT_ID
        except:
            pass
        line1.textChanged.connect(lambda *args: setattr(self,'id',line1.text()))
        label2=QtWidgets.QLabel('URL:')
        line2=QtWidgets.QLineEdit()
        try:
            line2.setText(self.acct.OANDA_URL)
            self.url=self.acct.OANDA_URL
        except:
            pass
        line2.textChanged.connect(lambda *args: setattr(self,'url',line2.text()))

        self.layout.addWidget(label0,0)
        self.layout.addWidget(line0,1)
        self.layout.addWidget(label1,2)
        self.layout.addWidget(line1,3)
        self.layout.addWidget(label2,4)
        self.layout.addWidget(line2,5)

        self.edb=EmbeddedDialogBox('Cancel','Ok',default_button=0)
        self.layout.addWidget(self.edb,6)
        self.edb.btn[0].clicked.connect(self.close)
        self.edb.btn[1].clicked.connect(self.enter)  

        self.exec()

    def enter(self):
        for a in self.api,self.id,self.url:
            a=a.strip()

        with open(f'{cfg.DATA_DIR}acct.py','w') as f:
            f.write(f"API_KEY='{self.api}'\n")
            f.write(f"ACCOUNT_ID='{self.id}'\n")
            f.write(f"OANDA_URL='{self.url}'\n")
        
        self.close()

class ProgressBox(QtWidgets.QProgressDialog):
    def __init__(self,name='',text='In progress...',button=None,min=0,max=5):
        super().__init__(text,button,min,max)
        try:
            self.setWindowTitle(name)
            self.setWindowModality(QtCore.Qt.WindowModal)
            self.show()
            self.setValue(0)
        except Exception as e:
            errBox = QtWidgets.QMessageBox()
            errBox.setWindowTitle('Error')
            errBox.setText('Error: ' + str(e),'. Try again')
            errBox.addButton(QtWidgets.QMessageBox.Ok)
            errBox.exec()
            return

class ChartPropDialog(QtWidgets.QDialog):
    def __init__(self,plt) -> None:
        super().__init__()
        self.setWindowTitle('Chart properties')
        self.plt=plt
        self.order=0
        stylelist=[key for key in cfg.CHARTPROPS]
        startindex=0 #set to "Custom..."
        self.stdprops=stylelist[startindex]
        self.chartprops=dict(self.plt.chartprops)

        self.layout=QtWidgets.QGridLayout()
        self.setLayout(self.layout)

        label0=QtWidgets.QLabel('Color scheme: ')
        self.stdpropsbox=QtWidgets.QComboBox()
        
        self.stdpropsbox.insertItems(1,stylelist)
        self.stdpropsbox.setCurrentIndex(startindex)#Set to 'Custom...'
        self.layout.addWidget(label0,self.order,0)
        self.layout.addWidget(self.stdpropsbox,self.order,1)
        self.stdpropsbox.currentTextChanged.connect(lambda *args: setattr(self,'stdprops',self.stdpropsbox.currentText()))
        self.order+=1

        self.layout.addWidget(QHLine(),self.order,0)
        self.layout.addWidget(QHLine(),self.order,1)
        self.order+=1

        self.clrbtn={}
        for elem in cfg.CHARTPROPSCOLORLIST:
            clrlabel=QtWidgets.QLabel(elem)
            self.clrbtn[elem]=ColorButton("")
            btn=self.clrbtn[elem]
            self.layout.addWidget(clrlabel,self.order,0)
            self.layout.addWidget(btn,self.order,1)
            self.order+=1
        self.update_clrbtns()

        self.layout.addWidget(QHLine(),self.order,0)
        self.layout.addWidget(QHLine(),self.order,1)
        self.order+=1

        label1=QtWidgets.QLabel('Font: ')
        self.fontbox=QtWidgets.QFontComboBox()

        label2=QtWidgets.QLabel('Font size: ')
        self.fontsizebox=QtWidgets.QSpinBox()

        self.layout.addWidget(label1,self.order,0)
        self.layout.addWidget(self.fontbox,self.order,1)
        if self.chartprops[cfg.font] is not None:
            self.fontbox.setCurrentFont(self.chartprops[cfg.font])
        self.fontbox.currentFontChanged.connect(lambda *args: self.setprop(cfg.font,self.fontbox.currentFont()))
        self.order+=1
        self.layout.addWidget(label2,self.order,0)
        self.layout.addWidget(self.fontsizebox,self.order,1)
        fsz=self.chartprops[cfg.fontsize]
        if fsz is None:
            fsz=self.plt.mwindow.app.font().pointSize() #default font size
        self.fontsizebox.setValue(fsz)
        self.fontsizebox.textChanged.connect(lambda *args: self.setprop(cfg.fontsize,self.fontsizebox.value()))
        self.order+=1

        self.embedded_db()
        self.exec()

    def embedded_db(self):
        self.edb=EmbeddedDialogBox('Apply','Cancel','Ok',default_button=0)
        self.layout.addWidget(self.edb,self.order,0,1,0)
        self.edb.btn[0].clicked.connect(self.update_chart)
        self.edb.btn[1].clicked.connect(self.close)
        self.edb.btn[2].clicked.connect(lambda *args: self.update_chart(_close=True))
    
    def setprop(self,key,value):
        self.chartprops[key]=value
    
    def update_chart(self,_close=False):
        if cfg.CHARTPROPS[self.stdprops] is not None:
            for key,val in cfg.CHARTPROPS.items():
                if key==self.stdprops:
                    self.plt.set_chartprops(props=val,meta=True)
                    self.chartprops=self.plt.chartprops
                    self.fontbox.setCurrentFont(self.chartprops[cfg.font])
                    self.fontsizebox.setValue(self.chartprops[cfg.fontsize])
                    break
        else:
            for key,val in self.clrbtn.items():
                self.chartprops[key]=val.btncolor
            self.plt.set_chartprops(props=self.chartprops,meta=True)   
        if _close:
            self.close()
        else:
            self.update_clrbtns()   

    def update_clrbtns(self):
        for elem in cfg.CHARTPROPSCOLORLIST:
            clr=chtl.pgclr_to_hex(self.plt.chartprops[elem])
            self.clrbtn[elem].update_color(clr)

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self,mwindow) -> None:
        super().__init__()
        self.setWindowTitle('Settings')
        self.mwindow=mwindow
        self.tmr=self.timer
        self.cnt=self.count
        self.layout=QtWidgets.QGridLayout()
        self.setLayout(self.layout)
        self.labels=[]

        self.theme=self.mwindow.props['theme']
        self.labels.append(QtWidgets.QLabel('Theme: '))
        self.themebox=QtWidgets.QComboBox()
        self.themebox.addItems(cfg.THEMES.values())
        self.themebox.setCurrentText(self.theme)
        self.attach(self.themebox)
        self.themebox.currentTextChanged.connect(lambda *args: setattr(self,'theme',self.themebox.currentText()))

        self.labels.append(QtWidgets.QLabel('Server query periodicity,ms: '))
        pbox=QtWidgets.QSpinBox()
        pbox.setMaximum(1000000)
        pbox.setMinimum(1)
        pbox.setValue(self.timer)
        self.attach(pbox)
        pbox.textChanged.connect(lambda *args: setattr(self,'tmr',pbox.value()))

        self.labels.append(QtWidgets.QLabel('Server query count,bars: '))
        cbox=QtWidgets.QSpinBox()
        cbox.setMaximum(10000)
        cbox.setMinimum(3)
        cbox.setValue(self.count)
        self.attach(cbox)
        cbox.textChanged.connect(lambda *args: setattr(self,'cnt',cbox.value()))


        pmap=QtWidgets.QStyle.StandardPixmap
        pixmapi = getattr(pmap,f'SP_DialogDiscardButton')

        self.labels.append(QtWidgets.QLabel('Clear cache:'))
        btn2=QtWidgets.QPushButton('Clear cache')
        icon2 = self.style().standardIcon(pixmapi)
        btn2.setIcon(icon2)
        btn2.setAutoDefault(False)
        self.attach(btn2)
        btn2.clicked.connect(self.clear_cache)

        self.labels.append(QtWidgets.QLabel('Clear history:'))
        btn3=QtWidgets.QPushButton('Clear history')
        icon3 = self.style().standardIcon(pixmapi)
        btn3.setIcon(icon3)
        btn3.setAutoDefault(False)
        self.attach(btn3)
        btn3.clicked.connect(self.clear_history)

        edb=EmbeddedDialogBox('Reset','Apply','Cancel','Ok',default_button=2)
        self.layout.addWidget(edb,len(self.labels)+1,0,1,0)
        edb.btn[0].clicked.connect(lambda *args: (pbox.setValue(cfg.D_TIMER),cbox.setValue(cfg.D_BARCOUNT)))
        edb.btn[1].clicked.connect(self.apply)
        edb.btn[2].clicked.connect(self.close)
        edb.btn[3].clicked.connect(lambda *args: self.apply(close=True))

        self.exec()
    
    @property
    def timer(self):
        return self.mwindow.props['timer']

    @timer.setter
    def timer(self,x):
        self.mwindow.props['timer']=x
    
    @property
    def count(self):
        return self.mwindow.props['count']
    
    @count.setter
    def count(self,x):
        self.mwindow.props['count']=x

    def attach(self,wdg):
        self.layout.addWidget(self.labels[-1],n:=len(self.labels),0)
        self.layout.addWidget(wdg,n,1)

    def apply(self,close=False):
        import styles
        if self.timer!=self.tmr:
            self.timer=self.tmr
            for wnd in (mw:=self.mwindow).mdi.subWindowList():
                mw.mdi.setActiveSubWindow(wnd)
                mw.window_act('Refresh')
        if self.count!=self.cnt:
            self.count=self.cnt
        (mw:=self.mwindow).props['theme']=self.theme
        mw.set_theme()
        #workaround maximized button widget illigebility in "Darker"
        if (asw:=mw.mdi.activeSubWindow()) is not None and\
            (mbw:=asw.maximizedButtonsWidget()) is not None:
            if mw.props['theme']=='Darker':
                mbw.setStyleSheet('background-color:'+styles.darker_mbw)
            else: mbw.setStyleSheet("")
        if close:
            self.close()

    def clear_cache(self):
        txt='WARNING! This will wipe out your charts and restore original configuration. '
        txt+='Be sure to back up your charts prior to clicking "Apply" button.'
        cc=dialog_message_box(title='Clear cache',text=txt,
            icon=QtWidgets.QMessageBox.Critical,default_button=QtWidgets.QMessageBox.Cancel,
            action_button=QtWidgets.QMessageBox.Apply)
        if cc==QtWidgets.QMessageBox.Apply:
            import os
            for root,dirs,files in os.walk(cfg.DATA_STATES_DIR):
                for f in files:
                    if '.py' not in f:
                        os.remove(cfg.DATA_STATES_DIR+f)
            (mw:=self.mwindow).props=cfg.D_METAPROPS
            mw.pstate=[]
            for subw in mw.mdi.subWindowList():
                mw.mdi.removeSubWindow(subw)

    def clear_history(self):
        txt='WARNING! This will wipe out the entire symbols history.'
        cc=dialog_message_box(title='Clear history',text=txt,
            icon=QtWidgets.QMessageBox.Critical,default_button=QtWidgets.QMessageBox.Cancel,
            action_button=QtWidgets.QMessageBox.Apply)
        if cc==QtWidgets.QMessageBox.Apply:
            import os
            for root,dirs,files in os.walk(cfg.DATA_SYMBOLS_DIR):
                for f in files:
                    if '.py' not in f and 'MODEL' not in f:
                        os.remove(cfg.DATA_SYMBOLS_DIR+f)

class TreeSubWindow(QtWidgets.QMdiSubWindow):
    def __init__(self,mwindow) -> None:
        self.mwindow=mwindow
        self.mdi=mwindow.mdi
        for sw in self.mdi.subWindowList():#ensure no duplication
            if isinstance(sw,TreeSubWindow):
                return
        super().__init__()
        self.setWindowTitle("User Apps")
        self.is_persistent=True
        self.tree=QtWidgets.QTreeView()
        self.setWidget(self.tree)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.context_menu)
        self.populate()
        self.mdi.addSubWindow(self)
        self.show()

    def context_menu(self):
        menu = QtWidgets.QMenu()
        addapp = menu.addAction('Add')
        addapp.triggered.connect(self.add_app)
        update_shorcuts=menu.addAction('Update Shortcuts')
        update_shorcuts.triggered.connect(self.mwindow.update_api_shortcuts)
        cursor = QtGui.QCursor()
        menu.exec(cursor.pos())

    def populate(self):
        self.model = QtWidgets.QFileSystemModel()
        self.model.setRootPath((QtCore.QDir.rootPath()))
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(cfg.APP_DIR))
        self.tree.setSortingEnabled(True)

    def add_app(self):
        import api
        from os import path
        index = self.tree.currentIndex()
        if not self.model.isDir(index):
            fpath= path.relpath(self.model.filePath(index))
            fname=path.basename(fpath)
            api.invoker(self.mdi,fname,fpath)        

    def closeEvent(self, closeEvent: QtGui.QCloseEvent) -> None:
        self.mdi.removeSubWindow(self)
        return super().closeEvent(closeEvent)

class HistoryDialog(QtWidgets.QDialog):
    def __init__(self, mwindow):
        super().__init__()
        self.mwindow=mwindow
        self.title="History Download"
        self.setWindowTitle("History Download")
        pmap=QtWidgets.QStyle.StandardPixmap

        # Number of bars spin box
        self.num_bars_label = QtWidgets.QLabel("Number of Timeframe Periods (including off-market):")
        self.num_bars_spinbox = QtWidgets.QSpinBox()
        self.num_bars_spinbox.setMaximum(10000000)

        # Ticker checkboxes
        self.ticker_checkboxes = []
        timeframes = cfg.TIMEFRAMES
        for timeframe in timeframes:
            checkbox = QtWidgets.QCheckBox(timeframe)
            self.ticker_checkboxes.append(checkbox)

        # Action buttons
        self.all_button = QtWidgets.QPushButton("All")
        self.reset_button = QtWidgets.QPushButton("Reset")
        pixmapi = getattr(pmap,f'SP_DialogResetButton')
        icon = self.style().standardIcon(pixmapi)
        self.reset_button.setIcon(icon)
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        pixmapi = getattr(pmap,f'SP_DialogCancelButton')
        icon = self.style().standardIcon(pixmapi)
        self.cancel_button.setIcon(icon)
        self.ok_button = QtWidgets.QPushButton("OK")
        pixmapi = getattr(pmap,f'SP_DialogOkButton')
        icon = self.style().standardIcon(pixmapi)
        self.ok_button.setIcon(icon)

        # Connect button signals
        self.all_button.clicked.connect(self.toggle_all_timeframes)
        self.reset_button.clicked.connect(self.reset_dialog)
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.download_history)

        # Dialog layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.num_bars_label)
        layout.addWidget(self.num_bars_spinbox)

        grid_layout = QtWidgets.QGridLayout()
        for i, checkbox in enumerate(self.ticker_checkboxes):
            grid_layout.addWidget(checkbox, i // 3, i % 3)
        layout.addLayout(grid_layout)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.all_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.reset_dialog()

        self.exec()

    def _get_checked_timeframes(self):
        checked_timeframes = []
        for checkbox in self.ticker_checkboxes:
            if checkbox.isChecked():
                checked_timeframes.append(checkbox.text())
        return checked_timeframes

    def toggle_all_timeframes(self):
        any_checked = any(checkbox.isChecked() for checkbox in self.ticker_checkboxes)
        for checkbox in self.ticker_checkboxes:
            checkbox.setChecked(not any_checked)

    def reset_dialog(self):
        self.num_bars_spinbox.setValue(0)
        default_timeframes = ["M1", "M5", "M15","M30","H1","H4","D1","W1"]  # Default timeframes to be ticked
        for checkbox in self.ticker_checkboxes:
            checkbox.setChecked(checkbox.text() in default_timeframes)
    
    def download_history(self):
        plt=self.mwindow.mdi.activeSubWindow().plt
        symbol=plt.symbol
        checked_timeframes=self._get_checked_timeframes()
        num_bars=self.num_bars_spinbox.value()
        
        checked_timeframes={name: cfg.TIMEFRAMES[name] for name in checked_timeframes}
        tflen=len(checked_timeframes)
        if tflen<1:
            simple_message_box(title=self.title,text="No timeframe selected")
            self.close()
        pbox=ProgressBox(name='History',text='Loading history',max=tflen-1)
        for i,tf in enumerate(checked_timeframes.values()):
            if tf!=cfg.PERIOD_MN:
                hst=ftch.history(tf,symbol,bars=num_bars)
                if hst is True:
                    pbox.setValue(i)
                    lbl=cfg.tf_to_label(tf)
                    pbox.setLabelText(f'Loading history: {symbol},{lbl}')
                elif hst is False:
                    pass
                else:
                    pbox.close()
                    simple_message_box(title=self.title,
                        text=f'Loading error: check connection and try again: {hst}')
                    break
        self.mwindow.window_act('Refresh')
        self.close()
            