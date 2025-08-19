"""
Basic sound class for cyal, adapted from electrode.
"""

import cyal

class Sound:
	def __init__(self, context: cyal.Context, buffer: cyal.Buffer, **kwargs):
		self.context=context
		self.buffer=buffer
		self.alSource=context.gen_source()
		self.alSource.buffer=self.buffer
		self.alSource.spatialize = True
		self.position=[0.0, 0.0, 0.0]
		self._direct = False
		self.playedOnce=False
		for key, value in kwargs.items():
			setattr(self, key, value)

	@property
	def x(self):
		return self.alSource.position[0]

	@x.setter
	def x(self, val: float):
		pos=self.alSource.position
		self.alSource.position=[val, pos[1], pos[2]]

	@property
	def y(self):
		return self.alSource.position[1]

	@y.setter
	def y(self, val: float):
		pos=self.alSource.position
		self.alSource.position=[pos[0], val, pos[2]]

	@property
	def z(self):
		return self.alSource.position[2]

	@z.setter
	def z(self, val: float):
		pos=self.alSource.position
		self.alSource.position=[pos[0], pos[1], val]

	@property
	def position(self):
		return self.alSource.position

	@position.setter
	def position(self, val):
		self.alSource.position=val

	@property
	def direction(self):
		return self.alSource.direction

	@direction.setter
	def direction(self, val):
		self.alSource.direction=val

	@property
	def pitch(self):
		return self.alSource.pitch*100

	@pitch.setter
	def pitch(self, val: float):
		self.alSource.pitch=val/100

	@property
	def direct(self):
		return self._direct

	@direct.setter
	def direct(self, val):
		if val==True:
			self.alSource.relative=True
			self.alSource.direct_channels=True
			self.position =[0.0, 0.0, 0.0]
			self._direct = True
		elif val==False:
			self.alSource.relative=False
			self.alSource.direct_channels=False
			self._direct = False

	@property
	def rolloffFactor(self):
		return self.alSource.rolloff_factor*100

	@rolloffFactor.setter
	def rolloffFactor(self, val):
		self.alSource.rolloff_factor=val/100

	@property
	def looping(self):
		return self.alSource.looping

	@looping.setter
	def looping(self, val):
		self.alSource.looping=val

	@property
	def gain(self):
		return self.alSource.gain*100

	@gain.setter
	def gain(self, val):
		self.alSource.gain=val/100

	@property
	def isPlaying(self):
		return self.alSource.state==cyal.SourceState.PLAYING

	@property
	def isPaused(self):
		return self.source.state == cyal.SourceState.PAUSED

	@property
	def isStopped(self):
		return self.alSource.state in [cyal.SourceState.INITIAL, cyal.SourceState.STOPPED,]

	def play(self):
		if self.isPlaying: return
		if not self.playedOnce: self.playedOnce=True
		return self.alSource.play()

	def stop(self):
		if self.isPlaying: return self.alSource.stop()

	def pause(self):
		if self.isPlaying: return self.alSource.pause()