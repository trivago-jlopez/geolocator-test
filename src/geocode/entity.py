"""
Entities that can be geocoded in the World domain. These include hotels, destinations and point of
interest.
"""
import abc
from itertools import chain
import logging


LOGGER = logging.getLogger('trvcoder.entity')
LOGGER.setLevel(logging.INFO)


class Entity(metaclass=abc.ABCMeta):
    """
    Entity class with a unique identifier.
    """
    def __init__(self, entity_id, entity_type):
        self.entity_id = entity_id
        self.entity_type = entity_type

    @abc.abstractproperty
    def address(self) -> dict:
        """
        Each entity decided what text components best describes its location. The location can be
        iterative in nature.
        """
        raise NotImplementedError


class Accommodation(Entity):
    """
    Address representation of a hotel. A hotel always has a street and country code.
    """
    __fields = [
        'street',
        'house_number',
        'country_code',
        'name',
        'district',
        'city',
        'region',
        'postal_code',
        'country',
        'guess'
    ]

    def __init__(self, entity_id, **kwargs):
        super(Accommodation, self).__init__(entity_id, 'accommodation')

        # optional fields
        for field in self.__fields:
            if field in kwargs:
                setattr(self, field, kwargs[field])


    @property
    def address(self):
        """
        Address components of an entity.
        """
        return dict(filter(lambda pair: pair[0] in self.__fields, vars(self).items()))


class ReferenceAccommodation(Accommodation):
    """
    Address representation of a reference hotel.
    """
    def __init__(self, entity_id, **kwargs):
        super(ReferenceAccommodation, self).__init__(entity_id, **kwargs)
        self.entity_type = 'reference_accommodation'


class CandidateAccommodation(Accommodation):
    """
    Address representation of a reference hotel.
    """
    def __init__(self, entity_id, **kwargs):
        super(CandidateAccommodation, self).__init__(entity_id, **kwargs)
        self.entity_type = 'candidate_accommodation'


class Destination(Entity):
    """
    Representation of a destination; a destination has a unique id, city name, country_code and optionally a coords guess.
    """
    __fields = [
        'city',
        'country_code',
        'guess'
    ]

    def __init__(self, entity_id, **kwargs):
        super(Destination, self).__init__(entity_id, 'destination')
        
        for field in self.__fields:
            if field in kwargs:
                setattr(self, field, kwargs[field])


    @property
    def address(self):
        """
        Address of a city is the city name and the country-code. The country-code should be specified, in order to avoid
        confusion between same name destinations in different countries.
        """
        return dict(filter(lambda pair: pair[0] in self.__fields, vars(self).items()))


class PointOfInterest(Entity):
    """
    Address representation of a point of interest. A point of interest always has a street and
    country code.
    """
    __fields = [
        'street',
        'house_number',
        'country_code',
        'name',
        'district',
        'city',
        'region',
        'postal_code',
        'country',
        'guess'
    ]

    def __init__(self, entity_id, **kwargs):
        super(PointOfInterest, self).__init__(entity_id, 'point_of_interest')

        # optional fields
        for field in self.__fields:
            if field in kwargs:
                setattr(self, field, kwargs[field])


    @property
    def address(self):
        """
        Address components of an entity.
        """
        return dict(filter(lambda pair: pair[0] in self.__fields, vars(self).items()))


class CandidatePointOfInterest(PointOfInterest):
    """
    Address representation of a candidate point of interest.
    """
    def __init__(self, entity_id, **kwargs):
        super(CandidatePointOfInterest, self).__init__(entity_id, **kwargs)
        self.entity_type = 'candidate_point_of_interest'
