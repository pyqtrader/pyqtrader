import pandas_ta as ta

PQitemtype='Expert'

SMAPERIOD=9

def PQinitf(PQexpert):
    s=PQexpert.series
    PQexpert.Current_Time=s.times[-1]
    PQexpert.Sma_Value=sum(s.closes[-SMAPERIOD-1:])/SMAPERIOD

def PQexecutef(PQexpert):
    s=PQexpert.series
    if PQexpert.Current_Time!=s.times[-1]:
        PQexpert.Current_Time=s.times[-1]
        cc2=s.closes[-2]
        cc3=s.closes[-3]
        sma0=sum(s.closes[-SMAPERIOD-1:])/SMAPERIOD
        if cc2>sma0 and cc3<=PQexpert.Sma_Value:
            t=s.times[-2]
            h=s.highs[-2]
            si=PQexpert.create_subitem('Text',values=(t,h),text='xUp')
            si.set_anchor(x=0.5,y=1)
            si.setColor(color='g')
            si.set_frozen(True)
        elif cc2<sma0 and cc3>=PQexpert.Sma_Value:
            t=s.times[-2]
            l=s.lows[-2]
            si=PQexpert.create_subitem('Text',values=(t,l),text='xDown')
            si.set_anchor(x=0.5,y=0)
            si.setColor(color='r')
            si.set_frozen(True)
        PQexpert.Sma_Value=sma0
    