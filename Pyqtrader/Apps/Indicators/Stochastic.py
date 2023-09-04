from Pyqtrader.Apps.lib import *

PQitemtype='CurveIndicator'

_K=5
_SLOW=3
_D=3
WIDTH=1
COLOR='#55aa7f'
WIDTH_D=1
COLOR_D='#cc0000'
FREEZE=True
FREEZE_RANGE=[0,100]
LEVELS=[{'show': True, 'value': 80.0, 'width': 0.2, 'style': '....',
'color': '#ffffff', 'desc_on': False, 'removable': False}, 
{'show': True, 'value': 20.0, 'width': 0.2, 'style': '....',
'color': '#ffffff', 'desc_on': False, 'removable': False}]

PQkwords=dict(windowed=True,width=WIDTH,color=COLOR,freeze=FREEZE,
    freeze_range=FREEZE_RANGE,levels=LEVELS)

def PQinitf(PQitem):
    yv_d=calc_sma(PQitem.yvalues,period=_D)
    PQitem.create_subitem('Curve',yv_d)
    PQitem.subitems[0].setPen(dict(width=WIDTH_D,color=COLOR_D))

def PQcomputef(PQitem):
    series=PQitem.series
    highs=series.highs
    lows=series.lows
    closes=series.closes
    y = []
    lng=len(closes)
    st=lng-2-_K-_SLOW-_D if PQitem.cache_event else _K #caching processing
    for i in range(st,lng):
        highest=max(highs[i+1-_K:i+1])
        lowest=min(lows[i+1-_K:i+1])
        res=100*(closes[i]-lowest)/(highest-lowest) if highest-lowest!=0 else 50
        y.append(res)

    res=calc_sma(y,period=_SLOW)
    return res

def PQreplot(PQitem):
    start=-2-_D if PQitem.cache_event else None #preceds mredraw() to ensure execution before 
                                         #self.cache_event is reset
    PQitem.mreplot()
    yv_d=calc_sma(PQitem.yvalues[start:],period=_D)
    if PQitem.subitems != []:
        si=PQitem.subitems[0]
        si.update_subitem(yv_d)        

def PQstudylabel(PQitem):
    v=PQitem.yvalues
    v2=None if len(sis:=PQitem.subitems)==0 else sis[0].yvalues
    if v is None or v2 is None:
        res='Stoch({},{},{})'.format(_K,_SLOW,_D)
    else:
        v=v[-1]
        v2=v2[-1]
        res='Stoch({},{},{}) {:.{pr}f} {:.{pr}f}'.format(_K,_SLOW,_D,v,v2,pr=2)
    return res

def PQtooltip(PQitem):
    index,xtext,ytext,precision=PQitem.tooltipinfo
    index1=index-(len(PQitem.yvalues)-len((si:=PQitem.subitems[0]).yvalues))
    v_d=si.yvalues[index1]
    return '{}({},{},{})\n{}\n%K:{:.{pr}f}\n%D:{:.{pr}f}'.format(PQitem.fname,_K,_SLOW,_D,
        xtext,ytext,v_d,pr=2)