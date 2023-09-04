PQitemtype='Script'

PQshortcut='Ctrl+Up'
PQshortcut='Ctrl+Down'

symbollist=['AUDCAD',
 'AUDCHF',
 'AUDJPY',
 'AUDNZD',
 'AUDUSD',
 'CADCHF',
 'CADJPY',
 'CHFJPY',
 'EURAUD',
 'EURCAD',
 'EURCHF',
 'EURGBP',
 'EURJPY',
 'EURNZD',
 'EURUSD',
 'GBPAUD',
 'GBPCAD',
 'GBPCHF',
 'GBPJPY',
 'GBPNZD',
 'GBPUSD',
 'NZDCAD',
 'NZDCHF',
 'NZDJPY',
 'NZDUSD',
 'USDCAD',
 'USDCHF',
 'USDJPY',
 'XAUUSD',
 'WTICOUSD',
 'SPX500USD',
 'BTCUSD',
 'USDMXN',
 'USDSEK',
 'USDNOK',
 'USDZAR']

def PQinitf(PQscript):
    for i,value in enumerate(symbollist):
        if value==PQscript.symbol:
            if PQscript.shortcut=='Ctrl+Up':
                PQscript.set_chart(symbol=symbollist[i-1])
                break
            if PQscript.shortcut=='Ctrl+Down':
                if i<len(symbollist)-1:
                    PQscript.set_chart(symbol=symbollist[i+1])
                else:
                    PQscript.set_chart(symbol=symbollist[0])
                break