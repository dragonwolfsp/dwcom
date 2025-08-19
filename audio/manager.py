"""
Sound Manager class for cyal, some code adapted from electrode.
"""

import cyal
from pool import Pool
from sound import Sound

class Manager:
	def __init__(self, path: str, key: str = "", device: cyal.Device | None=None, context: cyal.Context | None=None):
		self.device = device or cyal.Device()
		self.context=context or cyal.Context(self.device, make_current=True, hrtf_soft=1)
		self.alListener=self.context.listener
		self.alListener.orientation = [0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
		self.alListener.position = [0, 0, 0]
		self.pool=Pool(self.context, path, key = key)
		self.sounds: list[Sound]=[]
		

	def newSound(self, filePath: str, oneShot= False, **kwargs):
		s=Sound(self.context,self.pool.get(filePath),**kwargs)
		self.sounds.append(s)
		return s

	def tryCleanAll(self):
		for s in self.sounds:
			if s.isStopped: self.sounds.remove(s

	def forceCleanAll(self):
		for s in self.sounds:
			if not s.isStopped: s.stop()
		self.sounds.clear()