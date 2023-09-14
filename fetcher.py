import os
import requests
import pandas as pd
import numpy as np
from PySide6 import QtCore
from datetime import datetime as dtm
from importlib.machinery import SourceFileLoader
# import data.acct as acct
import ohist
import cfg

from _debugger import _p,_pc,_printcallers,_exinfo,_ptime,_print

OA_PRICE='M'
OA_SMOOTH=True
OA_TIMEOUT=7 #internet disconnection timeout

oa_dict={
    'S5' : {'tf': 'S5', 'cnt':None},
    'S10' : {'tf': 'S10', 'cnt':None},
    'S15' : {'tf': 'S15', 'cnt':None},
    'S30' : {'tf': 'S30', 'cnt':None},
    'M1': {'tf': 'M1','cnt':int(cfg.PERIOD_W1//cfg.PERIOD_M1)},
    'M2' : {'tf': 'M2', 'cnt':None},
    'M4' : {'tf': 'M4', 'cnt':None},
    'M5': {'tf': 'M5', 'cnt':int(cfg.PERIOD_MN//cfg.PERIOD_M5)},
    'M10' : {'tf': 'M10', 'cnt':None},
    'M15': {'tf': 'M15', 'cnt':int(3*cfg.PERIOD_MN//cfg.PERIOD_M15)},
    'M30': {'tf': 'M30', 'cnt':int(6*cfg.PERIOD_MN//cfg.PERIOD_M30)},
    'H1' : {'tf': 'H1', 'cnt':int(18*cfg.PERIOD_MN//cfg.PERIOD_H1)},
    'H2' : {'tf': 'H2', 'cnt':None},
    'H3' : {'tf': 'H3', 'cnt':None},
    'H4' : {'tf': 'H4', 'cnt':int(4*cfg.PERIOD_Y1//cfg.PERIOD_H4)},
    'H6' : {'tf': 'H6', 'cnt':None},
    'H8' : {'tf': 'H8', 'cnt':None},
    'H12' : {'tf': 'H12', 'cnt':None},
    'D'  : {'tf': 'D1', 'cnt':int(20*cfg.PERIOD_Y1//cfg.PERIOD_D1)},
    'W'  : {'tf': 'W1', 'cnt':int(20*cfg.PERIOD_Y1//cfg.PERIOD_W1)},
    'M'  : {'tf': 'MN', 'cnt':int(20*cfg.PERIOD_Y1//cfg.PERIOD_MN)},
}

def history(tf,symbol):
    a=histparams(tf,symbol)
    if a is not None:
        try:
            filename=ohist.output(*a)
            df=pd.read_csv(filename)
            df.drop_duplicates(subset=None,inplace=False)
            df.to_csv(filename,index=True,header=False)
            return True
        except ValueError as e:
            return e
    else:
        return False

def histparams(tframe,symbol):
    instrument=symbol[:-3]+'_'+symbol[-3:]
    grn=tf_to_grn(tframe)
    count=oa_dict[f'{grn}']['cnt']
    tf=cfg.TIMEFRAMES[oa_dict[f'{grn}']['tf']]
    now=dtm.timestamp(dtm.utcnow())
    if count is not None:
        start=dtm.fromtimestamp(now-count*tf).strftime('%Y-%m-%dT%H:%M:%SZ')
        finish=dtm.fromtimestamp(now-tf).strftime('%Y-%m-%dT%H:%M:%SZ') #to ensure no 'This is in the future' error
        result=start,finish,grn,instrument
    else:
        result=None
    return result

def tf_to_grn(tf):
    for grn in oa_dict:
        if oa_dict[f'{grn}']['tf']==cfg.tf_to_label(tf):
            return grn

class Fetcher(QtCore.QObject):
    sigConnectionStatusChanged=QtCore.Signal(object)
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.connected=False
        self.acct=self._acct()

    @property
    def OANDA_URL(self):
        return self.acct.OANDA_URL

    @property
    def SECURE_HEADER(self):
        return {'Authorization': f'Bearer {self.acct.API_KEY}'}

    def _acct(self):
        try:
            a=SourceFileLoader(cfg.ACCT_FILE,cfg.DATA_DIR+cfg.ACCT_FILE).load_module()
        except Exception:
            from uitools import simple_message_box
            simple_message_box(text='Login data error: re-enter login data')
            with open(cfg.DATA_DIR+cfg.ACCT_FILE,'w') as f:
                f.write(cfg.ACCT_DETAILS)
            a=SourceFileLoader(cfg.ACCT_FILE,cfg.DATA_DIR+cfg.ACCT_FILE).load_module()
        return a
    
    def reload_acct(self):
        self.acct=self._acct()

    def trigger(self):
        self.connected= not self.connected
        self.sigConnectionStatusChanged.emit(self.connected)

    def fetch_data(self,session=None, record=False,symbol=cfg.D_SYMBOL, fromdt=None, todt=None, 
                    count=cfg.D_BARCOUNT,timeframe=cfg.D_TIMEFRAME, indexcut=0):
        
        instrument=symbol[:-3]+'_'+symbol[-3:]
        datalist=None
        granularity=tf_to_grn(timeframe)
        
        saved_df=None
        if record==True:
            datasource=cfg.DATA_SYMBOLS_DIR+symbol+'_'+oa_dict[granularity]['tf']+'.csv'
            if os.path.isfile(datasource) and os.stat(datasource).st_size!=0:
                saved_df=pd.read_csv(datasource)
                indexcut=int(saved_df.iloc[-1][0]+1)
                fromdt=saved_df.iloc[-1][1]+timeframe

        if fromdt is None:
            params = dict(count=count,granularity = granularity,smooth=OA_SMOOTH, price=OA_PRICE)
        else:
            todt=dtm.timestamp(dtm.now()) if todt is None else todt
            if(todt-fromdt<0): #interrupt function
                #print('Start time greater than end time')
                return None
            params={'from': fromdt, 'to': todt , 'granularity': granularity,
                    'smooth': OA_SMOOTH, 'price':OA_PRICE}

        if session is None:
            session=requests.Session()
        url=f"{self.OANDA_URL}/instruments/{instrument}/candles"
        
        def get_resp(prms):
            try: a=session.get(url,params=prms,headers=self.SECURE_HEADER,timeout=OA_TIMEOUT)
            except Exception: a=None
            return a

        response=get_resp(params)
        if response is None:
            if self.connected:
                self.trigger()
            return None
        elif (response.status_code==200): #workaround 'Time is in the future' error
            data=response.json()
            if not self.connected:
                self.trigger()
        else:
            try:
                params_lc=dict(count=1,granularity=granularity,price=OA_PRICE, smooth=OA_SMOOTH)
                data=get_resp(params_lc).json()
                tc=data['candles'][-1]['time']
                if tc==fromdt:
                    params=params_lc
                else:
                    params['to']=data['candles'][-1]['time']
                response=get_resp(params)
                data=response.json()
                if not self.connected:
                    self.trigger()
            except Exception:
                if self.connected:
                    self.trigger()

        try:
            lc_complete=data['candles'][-1]['complete']
        except Exception:
            lc_complete=True

        try:
            ohlc=['o','h','l','c']
            our_data=[]

            for candle in data['candles']:
                new_dict={}
                new_dict['time']=candle['time']
                for oh in ohlc:
                    new_dict[oh]=candle['mid'][oh]
                our_data.append(new_dict)

            def dfreader(dt):
                df=pd.DataFrame.from_dict(dt)
                df['time'] = pd.to_datetime(df['time']) #.apply(lambda x: x.value)//10**9 - alternative method, 
                # it is believed to be slower but is one liner and does not require numpy
                df['time']=df.time.values.astype(np.int64) // 10 ** 9
                df.index=df.index+indexcut
                return df

            candles_df=dfreader(our_data)
            # candles_df.index=candles_df.index+indexcut
        
            if saved_df is not None: #double check to ensure non-duplication of candles
                c=candles_df.iloc[0][0] #time stamp
                s=saved_df.iloc[-1][1] #time stamp
                if c==s:
                    our_data.pop(0) #remove duplicating entry
                    candles_df=dfreader(our_data)
            
            if record==True:
                if lc_complete==False:
                    our_data.pop()        
                cdf=dfreader(our_data)
                cdf.to_csv(datasource, mode='a',header=False)
            
            datalist=candles_df.reset_index().values.tolist()
            for i,row in enumerate(datalist):
                for j,val in enumerate(row):
                    x=float(val) if isinstance(val,str) else val
                    datalist[i][j]=x
        except Exception:
            pass

        return {'data': datalist,'complete':lc_complete}

    def fetch_lc(self,session=None,symbol=cfg.D_SYMBOL,timeframe=cfg.D_TIMEFRAME): #fetch last candle       
        a=self.fetch_data(session=session,record=False,symbol=symbol, 
            fromdt=None, todt=None, count=1,timeframe=timeframe, indexcut=0)
        return a

