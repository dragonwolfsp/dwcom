import sys
# we do this weerd workaround so that plugin code gets reloaded  when the refresh command is run, this should already happen but it seems broken at this time.
if __name__ in sys.modules:
    del(sys.modules[__name__])
# close old config if it exists
from dwcom import config
if config is not None:
    config.close()
    del(config)
from dwcom import Trigger
