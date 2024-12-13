PQitemtype='Script'

PQshortcut='Ctrl+L'

def PQinitf(PQscript):
    PQscript.create_subitem('Label',text='!@tk, !@tf', ignoreBounds=True)
    si=PQscript.subitems[0]
    si.set_bind('br')
    si.setState([0,0])
    si.set_anchor(1,0.75)
    si.setColor(color='#aa0000')
    si.set_fontsize(24)
    si.set_bold(True)
    si.set_frozen(True)
    si.set_persistent(True)
    