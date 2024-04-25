PQitemtype='TextIndicator'

BARSBACK=50
TOP='\u2B99'
BOTTOM='\u2B9B'
TOPANCHOR=0.8
BOTTOMANCHOR=0.1

def logic(PQtext,i):
    s=PQtext.series
    top,bottom=False,False
    sh=s.highs
    if sh[i-1]<sh[i]>sh[i+1] and sh[i-2]<sh[i]>sh[i+2]:
        top=True
    sl=s.lows
    if sl[i-1]>sl[i]<sl[i+1] and sl[i-2]>sl[i]<sl[i+2]:
        bottom=True
    return top, bottom

def mark(PQtext,itm,i,top):
    s=PQtext.series
    if top: yanch=TOPANCHOR; txt=TOP; vals=[s.times[i],s.highs[i]]
    else: yanch=BOTTOMANCHOR; txt=BOTTOM; vals=[s.times[i],s.lows[i]]
    itm.set_data(vals)
    itm.set_text(txt)
    itm.set_anchor(x=0.5,y=yanch)

def place_marks(PQtext,limit=-BARSBACK):
    for i in range(limit,-2): #-2 as requires 2 bars both ways; first identify main item position
        lgc=logic(PQtext,i)
        if lgc[0]:
            mark(PQtext,PQtext,i,True)
            starttop=True
            newstart=i
            break
        elif lgc[1]:
            mark(PQtext,PQtext,i,False)
            starttop=False
            newstart=i
            break

    for i in range(newstart,-2): #identify subitems' positions
        lgc=logic(PQtext,i)
        if lgc[0]:
            if i==newstart and not starttop: pass
            else:
                si=PQtext.create_subitem('Text')
                mark(PQtext,si,i,True)
        elif lgc[1]:
            if i==newstart and starttop: pass
            else:
                si=PQtext.create_subitem('Text')
                mark(PQtext,si,i,False)

def remove_marks(PQtext):
    for si in list(PQtext.subitems):
        PQtext.remove_subitem(si)

def PQinitf(PQtext):
    place_marks(PQtext)
    PQtext.sigSeriesChanged.connect(PQupdatef)

def PQupdatef(PQtext):
    remove_marks(PQtext)
    place_marks(PQtext)

def PQcomputef(PQtext):
    for i in -4,-3: #last and interim (the one before the last) candles shifted by 2
        te=logic(PQtext,i)
        already_exists=False
        for si in PQtext.subitems:
            if si.get_data()[0]==PQtext.series.times[i]:
                if not te[0] and not te[1]:
                    PQtext.remove_subitem(si)
                elif te[0] and si.text==BOTTOM:
                    mark(PQtext,si,i,True)
                elif not te[0] and si.text==TOP:
                    PQtext.remove_subitem(si)
                elif te[1] and si.text==TOP:
                    mark(PQtext,si,i,False)
                elif not te[1] and si.text==BOTTOM:
                    PQtext.remove_subitem(si)
                already_exists=True
                break
        if not already_exists:
            if te[0]:
                newsi=PQtext.create_subitem('Text')
                mark(PQtext,newsi,i,True)
            if te[1]:
                newsi=PQtext.create_subitem('Text')
                mark(PQtext,newsi,i,False)
                