PQitemtype='Script'

def PQinitf(PQscript):
    s=PQscript.series
    t=s.times[-2]
    h=s.highs[-2]
    l=s.lows[-2]
    PQscript.create_subitem('Text',values=(t,h),text='High')
    si=PQscript.subitems[0]
    si.set_anchor(x=0.5,y=1)
    si.setColor(color='y')
    PQscript.create_subitem('Text',values=(t,l),text='Low')
    si=PQscript.subitems[1]
    si.set_anchor(x=0.5,y=0)
    si.setColor(color='y')