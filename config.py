"""
config class for dwcom
"""

from threading import Thread
from conf import conf
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Config:
    def __init__(self):
        self.serverConfigs = conf.servers()
        self.watcher = ConfigWatcher('ttcom.conf', self.reloadConf)
        self.observer = Observer()
        self.observer.schedule(self.watcher, '.', recursive = False)
        self.observer.start()
        self.observerThread = Thread(target = self.observer.join, daemon = True)
        self.observerThread.start()

    def get(self, serverName: str, itemName: str):
        try:
            serverConfig = self.serverConfigs[serverName]
        except ValueError as e:
            print(e)
            return None
        try:
            return self._convertConfigValue(serverConfig[itemName])
        except KeyError:
            return None

    @staticmethod
    def _convertConfigValue(configValue: str):
        if configValue.isnumeric() and configValue != '1' and configValue != '0': return float(configValue)
        match configValue.lower():
            case 'y' | 'yes' | '1' | 'true': return True
            case 'n' | 'no' | '0' | 'false': return False
            case _: return configValue

    def reloadConf(self):
        self.serverConfigs = conf.servers()

class ConfigWatcher(FileSystemEventHandler):
    def __init__(self, configPath, reloadFunc):
        self.configPath = configPath
        self.reloadFunc = reloadFunc

    def on_modified(self, event):
        self.reloadFunc()