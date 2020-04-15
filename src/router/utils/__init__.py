class Singleton(type):
    """
    Singleton pattern.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


from .fetcher import Fetcher
from .stasher import Stasher
from .stasher import dynamodb_json_to_dict
from .country_mapper import CountryMapper
