"""
The trigger class for dwcom
"""


import os
from rpaudio import AudioChannel, AudioSink
from trigger_cc import TriggerBase
from conf import conf
from notifiers import sendSystemNotification, sendProwlNotification, ntfyNotifier
from speech import Speech
from logger import getServerLogger

serverConfigs = conf.servers()
audioChannnel = AudioChannel()
audioChannnel.auto_consume = True

def getServerConfigItem(serverName: str, itemName: str):
    try:
        serverConfig = serverConfigs[serverName]
    except ValueError as e:
        print(e)
        return None
    try:
        return convertConfigValue(serverConfig[itemName])
    except KeyError:
        return None

def convertConfigValue(configValue: str):
    if configValue.isnumeric() and configValue != '1' and configValue != '0': return float(configValue)
    match configValue.lower():
        case 'y' | 'yes' | '1' | 'true': return True
        case 'n' | 'no' | '0' | 'false': return False
        case _: return configValue

serverCaches = {}

def getServerSpeaker(serverName: str):
    if serverName in serverCaches:
        if 'speaker' in serverCaches[serverName]: return serverCaches[serverName]['speaker']
    outputModule = getServerConfigItem(serverName, 'speechdmodule')
    rate= getServerConfigItem(serverName, 'speechrate')
    volume = getServerConfigItem(serverName, 'speechvolume')
    voice = getServerConfigItem(serverName, 'speechvoice')
    pitch = getServerConfigItem(serverName, 'speechpitch')
    speakerType = getServerConfigItem(serverName, 'speechengine')
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
    return userInfo

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
            output += f' {userTypeString} {prittyName} logged in'
        case 'loggedout':
            output += f' {userTypeString} {prittyName} logged out'
        case 'adduser':
            output += f' {userTypeString} {prittyName} joined channel {server.channelname(event.parms.chanid)}'
        case 'removeuser':
            output += f' {userTypeString} {prittyName} left channel {server.channelname(event.parms.chanid)}'
        case 'updateuser':
            statusMSG = event.parms.statusmsg if 'statusmsg' in event.parms else ''
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
            output += f'{prittyName} - {statusMode}'
            if statusMSG: output += f' - {statusMSG}'
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
            output += f'channel with id {event.parms.chanid} deleted'
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
        self.doTrigger = True
        if not self.doTrigger: return
        # Do not process events from a server that is not logged in
        if not self.server.loggedIn: return
        # do not process events if they are from hour user.
        if 'userid' in self.event.parms and self.server.me.userid == self.event.parms.userid: return
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

    def speak(self, message):
        doSpeak = getServerConfigItem(self.server.shortname, 'speech')
        if doSpeak != True and doSpeak is not None: return
        noSpeak = getServerConfigItem(self.server.shortname, 'nospeak')
        interrupt = getServerConfigItem(self.server.shortname, 'speechinterrupt')
        if interrupt is None: interrupt = True
        if noSpeak:
            if self.event.event in noSpeak.split('+'): return
        speaker = getServerSpeaker(self.server.shortname)
        speaker.both(message, interrupt = interrupt)

    def notify(self):
        if self.event.event in ('loggedin', 'loggedout') and getServerConfigItem(self.server.shortname, 'notifyloginout') == False: return
        elif self.event.event == 'messagedeliver' and getServerConfigItem(self.server.shortname, 'notifymessage') == False: return
        title = self.makeTitle()
        if getServerConfigItem(self.server.shortname, 'systemnotify') == True: sendSystemNotification(title, self.prittyEvent)
        if getServerConfigItem(self.server.shortname, 'ntfy') == True: self.ntfyNotify(title, self.prittyEvent)
        if getServerConfigItem(self.server.shortname, 'prowl') == True: self.prowlNotify(title, self.prittyEvent)

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
        serverUrl = getServerConfigItem(self.server.shortname, 'ntfyurl')
        if not serverUrl: serverUrl = 'https://ntfy.sh'
        topic = getServerConfigItem(self.server.shortname, 'ntfytopic')
        if not topic: raise NameError(f'ntfytopic not found in server config for {self.server.shortname}')
        user = getServerConfigItem(self.server.shortname, 'ntfyuser')
        password = getServerConfigItem(self.server.shortname, 'ntfypassword')
        notifyer = ntfyNotifier(serverUrl, topic, user, password)
        notifyer.sendNotification(title, message)

    def prowlNotify(self, title: str, message: str):
        prowlKey = getServerConfigItem(self.server.shortname, 'prowlkey')
        if not prowlKey: raise NameError(f'prowlkey not found in config for {self.server.shortname}')
        sendProwlNotification(prowlKey, title, message)

    def logEvent(self):
        log = getServerConfigItem(self.server.shortname, 'log')
        if log != True and log is not None: return
        maxSize = getServerConfigItem(self.server.shortname, 'maxlogsize') 
        maxSize = maxSize * 1024 * 1024 if maxSize is not None else 4 * 1024 * 1024
        maxFiles = getServerConfigItem(self.server.shortname, 'maxlogfiles')
        if maxFiles is None: maxFiles = 5
        logger = getServerLogger(self.server.shortname, 'logs', maxSize, maxFiles)
        logger.info(self.prittyEvent)

    def playSound(self):
        playSounds = getServerConfigItem(self.server.shortname, 'sounds')
        if playSounds != True and  playSounds is not  None: return
        soundPack = getServerConfigItem(self.server.shortname, 'soundpack')
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
        for filetype in ('wav', 'flac', 'mp3'):
            fullSoundPath = f'sounds/{soundPack}/{sound}.{filetype}'
            if os.path.exists(fullSoundPath): break
            fullSoundPath = None
        playerType = getServerConfigItem(self.server.shortname, 'playbacktype')
        if playerType is None: playerType = 'overlapping'
        sink = AudioSink().load_audio(os.path.abspath(fullSoundPath))
        volume = getServerConfigItem(self.server.shortname, 'soundVolume')
        volume = volume/100 if volume is not None else 1.0
        sink.set_volume(volume)
        match playerType.lower():
            case 'onebyone':
                audioChannnel.push(sink)
            case 'interrupting':
                audioChannnel.drop_current_audio()
                audioChannnel.push(sink)
            case 'overlapping':
                sink.play()
            case _:
                raise ValueError(f'Failed to play sound:\n unsupported playback type {playerType}')
