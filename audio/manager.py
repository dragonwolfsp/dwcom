"""
Sound Manager class for cyal, some code adapted from electrode.
"""

from threading import Thread
from time import sleep
import cyal
from pool import Pool
from sound import Sound

class Manager:
	def __init__(self, path: str, device: cyal.Device | None=None, context: cyal.Context | None=None):
		self.device = device or cyal.Device()
		self.context=context or cyal.Context(self.device, make_current=True, hrtf_soft=1)
		self.alListener=self.context.listener
		self.alListener.orientation = [0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
		self.alListener.position = [0, 0, 0]
		self.pool=Pool(self.context, path)
		self.sounds: list[Sound]=[]
		

	def newSound(self, filePath: str, **kwargs):
		s=Sound(self.context,self.pool.get(filePath),**kwargs)
		s.direct = True
		self.sounds.append(s)
		return s

	def tryCleanAll(self):
		for s in self.sounds:
			if s.isStopped: self.sounds.remove(s)

	def forceCleanAll(self):
		for s in self.sounds:
			if not s.isStopped: s.stop()
		self.sounds.clear()

	def _pushAndWait(self):
		for s in self.sounds:
			if not s.isPlaying(): s.play()
			while s.isPlaying(): sleep(0.003)
			self.sounds.remove(s)

	def _pushAndStop(self):
		s = self.sounds[-1]
		self.forceCleanAll()
		s.play()

	def _push(self):
		for s in self.sounds:
			s.play()

	def run(self, playVType: int):
		thread = None
		if playType == 0:
			thread = Thread(target = self._push)
		elif playType == 1:
			thread = Thread(target = self._pushAndStop)
		else:
			thread = Thread(target = self._pushAndWait)
		thread.start()