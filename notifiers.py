"""
Contains functions for sending notifications via ntfy, prowl, and desktop notifications.
"""

import subprocess
import sys
from notifypy import Notify
import pyprowl
import ntfpy

appName = 'TeamTalk Commander'

# Patch notify_py PowerShell call to hide the window
if sys.platform == "win32":
    try:
        from notifypy.os_notification import windows
        _orig_run = windows.subprocess.run

        def _runNoWindow(*popenargs, **kwargs):
            if isinstance(popenargs[0], (list, tuple)) and popenargs[0] and "powershell" in popenargs[0][0].lower():
                kwargs["creationflags"] = kwargs.get("creationflags", 0) | subprocess.CREATE_NO_WINDOW
            return _orig_run(*popenargs, **kwargs)

        windows.subprocess.run = _runNoWindow
    except ImportError:
        pass

_systemNotifier = Notify(default_notification_application_name=appName)

def sendSystemNotification(title: str, message: str):
    _systemNotifier.title = title
    _systemNotifier.message = message
    _systemNotifier.send(block=False)

def sendProwlNotification(prowlKey: str, title: str, message: str):
    prowlObj = pyprowl.Prowl(prowlKey, appName=appName)
    prowlObj.notify(title, message)

class ntfyNotifier:
    def __init__(self, serverURL: str, topic: str, user=None, password=None):
        self.serverURL   = serverURL
        self.ntfyServer = ntfpy.NTFYServer(serverURL)
        self.topic = topic
        self.user = user
        if self.user is not None:
            ntfyUser = ntfpy.NTFYUser(self.user, password)
            self.NTFYClient = ntfpy.NTFYClient(self.ntfyServer, self.topic, user=ntfyUser)
        else:
            self.NTFYClient = ntfpy.NTFYClient(self.ntfyServer, self.topic)

    def sendNotification(self, title, message):
        self.NTFYClient.send(message=message, title=title).text
