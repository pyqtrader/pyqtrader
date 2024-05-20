import os
import requests
import pandas as pd
import numpy as np
from PySide6 import QtCore
from datetime import datetime as dtm
from importlib.machinery import SourceFileLoader

import cfg
import charttools as chtl, charttools

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

def tf_to_grn(tf):
    for grn in oa_dict:
        if oa_dict[f'{grn}']['tf']==cfg.tf_to_label(tf):
            return grn

class Fetcher(QtCore.QObject):
    sigConnectionStatusChanged=QtCore.Signal(object)
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.connected=False
        self.offline_mode=False
        self.acct=self._acct()

    @property
    def OANDA_URL(self):
        return self.acct.OANDA_URL

    @property
    def SECURE_HEADER(self):
        return {'Authorization': f'Bearer {self.acct.API_KEY}'}

    def _acct(self):
        
        def create_acct_file():
            with open(cfg.DATA_DIR+cfg.ACCT_FILE,'w') as f:
                    f.write(cfg.ACCT_DETAILS)
        
        if not os.path.isfile(cfg.DATA_DIR+cfg.ACCT_FILE):
            create_acct_file()    
        try:
            a=SourceFileLoader(cfg.ACCT_FILE,cfg.DATA_DIR+cfg.ACCT_FILE).load_module()
        except Exception:
            from uitools import simple_message_box
            simple_message_box(text='Login data error: (re)enter login data if using API')
            create_acct_file()
            a=SourceFileLoader(cfg.ACCT_FILE,cfg.DATA_DIR+cfg.ACCT_FILE).load_module()
        return a
    
    def reload_acct(self):
        self.acct=self._acct()

    def trigger(self):
        self.connected= not self.connected
        self.sigConnectionStatusChanged.emit(self.connected)
    
    def fetch_data(self,session=None,symbol=cfg.D_SYMBOL, fromdt=None, todt=None, 
            count=cfg.D_BARCOUNT,timeframe=cfg.D_TIMEFRAME):
        
        #--------- breakpoint for the offline mode or short symbol names:
        if self.offline_mode or len(symbol)<6:
            return None
        ############
        
        instrument=symbol[:-3]+'_'+symbol[-3:]
        granularity=tf_to_grn(timeframe)    
    
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

        ohlc=['o','h','l','c']
        our_data=[]

        # Return None if server request failed or dataframe cannot be formed
        try:
            for candle in data['candles']:
                new_dict={}
                new_dict['time']=candle['time']
                for oh in ohlc:
                    new_dict[oh]=candle['mid'][oh]
                our_data.append(new_dict)

            df=pd.DataFrame.from_dict(our_data)
            df['time'] = pd.to_datetime(df['time']) #.apply(lambda x: x.value)//10**9 - alternative method, 
            # it is believed to be slower but is one liner and does not require numpy
            df['time']=df.time.values.astype(np.int64) // 10 ** 9
            df[ohlc]=df[ohlc].astype(np.float64)
            df.columns=cfg.TS_NAMES
        except Exception as e:
            print(repr(e))
            return None

        return {'data': df,'complete':lc_complete}

    def fetch_lc(self,session=None,symbol=cfg.D_SYMBOL,timeframe=cfg.D_TIMEFRAME): #fetch last candle       
        if self.offline_mode:
            return None
        else:
            a=self.fetch_data(session=session,symbol=symbol, count=1,timeframe=timeframe)
            return a
    
    def history(self,tf,symbol,session,bars):
        
        grn=tf_to_grn(tf)
        count=oa_dict[f'{grn}']['cnt'] if bars==0 else bars
        df=pd.DataFrame()
        tdiff=(7*tf)/5 if tf==cfg.PERIOD_W1 else tf
       
        while count>0:
            batch=min(count,5000)
            fromdt=df.iloc[0,0]-tdiff*batch if not df.empty else None
            data=self.fetch_data(session,symbol,fromdt,count=batch,timeframe=tf)
            interim_df=data['data']
            if not data['complete']:
                interim_df=interim_df.iloc[:-1]

            df=pd.concat([interim_df,df])
            count-=5000

        df.drop_duplicates(subset=df.columns[0],inplace=True)
        df.reset_index(drop=True,inplace=True)
        filename=chtl.symbol_to_filename(symbol,cfg.tf_to_label(tf),True)
        df.to_csv(filename,index=False,header=False)

        return