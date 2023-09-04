
SolidLine='____'
DashLine='_ _ _'
DotLine='....'
DashDotLine='_._.'
DashDotDotLine='_.._'

def inputs(series,mode='close',start=None,end=None):
    res=getattr(series,mode.lower()+'s')
    return res[start:end]

def normalised_series(series,attr='times',latest=None,earliest=None):
    if earliest==0:
        earliest=None
    s=attr.lower()
    v=getattr(series,s)
    rv=[x for x in reversed(v[earliest:latest])]
    return rv

#Simple moving average calculation    
def calc_sma(ins,period):
    yres = []
    def sma(i):
        return sum(ins[i-period+1:i+1])/period
    
    for ind,val in enumerate(ins):
        if ind>=period-1:
            s=sma(ind)
            yres.append(s)
    
    return yres

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

#RSI calculation
def calc_rsi(ins,period=14): #recommended bars back number for ins for period==14 is 150 
    yres = []
    up,down=0,0
    values=ins
    for i in range(period): #calculate the first element
        diff=values[i+1]-values[i]
        if diff<0:
            down+=-diff
        else:
            up+=diff
    up/=period
    down/=period
    if down!=0:
        rs0=100*(1-(1/(1+up/down)))
    elif up!=0:
        rs0=100
    else:
        rs0=50
    yres.append(rs0)
    
    values=values[period+1:]

    for i,value in enumerate(values[:-1]):#main loop
        diff=values[i+1]-value
        up=(up*(period-1)+(diff if diff>0 else 0))/period
        down=(down*(period-1)+(-diff if diff<0 else 0))/period
        if down!=0:
            rs=100*(1-(1/(1+up/down)))
        elif up!=0:
            rs=100
        else:
            rs=50
        yres.append(rs)
    return yres

def calc_bands(ins,period=20,multi=2):
    from numpy import sqrt #requires numpy package to be installed
    up,down=[],[]
    mas=calc_sma(ins,period)
    diff=len(ins)-len(mas)
    for i,val in enumerate(mas):
        dev=0
        for j in range(period):
            dev+=pow(ins[i+diff-j]-val,2)
        dev=sqrt(dev/period)
        up.append(val+multi*dev)
        down.append(val-multi*dev)
    return mas,up,down
