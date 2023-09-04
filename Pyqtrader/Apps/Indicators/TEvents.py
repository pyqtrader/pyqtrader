from Pyqtrader.Apps import lib

PQitemtype='TextIndicator'

BARSBACK=20
OUTSIDE='\u00D8'
INSIDE='\u03C3'
KEYUP='\u2206'
KEYDOWN='\u2207'
UPCOLOR='g'
DOWNCOLOR='r'
TOPANCHOR=1
BOTTOMANCHOR=0

def logic(PQtext,i):
    s=PQtext.series
    if s.highs[i]>s.highs[i-1] and s.lows[i]<s.lows[i-1]:
        if s.closes[i]>s.opens[i]: return 'ou'
        elif s.closes[i]<s.opens[i]: return 'od'
        else: return None
    elif s.highs[i]<=s.highs[i-1] and s.lows[i]>=s.lows[i-1]:
        if s.closes[i]>s.opens[i]: return 'iu'
        elif s.closes[i]<s.opens[i]: return 'id'
        else: return None
    elif s.highs[i]>s.highs[i-1] and s.closes[i-1]>s.closes[i]:
        return 'kd'
    elif s.lows[i]<s.lows[i-1] and s.closes[i-1]<s.closes[i]:
        return 'ku'
    else: return None

def params(PQtext,i,te):
    if te is None: return None
    s=PQtext.series
    t,h,l=s.times[i],s.highs[i],s.lows[i]
    size=10
    if te[0]=='o': txt=OUTSIDE
    elif te[0]=='i': txt=INSIDE
    elif te[0]=='k':
        size-=1
        if te[1]=='u': txt=KEYUP
        elif te[1]=='d': txt=KEYDOWN
    if te[1]=='u':
        cl=UPCOLOR
        yanch=BOTTOMANCHOR
        vals=[t,l]
    elif te[1]=='d':
        cl=DOWNCOLOR
        yanch=TOPANCHOR
        vals=[t,h]

    return txt,vals,cl,yanch,size
    
def place(PQtext,txt,vals,cl,yanch,size,subitem=False):
    if subitem: itm=PQtext.create_subitem('Text',values=vals,text=txt)
    else: itm=PQtext; itm.set_data(vals),itm.set_text(txt)
    itm.set_anchor(x=0.5,y=yanch)
    itm.setColor(color=cl)
    itm.set_fontsize(size)
    return itm

def refresh(itm,txt,vals,cl,yanch,size):
    if itm.text!=txt: itm.set_text(txt)
    if itm.color!=cl: itm.setColor(cl)
    if itm.anchY!=yanch: itm.set_anchor(y=yanch)
    if itm.fontsize!=size: itm.setfontsize(size)

def place_marks(PQtext,limit=BARSBACK):
    #find the first element to set the main item
    newstart=-limit
    if PQtext.subitems==[]:
        for i in range(limit,0):
            te=logic(PQtext,i)
            if te is not None:
                pm=params(PQtext,i,te)
                place(PQtext,*pm)
                newstart=i+1
                break
    for i in range(newstart,0):
        te=logic(PQtext,i)
        already_exists=False
        if te is not None:
            for si in PQtext.subitems: #computef functionality
                if si.get_data()[0]==PQtext.series.times[i]: 
                    already_exists=True
                    break
            if not already_exists:
                pm=params(PQtext,i,te)
                place(PQtext,*pm,subitem=True)

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
    for si in PQtext.subitems:
        for i in -2,-1: #last and interim (the one before the last) candles
            if si.get_data()[0]==PQtext.series.times[i]:
                te=logic(PQtext,i)
                if te is not None:
                    pm=params(PQtext,i,te)
                    refresh(si,*pm)
                else:
                    PQtext.remove_subitem(si)
    place_marks(PQtext,limit=2) #add either of last two labels if they are not present but should be            

# def deinitf(PQtext):
#     PQtext.sigSeriesChanged.disconnect(PQupdatef)