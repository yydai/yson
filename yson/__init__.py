__version__ = '2.1.1'
__author__ = 'Ying Dai'

from .decoder import JSONDecoder

json = JSONDecoder()

__all__ = ['loads']


def loads(s):
    return json.decode(s)
