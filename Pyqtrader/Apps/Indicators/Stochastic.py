from pandas_ta import stoch
from cfg import DOTLINE

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
LEVELS=[{'show': True, 'value': 80.0, 'width': 0.2, 'style': DOTLINE,
'color': '#ffffff', 'desc_on': False, 'removable': False}, 
{'show': True, 'value': 20.0, 'width': 0.2, 'style': DOTLINE,
'color': '#ffffff', 'desc_on': False, 'removable': False}]

PQkwords=dict(windowed=True,width=WIDTH,color=COLOR,freeze=FREEZE,
    freeze_range=FREEZE_RANGE,levels=LEVELS)

def PQinitf(PQitem):
    df=PQitem.timeseries.data
    yvals_d=stoch(df.h,df.l,df.c,k=_K,d=_D,smooth_k=_SLOW).iloc[:,1].dropna().to_numpy()
    PQitem.create_subitem('Curve',values=yvals_d)
    PQitem.subitems[0].setPen(dict(width=WIDTH_D,color=COLOR_D))

def PQcomputef(PQitem):
    df=PQitem.timeseries.data
    
    ins=df[-2-(_K+_SLOW+_D) if PQitem.cache_event else None:]

    s=stoch(ins.h,ins.l,ins.c,k=_K,d=_D,smooth_k=_SLOW)

    yvals_d=s.iloc[:,1].dropna().to_numpy()
    if len(PQitem.subitems)>0:
        PQitem.subitems[0].update_subitem(yvals_d) 

    return s.iloc[:,0].dropna().to_numpy()

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