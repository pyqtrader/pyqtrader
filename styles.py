from PySide6.QtGui import QPalette, QColor

def qc(*args):
    if len(args)==1: return QColor(args[0],args[0],args[0])
    else: return QColor(*args)

def set_generic_theme(mwindow,
    window=QColor(240,240,240),
    text='black',
    base=QColor(240,240,240),
    alternate=QColor(215,215,215),
    disabled=QColor(127,127,127),
    button=QColor(215,215,215),
    highlight=QColor(42,130,218),
    highlightedtext='white',
    mdi=None):
    dp=QPalette()
    dp.setColor(QPalette.Window,window)
    dp.setColor(QPalette.WindowText,text)
    dp.setColor(QPalette.Disabled,QPalette.WindowText,disabled)
    dp.setColor(QPalette.Base,base)
    dp.setColor(QPalette.AlternateBase,alternate)
    # dp.setColor(QPalette.ToolTipBase,"white")
    # dp.setColor(QPalette.ToolTipText,"white")
    dp.setColor(QPalette.Text,text)
    dp.setColor(QPalette.Disabled,QPalette.Text,disabled)
    dp.setColor(QPalette.Dark,QColor(35,35,35))
    dp.setColor(QPalette.Shadow,QColor(20,20,20))
    dp.setColor(QPalette.Button,button)
    dp.setColor(QPalette.ButtonText,text)
    dp.setColor(QPalette.Disabled,QPalette.ButtonText,disabled)
    dp.setColor(QPalette.BrightText,"red")
    dp.setColor(QPalette.Link,QColor(42,130,218))
    dp.setColor(QPalette.Highlight,highlight)
    dp.setColor(QPalette.Disabled,QPalette.Highlight,QColor(80,80,80))
    dp.setColor(QPalette.HighlightedText,highlightedtext)
    dp.setColor(QPalette.Disabled,QPalette.HighlightedText,disabled)
    mwindow.app.setPalette(dp)
    mwindow.mdi.setBackground(mdi if mdi is not None else dp.base())

def set_light_theme(mwindow):
    return set_generic_theme(mwindow,
        disabled=QColor("#cccccc"),
        mdi=QColor("#999999"))

def set_dark_theme(mwindow):
    return set_generic_theme(mwindow,
        window=QColor(53,53,53),
        text='white',
        base=QColor(42,42,42),
        alternate=QColor(66,66,66),
        button=QColor(53,53,53),
        highlight=QColor(42,130,218),
        highlightedtext='white')

#maximized buttons widget color
darker_mbw="#aaaaaa"
def set_darker_theme(mwindow):
    return set_generic_theme(mwindow,
        window=qc(130),
        text='black',
        base=qc(120),
        alternate=qc(150),
        disabled=QColor("#aaaaaa"),
        button=QColor(100,100,100),
        highlight=qc(172),
        highlightedtext='white',
        mdi=qc(90))