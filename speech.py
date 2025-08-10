"""
Speach class, adapted from Electrode.
"""

from accessible_output3 import outputs
try:
    from speechd.client import SSIPCommunicationError
    speechdHere = True
except ImportError:
    speechdHere = False

class Speech:
    """
    Class for speaking and brailling output.
    """
    def __init__(self, outputType: str = "auto", **params):
        """
        initialize the speech class.


        :param outputType: Sets the type of output, nvda, jaws, sapi, voiceover, ns, zdsr, speechd, espeak, dolphin, pctalker, systemaccess, windoweyes, or auto, defaults to "auto"
        :type outputType: str, optional
        """
        self.output = self._getOutput(outputType)
        self.outputType = outputType
        self.params = params
        if speechdHere:
            if isinstance(self.output, outputs.speech_dispatcher.SpeechDispatcher):
                speechdClient = self.output._client
                speechdClient.set_priority('notification')
                # we do this so that orca can interrupt speech, otherwise the screenreader becomes unusable wile we are speaking.
                if 'outputModule' in params: speechdClient.set_output_module(params['outputModule'])
                if 'rate' in params: speechdClient.set_rate(params['rate'])
                if 'volume' in params: speechdClient.set_volume(params['volume'])
                if 'pitch' in params: speechdClient.set_pitch(params['pitch'])
                if 'voice' in params: speechdClient.set_synthesis_voice(params['voice'])
        if hasattr(outputs, 'sapi5'):
            if isinstance(self.output, outputs.sapi5.SAPI5):
                if 'rate' in params: self.output.set_rate(params['rate'])
                if 'volume' in params: self.output.set_volume(params['volume'])
                if 'pitch' in params: self.output.set_pitch(params['pitch'])
                if 'voice' in params: self.output.set_voice(params['voice'])

    @classmethod
    def _getOutput(self, outputType: str):
        """
        Gets the output from the provided string.

        :param outputType: The type of output, nvda, jaws,  sapi, voiceover, ns, zdsr, speechd, espeak, dolphin, pctalker, systemaccess, windoweyes, or auto
        :type outputType: str
        """
        match outputType:
            case "auto": return outputs.auto.Auto().get_first_available_output()
            #This only works once, we do not like the auto class from accessible output because it doesn't keep engine settings properly.
            case "dolphin": return outputs.dolphin.Dolphin()
            case "espeak": return outputs.e_speak.ESpeak()
            case "jaws": return outputs.jaws.Jaws()
            case "mac" | "mackintalk" | "ns" | "nsspeech": return outputs.nsspeechsynthesizer.MacSpeech()
            case "nvda": return outputs.nvda.NVDA()
            case "pctalker": return outputs.pc_talker.PCTalker()
            case "sapi" | "sapi5": return outputs.sapi5.SAPI5()
            case "speechd", "speech-dispatcher", "speechdispatcher": return outputs.speech_dispatcher.SpeechDispatcher()
            case "systemaccess": return outputs.system_access.SystemAccess()
            case "voiceover": return outputs.voiceover.VoiceOver()
            case "windoweyes": return outputs.window_eyes.WindowEyes()
            case "zdsr": return outputs.zdsr.ZDSR()

    def speak(self, text: str, interrupt: bool = True):
        """
        speaks the given text with the selected synthesizer.

        :param text: The text to be spoken.
        :type text: str
        :param interrupt: Sets if the spoken text should interrupt the currently speaking text, defaults to True
        :type interrupt: bool, optional
        """
        if speechdHere:
            if isinstance(self.output, outputs.speech_dispatcher.SpeechDispatcher):
                self._speechdSpeak(text, interrupt)
        else:
            self.output.speak(text, interrupt= interrupt)

    def braille(self, text: str):
        """
        Brailles the given text.

        :param text: The text to be Brailled
        :type text: str
        """
        self.output.braille(text)

    def both(self, text: str, interrupt: bool = True):
        """
        Outputs the given text thrue speech and Braill.

        :param text: The text to output.
        :type text: str
        :param interrupt: Sets if the spoken text should interrupt the currently speaking text, defaults to True
        :type interrupt: bool, optional
        """
        self.braille(text)
        self.speak(text, interrupt = interrupt)

    def _speechdSpeak(self, text: str, interrupt: bool = True):
        """
        Speaks the given text with the selected synthesizer. Called only if speechd is beeing used. This is so we can  handel recovery if comunication to speech-dispature is lost.

        :param text: The text to be spoken.
        :type text: str
        :param interrupt: Sets if the spoken text should interrupt the currently speaking text, defaults to True
        :type interrupt: bool, optional
        """
        try:
            self.output.speak(text, interrupt= interrupt)
        except SSIPCommunicationError:
            self.__init__(self.outputType, **self.params)
            self.output.speak(text, interrupt= interrupt)
