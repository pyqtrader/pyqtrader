PQitemtype='CurveIndicator'

PERIODFAST=12
WIDTHFAST=1
COLORFAST='#55aa7f'
PERIODSLOW=26
PERIODSIGNAL=9
WIDTHSIGNAL=1
COLORSIGNAL='#cc0000'
WIDTHHIST=0.3

PQkwords=dict(windowed=True,width=WIDTHFAST,color=COLORFAST)
PQcache0=dict(v01=None,v02=None,sgn_v0=None,hist_c=None)

def PQinitf(PQitem):
    yvs_signal=calc_ema(PQitem.values[1],period=PERIODSIGNAL)
    PQitem.cache0['sgn_v0']=yvs_signal[-3] #initial value for caching purposes
    PQitem.create_subitem('Curve',values=yvs_signal)
    PQitem.subitems[0].setPen(dict(width=WIDTHSIGNAL,color=COLORSIGNAL))
    PQitem.subitems[0].setZValue(0)
    dkvb=PQitem.getViewBox()
    rct=dkvb.viewRect()
    hist=calc_hist(PQitem)
    PQitem.create_subitem('Bar',values=hist,width=WIDTHHIST)
    PQitem.subitems[1].setZValue(-1)
    dkvb.setRange(rect=rct,padding=0) 
    PQitem.set_label()

    PQitem.sigSeriesChanged.connect(update_hist_width)

def calc_hist(PQitem):
    st=len(PQitem.values[1])-len(PQitem.subitems[0].values[0])
    v=PQitem.values[1][st:]
    if PQitem.cache_event and len(PQitem.subitems)<2 and PQitem.cache0['hist_c']:
        ts_diff=len(v)-len(PQitem.subitems[1])
        st=-3-ts_diff
        v=v[st:]
    else:
        PQitem.cache0['hist_c']=True
    s=PQitem.subitems[0].values[1][-len(v):]
    hist=[a_i - b_i for a_i, b_i in zip(v, s)]
    return hist

def update_hist_width(PQitem):
        PQitem.subitems[1].opts['width']=WIDTHHIST*PQitem.ts.tf
        PQitem.subitems[1].setOpts()

def PQcomputef(PQitem):
    def cached_ma(ins,period,v0=None):
            start=-3-PQitem.ts_diff if PQitem.cache_event else None
            ins=list(ins[start:])
            yvals=calc_ema(ins,period=period,v0=v0)
            return yvals

    series=PQitem.series
    ins=series.closes
    y=[]
    if PQitem.cache_event:
        d1=0
        d2=0
    else:
        delta=PERIODSLOW-PERIODFAST
        d1=delta if delta>0 else 0
        d2=delta if delta<0 else 0
        PQitem.cache0['v01']=None
        PQitem.cache0['v02']=None
    ema1=cached_ma(ins,PERIODFAST,v0=PQitem.cache0['v01'])
    PQitem.cache0['v01']=ema1[-3]
    ema2=cached_ma(ins,PERIODSLOW,v0=PQitem.cache0['v02'])
    PQitem.cache0['v02']=ema2[-3]
    if PQitem.cache_event:
        rn=range(-3-PQitem.ts_diff,0)
    else:
        rn=range(min(len(ema1),len(ema2)))
    for i in rn:
        y.append(ema1[i+d1]-ema2[i+d2])
    return y

def PQreplot(PQitem):
    st=None
    if PQitem.cache_event and PQitem.cache0['sgn_v0'] is not None:
        st=-3-PQitem.ts_diff
    if len(PQitem.subitems)>0:
        ins=PQitem.values[1][st:]
        yvals_signal=calc_ema(ins,PERIODSIGNAL,v0=PQitem.cache0['sgn_v0'])
        PQitem.sgn_v0=yvals_signal[-3] if yvals_signal!=[] else None
        PQitem.subitems[0].update_subitem(yvals_signal)        
        hist=calc_hist(PQitem)
        PQitem.subitems[1].update_subitem(hist)

def PQstudylabel(PQitem):
    v=PQitem.yvalues
    v2=None if len(sis:=PQitem.subitems)==0 else sis[0].yvalues
    v3=None if len(sis)<2 else sis[1].yvalues
    if v is None or v2 is None or v3 is None: 
        res='MACD({},{},{})'.format(PERIODFAST,PERIODSLOW,PERIODSIGNAL)
    else:
        v=v[-1]
        v2=v2[-1]
        v3=v3[-1]
        res='MACD({},{},{}) {:.{pr}f} {:.{pr}f} {:.{pr}f}'.format(PERIODFAST,PERIODSLOW,PERIODSIGNAL,
            v,v2,v3,pr=5)
    return res

def PQtooltip(PQitem):
    index,xtext,ytext,precision=PQitem.tooltipinfo
    index1=index-(len(PQitem.yvalues)-len((si:=PQitem.subitems[0]).yvalues))
    v_d=si.yvalues[index1]
    return '{}({},{},{})\n{}\nMACD:{:.{pr}f}\nSignal:{:.{pr}f}'.format(PQitem.fname,
        PERIODFAST,PERIODSLOW,PERIODSIGNAL,xtext,ytext,v_d,pr=precision)

#Exponential moving average calculation
def calc_ema(ins,period,v0=None):
    yres=[]
    def sma(i):
        return sum(ins[i-period+1:i+1])/period
    k=2/(period+1)
    for ind,val in enumerate(ins):
        if v0 is None:
            if ind>=period-1:
                if ind==period-1:
                    e=sma(ind)
                else:
                    e=val*k+e*(1-k)
                yres.append(e)
        else: 
            if ind==0: #caching
                e=v0
            else:
                e=val*k+e*(1-k)
            yres.append(e)
    return yres