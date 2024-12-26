from PySide6 import QtCore
from datetime import datetime

PROGRAM_NAME='pyqtrader'

VERSION='1.4.1'

DYNAMIC_QUERYING=True #continuous updating from the data provider, set False to turn off (no QTimer initiation) 

PERIOD_S5=5
PERIOD_S10=10
PERIOD_S15=15
PERIOD_S30=30
PERIOD_M1=60
PERIOD_M2=120
PERIOD_M4=240
PERIOD_M5=300
PERIOD_M10=600
PERIOD_M15=900
PERIOD_M30=1800
PERIOD_H1=3600
PERIOD_H2=7200
PERIOD_H3=10800
PERIOD_H4=14400
PERIOD_H6=21600
PERIOD_H8=28800
PERIOD_H12=43200
PERIOD_D1=86400
PERIOD_W1= 5*PERIOD_D1
PERIOD_MN1=2629743
PERIOD_Y1=31556926

TIMEFRAMES = {
    'S5':  PERIOD_S5,
    'S10':  PERIOD_S10,
    'S15':  PERIOD_S15,
    'S30':  PERIOD_S30,
    'M1':   PERIOD_M1,
    'M2':   PERIOD_M2,
    'M4':   PERIOD_M4,
    'M5':   PERIOD_M5,
    'M10':  PERIOD_M10,
    'M15':  PERIOD_M15,
    'M30':  PERIOD_M30,
    'H1':   PERIOD_H1,
    'H2':   PERIOD_H2,
    'H3':   PERIOD_H3,
    'H4':   PERIOD_H4,
    'H6':   PERIOD_H6,
    'H8':   PERIOD_H8,
    'H12':   PERIOD_H12,
    'D1':    PERIOD_D1,
    'W1':   PERIOD_W1,
    'MN1':  PERIOD_MN1
}

MIN_REGULAR_TIMESTAMP = (datetime(1, 1, 1) - datetime(1970,1,1)).total_seconds()
MAX_REGULAR_TIMESTAMP = (datetime(9999, 1, 1) - datetime(1970,1,1)).total_seconds()
SEC_PER_YEAR = 365.25*24*3600

D_PROFILE='[default]'
DELETED_PROFILE='[deleted]'
D_PROFILES=[D_PROFILE,DELETED_PROFILE]

WINDOW_STATE_FLNM='window_state.json'
PROFILE_STATE_FLNM='profile_state.json'

D_SUBWINDOWWIDTH=600
D_SUBWINDOWHEIGHT=400
D_DOCKHEIGHT=0.25 #indicator dock height compared to the subwindow

# parameters for setXRange() and setYrange() on initialisation
DX_COUNT = 100 # default x-axis candle count
DX_SHIFT = 20 # default x-axis candle shift
DY_ZOOM = 0.8 # default y-axiz zoom
D_TIMEFRAME = PERIOD_H1 # default timeframe
D_SYMBOL='EURUSD' #default datasource symbol
ADJUSTED_TIMEFRAMES=(PERIOD_D1,PERIOD_W1,PERIOD_MN1) #timeframes adjusted to remove time gaps (weekend etc).

def tf_to_label(tf):
    for key in TIMEFRAMES:
            if TIMEFRAMES[key]==tf:
                return key   
                     
D_TFLABEL=tf_to_label(D_TIMEFRAME)

CHARTTYPES=('Bar','Candle','Line','HeikinAshi')
D_CHARTTYPE='Bar'

#Timeseries names
BARS='i'
TIMES='t'
OPENS='o'
HIGHS='h'
LOWS='l'
CLOSES='c'

TS_NAMES=[TIMES,OPENS,HIGHS,LOWS,CLOSES]

#Directories
MAIN_DIR='./Pyqtrader/'
SYS_DIR=f'{MAIN_DIR}.system/'
APP_DIR=rf'{MAIN_DIR}Apps/'
APP_INDICATORS_DIR=f'{APP_DIR}Indicators/'
APP_EXPERTS_DIR=f'{APP_DIR}Experts/'
APP_SCRIPTS_DIR=f'{APP_DIR}Scripts/'
ASSETS_DIR=f'{SYS_DIR}assets/'
DATA_DIR=f'{SYS_DIR}data/'
DATA_SYMBOLS_DIR=f'{DATA_DIR}symbols/'
DATA_STATES_DIR=f'{DATA_DIR}states/'
FILES_DIR=f'{MAIN_DIR}Files/'
DIRECTORIES=[APP_DIR,APP_EXPERTS_DIR,APP_INDICATORS_DIR,APP_SCRIPTS_DIR,ASSETS_DIR,
    DATA_DIR,DATA_SYMBOLS_DIR,DATA_STATES_DIR,FILES_DIR]
USER_DIRECTORIES=[APP_DIR,ASSETS_DIR,DATA_DIR,FILES_DIR]

#Files
ACCT_FILE='acct.py'
ACCT_DETAILS="API_KEY=''\nACCOUNT_ID=''\nOANDA_URL=''\n"
CORE_ICON=f'{ASSETS_DIR}m-512w_bb.png'

USERFILESLIST=(ACCT_FILE,'__init__.py','MovingAverageCross.py', "DonchianChannel.py", "HullMA.py",
    'ExponentialMovingAverage.py','Fractals.py','MACD.py','RSI.py','SimpleMovingAverage.py',
    'Stochastic.py','horline.py','verline.py','PreviousHighLow.py','Ticker.py','Scroller.py',
    "customiz.py")

HANDLE_SIZE=7
VICINITY_DISTANCE=20 #vicinity distance eg. hover distance in pixels/not used after pg bug fix
RAYDIR={'b':'Both','n':'Neither','r':'Right','l':'Left'}
SOLIDLINE='____'
DASHLINE='_ _ _'
DOTLINE='....'
DASHDOTLINE='_._.'
DASHDOTDOTLINE='_.._'
LINESTYLES={SOLIDLINE:QtCore.Qt.SolidLine,DASHLINE:QtCore.Qt.DashLine,
            DOTLINE:QtCore.Qt.DotLine,
            DASHDOTLINE:QtCore.Qt.DashDotLine, DASHDOTDOTLINE:QtCore.Qt.DashDotDotLine}
D_STYLE=SOLIDLINE
D_LEVELSTYLE=DOTLINE
D_COLOR='#ffffff'
D_TIMER=2000 #the frequency of the queries to data providers in ms
D_BARCOUNT=1000 #number of bars in a server query

LEVELS_WIDTH=0.2

# Regression channel
D_REGRESSION_MULTIPLIER=2.0

REGRESSION_LINE_CLOSES="Closes"
REGRESSION_LINE_HIGHSLOWSAVG="(Highs+Lows)/2"
REGRESSION_LINE_HIGHSLOWSCLOSESAVG="(Highs+Lows+Closes)/3"
D_REGRESSION_LINE=REGRESSION_LINE_CLOSES
REGRESSION_LINE_LIST=(REGRESSION_LINE_CLOSES,REGRESSION_LINE_HIGHSLOWSAVG,
                      REGRESSION_LINE_HIGHSLOWSCLOSESAVG)

LINESTDDEV_REGRESSION_MODE="LineStdDev"
HIGHSLOWSAVG_REGRESSION_MODE="HighsLowsAvg"
HIGHSLOWSSTDDEV_REGRESSION_MODE="HighsLowsStdDev"
D_REGRESSION_MODE=LINESTDDEV_REGRESSION_MODE
REGRESSION_MODE_LIST=(LINESTDDEV_REGRESSION_MODE,
                     HIGHSLOWSAVG_REGRESSION_MODE,
                     HIGHSLOWSSTDDEV_REGRESSION_MODE)

# Studies
D_STUDYCOLOR='#ff0000'
D_STUDYWIDTH=1
D_STUDYMODE='Close'
D_STUDYMODELIST=('Open','High','Low','Close')
D_STUDYMETHOD='Simple'
D_STUDYMETHODLIST=('Simple','Exponential')
D_STUDYPERIOD=20
D_STUDYPERIODMAX=10000
D_STUDYFREEZE=False

D_MAPERIOD=20
D_RSIPERIOD=14
D_RSICOLOR='#0055ff'
STOCH_K=5
STOCH_SLOW=3
STOCH_D=3
STOCHCOLOR_K='#55aa7f'
STOCHCOLOR_D='#ff0000'
STOCHWIDTH_D=0.7
MACD_PERIODFAST=12
MACD_PERIODSLOW=26
MACD_PERIODSIGNAL=9
MACD_WIDTHSIGNAL=1.0
MACD_COLORSIGNAL='#ff0000'
MACD_WIDTHHIST=0.3
BBCOLOR='#55aa7f'
BBMULTI=2
ATRPERIOD=14

FIBOLINECOLOR='#ff0000'
FIBOLINEWIDTH=1
FIBOWIDTH=0.5
FIBOCOLOR='#ffffff'
FIBOSTYLE=DOTLINE

D_ELSIZE=10
D_EIDEGREE='1 2 3 4 5'
ELLIOTT_IMPULSE={
    '(I) (II) (III) (IV) (V)' : ['(I)', '(II)', '(III)', '(IV)', '(V)'], 
    'I) II) III) IV) V)' : ['I)', 'II)', 'III)', 'IV)', 'V)'],
    'I II III IV V' : ['I', 'II', 'III', 'IV', 'V'],
    u'\u2780 \u2781 \u2782 \u2783 \u2784' : [u'\u2780',u'\u2781',u'\u2782',u'\u2783',u'\u2784'],
    '(1) (2) (3) (4) (5)':['(1)','(2)','(3)','(4)','(5)'],'1) 2) 3) 4) 5)':['1)','2)','3)','4)','5)'],
    D_EIDEGREE :['1','2','3','4','5'],'(i) (ii) (iii) (iv) (v)':['(i)','(ii)','(iii)','(iv)','(v)'],
    'i) ii) iii) iv) v)':['i)','ii)','iii)','iv)','v)'], 'i ii iii iv v':['i','ii','iii','iv','v'],
    }

D_ECDEGREE='A B C'
ELLIOTT_CORRECTION={
    u'\u24B6 \u24B7 \u24B8' : ['\u24B6', '\u24B7', '\u24B8'],
    '(A) (B) (C)' : ['(A)','(B)','(C)'], 'A) B) C)' : ['A)','B)','C)'], D_ECDEGREE : ['A','B','C'],
    u'\u24D0 \u24D1 \u24D2' : ['\u24D0', '\u24D1', '\u24D2'],
    '(a) (b) (c)' : ['(a)','(b)','(c)'], 'a) b) c)' : ['a)','b)','c)'], 'a b c' : ['a','b','c'],
    u'\u24CC \u24CD \u24CE' : ['\u24CC', '\u24CD', '\u24CE'],
    '(W) (X) (Y)' : ['(W)','(X)','(Y)'], 'W) X) Y)' : ['W)','X)','Y)'], 'W X Y' : ['W','X','Y'],
    u'\u24E6 \u24E7 \u24E9' : ['\u24E6', '\u24E7', '\u24E8'],
    '(w) (x) (y)' : ['(w)','(x)','(y)'], 'w) x) y)' : ['w)','x)','y)'], 'w x y' : ['w','x','y'],
    'S H S' : ['S','H','S']
    }

D_EECDEGREE='A B C D E'
ELLIOTT_EXTENDED_CORRECTION={
    u'\u24B6 \u24B7 \u24B8 \u24B9 \u24BA' : ['\u24B6', '\u24B7', '\u24B8','\u24B9','\u24BA'],
    '(A) (B) (C) (D) (E)' : ['(A)','(B)','(C)','(D)','(E)'], 
    'A) B) C) D) E)' : ['A)','B)','C)','D)','E)'], 
    D_EECDEGREE : ['A','B','C', 'D','E'],
    u'\u24D0 \u24D1 \u24D2 \u24D3 \u24D4' : ['\u24D0', '\u24D1', '\u24D2', '\u24D3','\u24D4'],
    '(a) (b) (c) (d) (e)' : ['(a)','(b)','(c)','(d)','(e)'], 
    'a) b) c) d) e)' : ['a)','b)','c)','d)','e)'], 'a b c d e' : ['a','b','c','d','e'],
    u'\u24CC \u24CD \u24CE \u24CD \u24CF' : ['\u24CC', '\u24CD', '\u24CE','\u24CD','\u24CF'],
    '(W) (X) (Y) (X) (Z)' : ['(W)','(X)','(Y)','(X)','(Z)'], 
    'W) X) Y) X) Z)' : ['W)','X)','Y)','X','Z'], 'W X Y X Z' : ['W','X','Y','X','Z'],
    u'\u24E6 \u24E7 \u24E8 \u24E7 \u24E9' : ['\u24E6', '\u24E7', '\u24E8','\u24E7','\u24E9'],
    '(w) (x) (y) (x) (z)' : ['(w)','(x)','(y)','(x)','(z)'], 
    'w) x) y) x) z)' : ['w)','x)','y)','x)','z)'], 'w x y x z' : ['w','x','y','x','z'],
    }

D_LABEL='!@tk, !@tf'
CORNER={'tl':'Top-Left','tr':'Top-Right','bl':'Bottom-Left','br':'Bottom-Right'}
D_ANCHOR=[0.5,0.5]

MAGNET_DISTANCE=20

#CHARTPROPS 
background='Background color'
foreground='Foreground color'
graphicscolor='Graphics color'
font='Font'
fontsize='Font size'
barcolor='Bar color'
framecolor='Candle frame color'
bull='Bullish candle color'
bear='Bearish candle color'
linecolor='Line color'
pricelinecolor='Price line color'
CHARTPROPSCOLORLIST=(background,foreground,graphicscolor,barcolor,framecolor,bull,bear,linecolor,pricelinecolor)
D_CHARTPROPS={background:'k',foreground:'d', graphicscolor:'w',font: None, fontsize: None, barcolor:'d',
    framecolor:'w',bull:'#00aa7f',bear:'r',linecolor:'d',pricelinecolor:'d'}
CHARTPROPS={
    'Custom...' : None,
    'Default' : D_CHARTPROPS,
    'Classic' : {background:'k',foreground:'d',graphicscolor: 'w', font: None, fontsize: None,barcolor:'w',
        framecolor:'g',bull:'k',bear:'w',linecolor:'d',pricelinecolor:'d'},
    'WhiteOnBlack' : {background:'k',foreground:'d',graphicscolor: 'w',font: None, fontsize: None, barcolor:'w',
        framecolor:'w',bull:'w',bear:'k',linecolor:'d',pricelinecolor:'d'},
    'BlackOnWhite' : {background:'w',foreground:'d', graphicscolor: 'k',font: None, fontsize: None,barcolor:'k',
        framecolor:'k',bull:'k',bear:'w',linecolor:'k',pricelinecolor:'d'},
    'Traditional' : {background:'w',foreground:'d',graphicscolor: 'k',font: None, fontsize: None,barcolor:'k',
        framecolor : 'k',bull:'g',bear: 'r',linecolor:'k',pricelinecolor:'d'},
    'Grey' : {background:'#dadada',foreground:'#474747',graphicscolor: 'k',font: None, fontsize: None,barcolor:'k',
        framecolor : 'k',bull:'g',bear: 'r',linecolor:'k',pricelinecolor:'#474747'},
}
D_FONTSIZE=8
API_LABEL_FONTSIZE=D_FONTSIZE
CROSSHAIR_WIDTH=0.3
PRICELINE_WIDTH=0.3

THEMES={'System':'System','Light':'Light','Darker':'Darker','Dark':'Dark'}
# dict of class properties, updated from within the classes 
# and used to restore the state on opening
D_METAPROPS=dict(magnet=False,experts_on=False,chartprops=dict(D_CHARTPROPS),
    timer=D_TIMER,count=D_BARCOUNT,tabbed_view=False,status_bar=True,
    theme=THEMES['Darker']) 
        
CONNECTION_MESSAGE='Connected'
NO_CONNECTION_MESSAGE='No Connection'

COPY_DIST=0.05 #Distance of copied object expressed as share of viewBox range

TRADE_RECORD= dict(
    id_number='id_number',
    symbol='symbol',
    trade_type='trade_type',
    volume='volume',
    open_time='open_time',
    open_price='open_price',
    close_time='close_time',
    close_price='close_price'
)

# GUI message timeout in seconds to avoid blocking of GUI by recurring messages,
# eg for messages generated on every server query
GUI_MESSAGE_TIMEOUT=30

D_TIMEZONE= ('EET', 'UTC+2:00 (Eastern European Time, EET)')

LISTED_TIMEZONES = [
    D_TIMEZONE,
    ('Etc/GMT-12', 'UTC-12:00'),
    ('Pacific/Honolulu', 'UTC-10:00'),
    ('America/Anchorage', 'UTC-9:00'),
    ('America/Los_Angeles', 'UTC-8:00'),
    ('America/Denver', 'UTC-7:00'),
    ('America/Chicago', 'UTC-6:00'),
    ('America/New_York', 'UTC-5:00'),
    ('America/Halifax', 'UTC-4:00'),
    ('America/Sao_Paulo', 'UTC-3:00'),
    ('Atlantic/South_Georgia', 'UTC-2:00'),
    ('Atlantic/Azores', 'UTC-1:00'),
    ('UTC', 'UTC+0:00'),
    ('Europe/London', 'UTC+0:00 (London)'),
    ('Europe/Paris', 'UTC+1:00 (Central European Time, CET)'),
    ('Europe/Athens', 'UTC+2:00 (Eastern European Time, EET)'),
    ('Africa/Johannesburg', 'UTC+2:00'),
    ('Europe/Moscow', 'UTC+3:00'),
    ('Asia/Dubai', 'UTC+4:00'),
    ('Asia/Karachi', 'UTC+5:00'),
    ('Asia/Kolkata', 'UTC+5:30'),
    ('Asia/Dhaka', 'UTC+6:00'),
    ('Asia/Bangkok', 'UTC+7:00'),
    ('Asia/Shanghai', 'UTC+8:00'),
    ('Asia/Tokyo', 'UTC+9:00'),
    ('Australia/Sydney', 'UTC+10:00'),
    ('Pacific/Auckland', 'UTC+12:00'),
]


#Currently not in use, styles.py used instead:
# LIGHTMODESTYLE=('''
# QWidget {background-color: white; color: black;} 
# QToolBar{border-top: 1px solid lightgrey; border-bottom: 1px solid lightgrey;}
# QMenuBar::item:selected {background-color: lightgrey;}
# QMenu{border: 1px solid lightgrey;}
# QMenu::item:selected {background-color: lightgrey;}
# ''')