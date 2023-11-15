from PySide6 import QtCore

COMPANY_NAME='pyqtrader'
PROGRAM_NAME='pyqtrader'

VERSION='1.0'

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
PERIOD_MN=2629743
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
    'MN':  PERIOD_MN
}

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
ADJUSTED_TIMEFRAMES=(PERIOD_D1,PERIOD_W1,PERIOD_MN) #timeframes adjusted to remove time gaps (weekend etc).

def tf_to_label(tf):
    for key in TIMEFRAMES:
            if TIMEFRAMES[key]==tf:
                return key            
D_TFLABEL=tf_to_label(D_TIMEFRAME)

CHARTTYPES=('Bar','Candle','Line')
D_CHARTTYPE='Candle'

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
DIRECTORIES=[APP_DIR,APP_EXPERTS_DIR,APP_INDICATORS_DIR,APP_SCRIPTS_DIR,DATA_DIR,
    DATA_SYMBOLS_DIR,DATA_STATES_DIR,FILES_DIR]
USER_DIRECTORIES=[APP_DIR,ASSETS_DIR,DATA_DIR,FILES_DIR]

#Files
ACCT_FILE='acct.py'
ACCT_DETAILS="API_KEY=''\nACCOUNT_ID=''\nOANDA_URL=''\n"
CORE_ICON=f'{ASSETS_DIR}m-512w_bb.png'

USERFILESLIST=(ACCT_FILE,'__init__.py','lib.py','MovingAverageCross.py',
    'ExponentialMovingAverage.py','Fractals.py','MACD.py','RSI.py','SimpleMovingAverage.py',
    'Stochastic.py','PreviousHighLow.py','Ticker.py','Scroller.py')

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
            DASHDOTDOTLINE:QtCore.Qt.DashDotLine, '_.._':QtCore.Qt.DashDotDotLine}
D_STYLE=SOLIDLINE
D_LEVELSTYLE=DOTLINE
D_COLOR='#ffffff'
D_TIMER=2000 #the frequency of the queries to data providers in ms
D_BARCOUNT=1000 #number of bars in a server query

LEVELS_WIDTH=0.2

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
D_EISTYLE='1 2 3 4 5'
ELLIOTT_IMPULSE={
    '(I) (II) (III) (IV) (V)' : ['(I)', '(II)', '(III)', '(IV)', '(V)'], 
    'I) II) III) IV) V)' : ['I)', 'II)', 'III)', 'IV)', 'V)'],
    'I II III IV V' : ['I', 'II', 'III', 'IV', 'V'],
    u'\u2780 \u2781 \u2782 \u2783 \u2784' : [u'\u2780',u'\u2781',u'\u2782',u'\u2783',u'\u2784'],
    '(1) (2) (3) (4) (5)':['(1)','(2)','(3)','(4)','(5)'],'1) 2) 3) 4) 5)':['1)','2)','3)','4)','5)'],
    D_EISTYLE :['1','2','3','4','5'],'(i) (ii) (iii) (iv) (v)':['(i)','(ii)','(iii)','(iv)','(v)'],
    'i) ii) iii) iv) v)':['i)','ii)','iii)','iv)','v)'], 'i ii iii iv v':['i','ii','iii','iv','v'],
    }

D_ECSTYLE='A B C'
ELLIOTT_CORRECTION={
    u'\u24B6 \u24B7 \u24B8' : ['\u24B6', '\u24B7', '\u24B8'],
    '(A) (B) (C)' : ['(A)','(B)','(C)'], 'A) B) C)' : ['A)','B)','C)'], D_ECSTYLE : ['A','B','C'],
    u'\u24D0 \u24D1 \u24D2' : ['\u24D0', '\u24D1', '\u24D2'],
    '(a) (b) (c)' : ['(a)','(b)','(c)'], 'a) b) c)' : ['a)','b)','c)'], 'a b c' : ['a','b','c'],
    u'\u24CC \u24CD \u24CE' : ['\u24CC', '\u24CD', '\u24CE'],
    '(W) (X) (Y)' : ['(W)','(X)','(Y)'], 'W) X) Y)' : ['W)','X)','Y)'], 'W X Y' : ['W','X','Y'],
    u'\u24E6 \u24E7 \u24E9' : ['\u24E6', '\u24E7', '\u24E8'],
    '(w) (x) (y)' : ['(w)','(x)','(y)'], 'w) x) y)' : ['w)','x)','y)'], 'w x y' : ['w','x','y'],
    'S H S' : ['S','H','S']
    }

D_EECSTYLE='A B C D E'
ELLIOTT_EXTENDED_CORRECTION={
    u'\u24B6 \u24B7 \u24B8 \u24B9 \u24BA' : ['\u24B6', '\u24B7', '\u24B8','\u24B9','\u24BA'],
    '(A) (B) (C) (D) (E)' : ['(A)','(B)','(C)','(D)','(E)'], 
    'A) B) C) D) E)' : ['A)','B)','C)','D)','E)'], 
    D_EECSTYLE : ['A','B','C', 'D','E'],
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
D_CHARTPROPS={background:'k',foreground:'d', graphicscolor:'w',font: None, fontsize: None, barcolor:'w',
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

#Currently not in use, styles.py used instead:
# LIGHTMODESTYLE=('''
# QWidget {background-color: white; color: black;} 
# QToolBar{border-top: 1px solid lightgrey; border-bottom: 1px solid lightgrey;}
# QMenuBar::item:selected {background-color: lightgrey;}
# QMenu{border: 1px solid lightgrey;}
# QMenu::item:selected {background-color: lightgrey;}
# ''')