import abc
import collections

class BaseConsolidator:
    @abc.abstractclassmethod
    def consolidate(cls, candidates):
        raise NotImplementedError
    