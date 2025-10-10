"""
The trigger class for dwcom
"""


import os
from soundfile import available_formats
from trigger_cc import TriggerBase
from notifiers import sendSystemNotification, sendProwlNotification, ntfyNotifier
from speech import Speech
from logger import getServerLogger
from fileRandomizer import getRandomLine
from audio.manager import Manager as AudioManager
from config import Config

audioManager = AudioManager('sounds')
config = Config()

serverCaches = {}

def getServerSpeaker(serverName: str):
    if serverName in serverCaches:
        if 'speaker' in serverCaches[serverName]: return serverCaches[serverName]['speaker']
    outputModule = config.get(serverName, 'speechdmodule')
    rate= config.get(serverName, 'speechrate')
    volume = config.get(serverName, 'speechvolume')
    voice = config.get(serverName, 'speechvoice')
    pitch = config.get(serverName, 'speechpitch')
    speakerType = config.get(serverName, 'speechengine')
    kwargs = {}
    if outputModule is not None: kwargs['outputModule'] = outputModule
    if rate is not None: kwargs['rate'] = rate
    if voice is not None: kwargs['voice'] = voice
    if volume is not None: kwargs['volume'] = volume
    if pitch is not None: kwargs['pitch'] = pitch
    speaker = Speech(speakerType if speakerType is not None else 'auto', **kwargs)
    if serverName not in serverCaches: serverCaches[serverName] = {'speaker': speaker}
    else: serverCaches[serverName]['speaker'] = speaker
    return speaker

def getUserInfo(server, userid):
    """Gets user information from cache, otherwise attempts to get it from the server.

    Args:
        server (any): The  server that the user is beeing retreeved from, tipicly server.shortname.
        userid (any): The user id of the user beeing retreeved.
    """
    if server.shortname in serverCaches:
        if 'users' in serverCaches[server.shortname]:
            if userid in serverCaches[server.shortname]['users']: return serverCaches[server.shortname]['users'][userid]
    if userid not in server.users: return {}
    userName = server.users[userid].get('username') or ""
    nickname = server.users[userid].get('nickname') or ""
    admin = True if server.users[userid].usertype == '2' else False
    userInfo = {'userName': userName, 'nickname': nickname, 'admin': admin}
    if not server.shortname in serverCaches:
        serverCaches[server.shortname] = {'users': {userid: userInfo}}
    else:
        if  not 'users' in serverCaches[server.shortname]: serverCaches[server.shortname]['users'] = {userid: userInfo}
        else: serverCaches[server.shortname]['users'][userid] = userInfo
    return serverCaches[server.shortname]['users'][userid]

def prittifyName(userid, userinfo):
    name = ''
    if 'nickname' in userinfo: name = f'"{userinfo['nickname']}"'
    if 'userName' in userinfo:
        if name and name != userinfo['userName']: name += f' ({userinfo['userName']})'
        else: name = f'"{userinfo['userName']}"'
    if not name: name = f'User {userid}'
    return name

def prittifyEvent(server, event):
    output = f'{server.shortname} -'
    userid = None
    destuserid = None
    if     'userid' in event.parms:
        userid = event.parms.userid
    elif 'srcuserid' in event.parms:
        userid = event.parms.srcuserid
    elif 'kickerid' in event.parms:
        userid = event.parms.kickerid
    if 'destuserid' in event.parms:
        destuserid = event.parms.destuserid
        destUserinfo = getUserInfo(server, destuserid)
        destPrittyName = prittifyName(destuserid, destUserinfo)
    if userid is not None and userid != '0':
        userinfo = getUserInfo(server, userid)
        prittyName = prittifyName(userid, userinfo)
        userTypeString = 'admin' if userinfo['admin'] == True else 'user'
    match event.event:
        case 'loggedin':
            loginMessage = 'logged in'
            if os.path.exists('text/logins.txt'):  loginMessage = getRandomLine('text/logins.txt')
            output += f' {userTypeString} {prittyName} {loginMessage}'
        case 'loggedout':
            logOutMessage = 'logged out'
            if os.path.exists('text/logouts.txt'):  logOutMessage = getRandomLine('text/logouts.txt')
            output += f' {userTypeString} {prittyName} {logOutMessage}'
        case 'adduser':
            channelName= server.channelname(event.parms.chanid)
            channelName = channelName if 'the root channel' not in channelName.lower() else 'root'
            output += f' {userTypeString} {prittyName} joined channel {channelName}'
        case 'removeuser':
            channelName= server.channelname(event.parms.chanid)
            channelName = channelName if 'the root channel' not in channelName.lower() else 'root'
            output += f' {userTypeString} {prittyName} left channel {channelName}'
        case 'updateuser':
            statusMSG = event.parms.statusmsg if 'statusmsg' in event.parms else ''
            nickname = event.parms.nickname
            statusMode = event.parms.statusmode
            if statusMode in ('0', '4096', '256'):
                statusMode = 'available'
            elif statusMode in ('1', '4097', '257'):
                statusMode = 'away'
            elif statusMode in ('2', '4098', '258'):
                statusMode = 'questioning'
            elif statusMode in ('6144', '2048', '2304'):
                statusMode = 'streaming media'
            else:
                statusMode = f'unknown status{statusMode}'
            output += f'{prittyName} -'
            if userinfo.get('statusmode', 0) != event.parms.statusmode:
                output += f' Status set to {statusMode}.'
            if userinfo.get('statusmsg', '') != statusMSG:
                output += f' Status message set to {event.parms.statusmsg}.'
            if userinfo['nickname'] != nickname:
                output += f' Nickname set to {nickname}.'
        case 'addfile':         
            fileName = event.parms.filename if 'filename' in event.parms else 'unknown file'
            owner = event.parms.owner
            output += f'file {fileName} uploaded to {server.channelname(event.parms.chanid)} by {owner}'
        case 'removefile':
            fileName = event.parms.filename if 'filename' in event.parms else 'unknown file'
            output += f'file {fileName} deleted from {server.channelname(event.parms.chanid)}'
        case 'fileaccepted':
            output += f'File transfer for {event.parms.filename} initiated'
        case 'filecompleted':
            output += f'File transfer for {event.parms.filename} complete'
        case 'addchannel':
            channelname = server.channelname(event.parms.chanid)
            output += f'channel {channelname} created'
        case 'removechannel':
            channelName = serverCaches[server.shortname]['channels'][event.parms.chanid] if event.parms.chanid in serverCaches[server.shortname]['channels'] else f'with id {event.parms.chanid}'
            output += f'channel {channelName} deleted'
        case 'updatechannel':
            channelname = server.channelname(event.parms.chanid)
            output += f'channel {channelname} updated'
        case 'kicked':
            if userid == '0':
                if 'chanid' not in event.parms: output += f'Kicked from server: multiple logins disallowed'
                else: output += f'Kicked from channel with id {event.parms.chanid}: channel deleted'
                return output
            if 'chanid' in event.parms: output += f'Kicked from channel {server.channelname(event.parms.chanid)} by {prittyName}'
            else: output += f'kicked from server by {prittyName}'
        case 'messagedeliver':
            if event.parms.type == '1':
                output += f'Private message from {prittyName}'
                if destuserid is not None and destuserid != server.me.userid: output += f' to {destPrittyName}'
                output += f': {event.parms.content}'
            elif event.parms.type == '2':
                channelName = server.channelname(event.parms.chanid)
                output += f'channel Message from {prittyName}'
                if server.me.chanid != event.parms.chanid: output += f' to {channelName}'
                output += f': {event.parms.content}'
            if event.parms.type == '3':
                output += f'Broadcast message from {prittyName}: {event.parms.content}'
            elif event.parms.type =='4':
                output += F'Custom message from {prittyName}: {event.parms.content}'
        case 'serverupdate':
            output += 'server updated'
        case _: return output + event.event
    return output

class Trigger(TriggerBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Do not process events from a server that is not logged in
        if not self.server.loggedIn: return
        # do not process events if they are from hour user.
        if 'userid' in self.event.parms and self.server.me.userid == self.event.parms.userid: return
        # ensure caches will be initialized after login.
        if self.event.event == 'ok':
            self.initializeCache()
        # do not process events that are caused by commands. This ensures that events like kicked and banned actualy work properly.
        if self.event.event in ('ok', 'left', 'joined', 'error'): return
        # Do not process spammy typing notifications.
        if self.event.event =='messagedeliver':
            if self.event.parms.type == '4' and self.event.parms.content.startswith('typing'): return
        self.prittyEvent = prittifyEvent(self.server, self.event)
        self.playSound()    
        self.speak(self.prittyEvent)
        if self.event.event in ('loggedin', 'loggedout', 'messagedeliver'): self.notify()
        self.logEvent()
        self.handleCache()

    def speak(self, message):
        doSpeak = config.get(self.server.shortname, 'speech')
        if doSpeak != True and doSpeak is not None: return
        noSpeak = config.get(self.server.shortname, 'nospeak')
        interrupt = config.get(self.server.shortname, 'speechinterrupt')
        if interrupt is None: interrupt = True
        if noSpeak:
            if self.event.event in noSpeak.split('+'): return
        speaker = getServerSpeaker(self.server.shortname)
        speaker.both(message, interrupt = interrupt)

    def notify(self):
        if self.event.event in ('loggedin', 'loggedout') and config.get(self.server.shortname, 'notifyloginout') == False: return
        elif self.event.event == 'messagedeliver' and config.get(self.server.shortname, 'notifymessage') == False: return
        title = self.makeTitle()
        if config.get(self.server.shortname, 'systemnotify') == True: sendSystemNotification(title, self.prittyEvent)
        if config.get(self.server.shortname, 'ntfy') == True: self.ntfyNotify(title, self.prittyEvent)
        if config.get(self.server.shortname, 'prowl') == True: self.prowlNotify(title, self.prittyEvent)

    def makeTitle(self):
        titles = {
            'loggedin': 'User logged in.',
            'loggedout': 'User logged out.',
            'kicked': 'Kicked from server' if 'chanid' not in self.event.parms else 'kicked from channel'
        }
        if self.event.event == 'messagedeliver':
            match self.event.parms.type:
                case '1': return 'Private message received'
                case '2': return 'Channel message received'
                case '3': return 'Broadcast message received'
                case '4': return 'custom message received'
        else: return titles[self.event.event] if self.event.event in titles else 'unknown event'

    def ntfyNotify(self, title: str, message: str):
        serverUrl = config.get(self.server.shortname, 'ntfyurl')
        if not serverUrl: serverUrl = 'https://ntfy.sh'
        topic = config.get(self.server.shortname, 'ntfytopic')
        if not topic: raise NameError(f'ntfytopic not found in server config for {self.server.shortname}')
        user = config.get(self.server.shortname, 'ntfyuser')
        password = config.get(self.server.shortname, 'ntfypassword')
        notifyer = ntfyNotifier(serverUrl, topic, user, password)
        notifyer.sendNotification(title, message)

    def prowlNotify(self, title: str, message: str):
        prowlKey = config.get(self.server.shortname, 'prowlkey')
        if not prowlKey: raise NameError(f'prowlkey not found in config for {self.server.shortname}')
        sendProwlNotification(prowlKey, title, message)

    def logEvent(self):
        log = config.get(self.server.shortname, 'log')
        if log != True and log is not None: return
        maxSize = config.get(self.server.shortname, 'maxlogsize') 
        maxSize = maxSize * 1024 * 1024 if maxSize is not None else 4 * 1024 * 1024
        maxFiles = config.get(self.server.shortname, 'maxlogfiles')
        if maxFiles is None: maxFiles = 5
        logger = getServerLogger(self.server.shortname, 'logs', maxSize, maxFiles)
        logger.info(self.prittyEvent)

    def playSound(self):
        playSounds = config.get(self.server.shortname, 'sounds')
        if playSounds != True and  playSounds is not  None: return
        noSound = config.get(self.server.shortname, 'nosound')
        if noSound is not None:
            if self.event.event in noSound.split('+'): return
        soundPack = config.get(self.server.shortname, 'soundpack')
        if soundPack is None: soundPack = 'default'
        sounds = {
            'loggedin': 'in',
            'loggedout': 'out',
            'adduser': 'join',
            'removeuser': 'leave',
            'updateuser': 'status',
            'addchannel': 'channelcreate',
            'removechannel': 'channelremove',
            'updatechannel': 'channelupdate',
            'addfile': 'fileadd',
            'removefile': 'fileremove',
            'fileaccepted': 'filetransfer',
            'filecompleted': 'filetransfercomplete',
            'serverupdate': 'serverupdate                                       ',
            'kicked': 'kicked'
        }
        if self.event.event == 'messagedeliver':
            if self.event.parms.type == '1': sound = 'user'
            elif self.event.parms.type == '2': sound = 'channel'
            elif self.event.parms.type == '3': sound = 'broadcast'
            if self.event.parms.type == '4': sound = 'message'
        else:
            if self.event.event in sounds: sound = sounds[self.event.event]
            else: return
        for filetype in available_formats():
            fullSoundPath = f'{soundPack}/{sound}.{filetype.lower()}'
            if os.path.exists('sounds/'+fullSoundPath): break
            fullSoundPath = None
        if fullSoundPath is None: return
        playerType = config.get(self.server.shortname, 'playbacktype')
        if playerType is None: playerType = 'interrupting'
        volume = config.get(self.server.shortname, 'soundvolume')
        if volume is  None: volume = 100
        match playerType.lower():
            case 'onebyone':
                audioManager.play(fullSoundPath, 2, gain = volume)
            case 'interrupting':
                audioManager.play(fullSoundPath, 1, gain = volume)
            case 'overlapping':
                audioManager.play(fullSoundPath, 0, gain = volume)
            case _:
                raise ValueError(f'Failed to play sound:\n unsupported playback type {playerType}')

    def handleCache(self):
        if self.event.event == 'loggedout': 
            if not self.server.shortname in serverCaches: return
            if not 'users' in serverCaches[self.server.shortname]: return
            if not self.event.parms.userid in serverCaches[self.server.shortname]['users']: return
            serverCaches[self.server.shortname]['users'].pop(self.event.parms.userid)
        if self.event.event == 'loggedin':
            userName = self.server.users[self.event.parms.userid].get('username') or ""
            nickname = self.server.users[self.event.parms.userid].get('nickname') or f'user{self.event.parms.userid}'
            admin = True if self.server.users[self.event.parms.userid].usertype == '2' else False
            userInfo = {'userName': userName, 'nickname': nickname, 'admin': admin}
            if not self.server.shortname in serverCaches:         serverCaches[self.server.shortname] = {'users': {self.event.parms.userid: userInfo}}
            elif  not 'users' in serverCaches[self.server.shortname]: serverCaches[self.server.shortname]['users'] = {self.event.parms.userid: userInfo}
            else: serverCaches[self.server.shortname]['users'][self.event.parms.userid] = userInfo
        if self.event.event == 'updateuser':
            serverCaches[self.server.shortname]['users'][self.event.parms.userid]['nickname'] = self.event.parms.nickname
            serverCaches[self.server.shortname]['users'][self.event.parms.userid]['statusmode'] = self.event.parms.statusmode
            serverCaches[self.server.shortname]['users'][self.event.parms.userid]['statusmsg'] = self.event.parms.statusmsg
        if self.event.event == 'addchannel':
            channelName = self.server.channelname(self.event.parms.chanid)
            if not self.server.shortname in serverCaches:         serverCaches[self.server.shortname] = {'channels':{self.event.parms.chanid: channelName}}
            elif  not 'channels' in serverCaches[self.server.shortname]: serverCaches[self.server.shortname]['channels'] = {self.event.parms.chanid: channelName}
            else: serverCaches[self.server.shortname]['channels'] += {self.event.parms.chanid: channelName}
        if self.event.event == 'updatechannel':
            channelName = self.server.channelname(self.event.parms.chanid)
            if not self.server.shortname in serverCaches:         serverCaches[self.server.shortname] = {'channels':{self.event.parms.chanid: channelName}}
            elif  not 'channels' in serverCaches[self.server.shortname]: serverCaches[self.server.shortname]['channels'] = {self.event.parms.chanid: channelName}
            else: serverCaches[self.server.shortname]['channels'][self.event.parms.chanid] = channelName
        if self.event.event == 'removechannel':
            if not self.server.shortname in serverCaches: return
            if  not 'channels' in serverCaches[self.server.shortname]: return
            serverCaches[self.server.shortname]['channels'].pop(self.event.parms.chanid)

    def initializeCache(self):
        if self.server.shortname  not in serverCaches: serverCaches[self.server.shortname] = {'users': {}, 'channels': {}}
        for u in self.server.users:
            u = self.server.users[u]
            userInfo = {'username': u['username'], 'usertype': u['usertype']}
            userInfo['nickname'] = u['nickname'] if 'nickname' in u else f'user{u['userid']}'
            serverCaches[u['userid']] = userInfo
        for c in self.server.channels:
            c = self.server.channels[c]
            serverCaches[self.server.shortname]['channels'][c['chanid']] = self.server.channelname(c['chanid'])