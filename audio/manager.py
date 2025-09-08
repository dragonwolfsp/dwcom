"""
Sound Manager class for cyal, some code adapted from electrode.
"""

from threading import Thread
from queue import Queue, Empty
from time import sleep
import cyal
from .pool import Pool
from .sound import Sound

class Manager:
	def __init__(self, path: str, device: cyal.Device | None=None, context: cyal.Context | None=None):
		self.device = device or cyal.Device()
		self.context=context or cyal.Context(self.device, make_current=True, hrtf_soft=1)
		self.alListener=self.context.listener
		self.alListener.orientation = [0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
		self.alListener.position = [0, 0, 0]
		self.pool=Pool(self.context, path)
		self.sequentialSounds: Queue[Sound]= Queue()
		self.replacedSound = None
		self.sequentialWorker = Thread(target=self._sequentialLoop, daemon=True)
		self.sequentialWorker.start()
		self.sounds: list[Sound] = []

	def _newSound(self, filePath: str, **kwargs):
		s = Sound(self.context, self.pool.get(filePath), **kwargs)
		s.direct = True
		return s

	def _sequentialLoop(self):
		while True:
			try:
				s = self.sequentialSounds.get(timeout=0.1)
			except Empty:
				continue
			s.play()
			while s.isPlaying: sleep(0.003)
			self.sequentialSounds.task_done()

	def play(self, filePath: str, playType: int, **kwargs):
		self.cleanSounds()
		s = self._newSound(filePath, **kwargs)
		if playType == 0:
			self.sounds.append(s)
			s.play()
		elif playType == 1:
			if self.replacedSound is not None:
				if self.replacedSound.isPlaying: self.replacedSound.stop()
			self.replacedSound = s
			self.replacedSound.play()
		else:
			self.sequentialSounds.put(s)

	def cleanSounds(self):
		for s in self.sounds:
			if not s.isPlaying: self.sounds.remove(s)