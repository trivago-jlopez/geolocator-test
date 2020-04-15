import functools
import itertools

def lazyprop(function):
    attr_name = '_' + function.__name__

    @property
    @functools.wraps(function)
    def _lazyprop(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, function(self))

        return getattr(self, attr_name)

    return _lazyprop
