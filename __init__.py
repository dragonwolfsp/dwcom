import sys
# we do this weerd workaround so that plugin code gets reloaded  when the refresh command is run, this should already happen but it seems broken at this time.
if __name__ in sys.modules:
    del(sys.modules[__name__])
from dwcom import Trigger