import PySide6
from pyqtgraph import Point
from pyqtgraph import functions as fn
from pyqtgraph import ViewBox
import inspect
import ast

def replacer(slf,lf):
        n = ast.parse(inspect.getsource(lf))
        del lf
        exec(compile(n, '<string>', 'exec'))
        return eval(slf)

def wheelEvent(self, ev, axis=None): #edited to supress y-axis scaling
        # if axis in (0, 1):
        #     mask = [False, False]
        #     mask[axis] = self.state['mouseEnabled'][axis]
        # else:
        #     mask = self.state['mouseEnabled'][:]
        mask=[True,False] #added
        s = 1.02 ** (ev.delta() * self.state['wheelScaleFactor']) # actual scaling factor
        s = [(None if m is False else s) for m in mask]
        center = Point(fn.invertQTransform(self.childGroup.transform()).map(ev.pos()))

        self._resetTarget()
        self.scaleBy(s, center)
        ev.accept()
        self.sigRangeChangedManually.emit(mask)

def patcher():
    ViewBox.wheelEvent=replacer('wheelEvent' , wheelEvent)

if __name__=='__main__':
    patcher()