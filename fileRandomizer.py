"""    
File line randomization functions for use with dwcom
"""

from random import choice
from os.path import abspath, exists

cache = {}

def getRandomLine(filePath: str):
    if filePath in cache: return choice(cache[filePath])
    if not exists(filePath): raise FileNotFoundError(f'the file {filePath} could not be found on the system.')
    with open(abspath(filePath), 'w') as f:
        lines = f.readlines()
        cache[filePath] = lines
        return choice(lines)    

def clearCache():
    cache.clear()