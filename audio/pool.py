"""
Sound pooll clas for cyall buffers, adapted from electrode.
"""
import os
import cyal
import soundfile

class Pool:
	def __init__(self, context: cyal.context, path: str):
		self.context=context
		self.cache={}
		elif not os.path.isdir(path):
			raise ValueError(f"{path} is not a directory.")
		self.path=path
		if not self.path.endswith("/"): self.path+="/"

	def get(self, file: str):
		if not file in self.cache.keys(): self.cache[file]=self.getBufferFromFile(file)
		return self.cache[file]

	def getBufferFromFile(self, file: str):
		fileObject = self.getFile(file)
		format=cyal.BufferFormat.MONO16 if fileObject.channels==1 else cyal.BufferFormat.STEREO16
		buffer = self.context.gen_buffer()
		data=fileObject.read(dtype='int16').tobytes()
		fileObject.close()
		buffer.set_data(data, sample_rate=fileObject.samplerate, format=format)
		return buffer

	def getFile(self, file: str):
		file=self.path+file
		fileObject=soundfile.SoundFile(file, 'r')
		return fileObject

	def clear(self):
		self.cache.clear()