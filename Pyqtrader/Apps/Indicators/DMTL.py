from Pyqtrader.Apps import lib

PQitemtype='TrendLineIndicator'

UPTRENDCOLOR='g'
DOWNTRENDCOLOR='orange'
TRENDWIDTH=2
NONTRENDWIDTH=1
TRENDSTYLE=lib.SolidLine
NONTRENDSTYLE=lib.DotLine
BARSBACK=48

NT_PROPS=dict(width=NONTRENDWIDTH,style=NONTRENDSTYLE)
T_PROPS=dict(width=TRENDWIDTH,style=TRENDSTYLE)

PQkwords=dict(width=TRENDWIDTH) #an alternative is PQtline.set_properties(width=TRENDWITH) in PQinitf

def PQinitf(PQtline):
    PQtline.create_subitem('TrendLine')
    si=PQtline.subitems[0]
    si.item_hide()

def calc_points(PQtline):
    s=PQtline.series
    times=lib.normalised_series(s,earliest=BARSBACK)
    highs=lib.normalised_series(s,'highs',earliest=BARSBACK)
    lows=lib.normalised_series(s,'lows',earliest=BARSBACK)
    closes=lib.normalised_series(s,'closes',earliest=BARSBACK)
    high1,high2,low1,low2=None,None,None,None

    def nextprice(point1,point2,nextpoint):
        dp=[x-y for x,y in zip(point1,point2)]
        gradient=dp[1]/dp[0]
        targettime=nextpoint[0]-point2[0]
        targetprice=targettime*gradient
        price=point2[1]+targetprice
        return price

    for i,h in enumerate(highs): #test downtrend line
        if 2<=i<=BARSBACK:
            if highs[i+1]<h>highs[i-1] and h>closes[i+2]: #condition 1 and condition 2
                if high1 is None: 
                    high1=[times[i],h]
                    nexthigh=[times[i-1],closes[i-1]]
                elif high2 is None and h>high1[1]: #earlier high should be higher than the later one
                    high2=[times[i],h]
                    np=nextprice(high1,high2,nexthigh)
                    if nexthigh[1]<np: 
                        break #condition 3
                    else:
                        high1=high2
                        nexthigh=[times[i-1],closes[i-1]]
                        high2=None
    for i,l in enumerate(lows): #test uptrend line
        if 2<=i<=BARSBACK:
            if lows[i+1]>l<lows[i-1] and l<closes[i+2]: #condition 1 and condition 2
                if low1 is None: 
                    low1=[times[i],l]
                    nextlow=[times[i-1],closes[i-1]]
                elif low2 is None and l<low1[1]: #earlier low should be lower than the later one
                    low2=[times[i],l]
                    np=nextprice(low1,low2,nextlow)
                    if nextlow[1]>np: 
                        break #condition 3
                    else:
                        low1=low2
                        nextlow=[times[i-1],closes[i-1]]
                        low2=None

    high=high1 is not None and high2 is not None
    low=low1 is not None and low2 is not None
    res=None

    si=PQtline.subitems[0]

    def _show(*items):
        for it in items:
            if not it.isVisible(): it.item_show(selected=False)
    
    def _hide(*items):
        for it in items:
            if it.isVisible(): it.item_hide(selected=False)

    def set_downtrend():
        PQtline.set_properties(color=DOWNTRENDCOLOR)
        if low:
            si.set_data([low1,low2])
            si.set_properties(color=UPTRENDCOLOR,**NT_PROPS)
        return high1,high2
    
    def set_uptrend():
        PQtline.set_properties(color=UPTRENDCOLOR)
        if high:
            si.set_data([high1,high2])
            si.set_properties(color=DOWNTRENDCOLOR,**NT_PROPS)
        return low1,low2
    
    def set_both():
        PQtline.set_properties(color=UPTRENDCOLOR)
        si.set_properties(colow=DOWNTRENDCOLOR,**T_PROPS)
        return low1,low2

    def set_neither():
        return None

    if high:
        if low:
            _show(PQtline,si)
            if high1[0]>low1[0]: res=set_downtrend()
            elif high1[0]==low1[0]: res=set_both()
            else: res=set_uptrend()        
        else:
            _show(PQtline)
            _hide(si) 
            res=set_downtrend()
    elif low: 
        _show(PQtline)
        _hide(si)
        res=set_uptrend()
    else: 
        _hide(PQtline,si)
        res=set_neither()
    PQtline.set_selected(False)
    si.set_selected(False)
    return res

def PQcomputef(PQtline):
    pts=calc_points(PQtline)
    return pts