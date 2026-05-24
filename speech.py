"""
Speach class, adapted from Electrode.
"""
import prism

class Speech:
    """
    Class for speaking and brailling output.
    """
    def __init__(self, context: prism.Context | None=None, outputType: str = "auto", **params):
        """initialize the speech class.

        Args:
            context (prism.Context | None, optional): The prism context for the speech class to use. Defaults to None.
            outputType (str, optional): Sets the output through wich the speech class will speak, nvda, jaws, zoomtext, sapi, onecore, voiceover, ns, zdsr, speechd, orca,  pctalker, pcreader, systemaccess, windoweyes, or auto. Defaults to "auto".
        """
        self.context=context or prism.Context()
        self.output = self._getOutput(outputType)
        self.outputType = outputType
        outputFeatures        = self.output.features
        if 'voice' in params and outputFeatures.supports_set_voice:
            self.output.voice = params['voice']
        if 'rate' in params and outputFeatures.supports_set_rate:
            self.output.rate = params['rate']
        if 'pitch' in params and outputFeatures.supports_set_pitch:
            self.output.pitch = params['pitch']
        if 'volume' in params and outputFeatures.supports_set_volume:
            self.output.volume = params['volume']

    def _getOutput(self, outputType: str) -> prism.Backend:
        """
        Gets the output from the provided string.

        :param outputType: The type of output, nvda, jaws, zoomtext, sapi, onecore, voiceover, ns, zdsr, speechd, orca,  pctalker, pcreader, systemaccess, windoweyes, or auto
        :type outputType: str
        """
        output = None
        if outputType == 'auto' or outputType == 'best':
            return self.context.acquire_best()
        match outputType:
            case "jaws" | "jfw": output = prism.BackendId.JAWS
            case "mac" | "mackintalk" | "ns" | "nsspeech" | "avspeech": output = prism.BackendId.AV_SPEECH
            case "nvda": output = prism.BackendId.NVDA
            case "pctalker": output = prism.BackendId.PC_TALKER
            case "sapi" | "sapi5": output = prism.BackendId.SAPI
            case "speechd" | "speech-dispatcher" | "speechdispatcher": output = prism.BackendId.SPEECH_DISPATCHER
            case "voiceover": output = prism.BackendId.VOICE_OVER
            case "zdsr": output = prism.BackendId.ZDSR
            case "orca": output = prism.BackendId.ORCA
            case "zoomtext" | "zt": output = prism.BackendId.ZOOM_TEXT
            case             "onecore": output = prism.BackendId.ONE_CORE
            case "boipcreader" | "pcreader": output = prism.BackendId.BOY_PC_READER
            case "systemaccess": output = prism.BackendId.SYSTEM_ACCESS
            case "windoweyes": output = prism.BackendId.WINDOW_EYES
            case _: raise ValueError('outputType is not one of: nvda, jaws, zoomtext, sapi, onecore, voiceover, ns, zdsr, speechd, orca,  pctalker, pcreader, systemaccess, windoweyes,  auto.')
        if self.context.exists(output):
            return self.context.create(output)
        else:
            raise RuntimeError(f'The backend {self.context.name_of(output)} cannot be initialized.')


    def speak(self, text: str, interrupt: bool = True):
        """
        speaks the given text with the selected synthesizer.

        :param text: The text to be spoken.
        :type text: str
        :param interrupt: Sets if the spoken text should interrupt the currently speaking text, defaults to True
        :type interrupt: bool, optional
        """
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
        self.output.output(text, interrupt = interrupt)

    def _Cleanup(self) -> None:
        self.output.stop()
        prism.lib.prism_backend_free(self.output._raw)