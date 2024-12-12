# Add to path to use as a module globally
import os, sys

this_dir=os.path.dirname(__file__)
if this_dir not in sys.path:
    sys.path.append(this_dir)