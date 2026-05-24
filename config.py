"""
config class for dwcom
"""
import atexit
import os
from threading import Thread
from conf import conf
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import weakref

class Config:
    def __init__(self):
        self.serverConfigs = conf.servers()
        self.watcher = ConfigWatcher('ttcom.conf', weakref.WeakMethod(self.reloadConf))
        self.observer = Observer()
        self.observer.schedule(self.watcher, '.', recursive=False)
        self.observer.start()
        self.observerThread = Thread(target=self.observer.join, daemon=True)
        self.observerThread.start()
        atexit.register(weakref.WeakMethod(self.close))

    def get(self, serverName: str, itemName: str):
        serverConfig = self.serverConfigs.get(serverName)
        if serverConfig is None: return None
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

    def close(self):
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join(timeout=1)

    def __del__(self):
        self.close()

class ConfigWatcher(FileSystemEventHandler):
    def __init__(self, configPath, reloadFunc):
        self.configPath = os.path.abspath(configPath)
        self.reloadFunc = reloadFunc

    def on_modified(self, event):
        if event.is_directory: return
        if os.path.abspath(event.src_path) != self.configPath: return
        func = self.reloadFunc()
        if func is not None:
            func()