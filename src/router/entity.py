import abc
import logging

from router import logger


class Entity(metaclass=abc.ABCMeta):
    def __init__(self, entity_id, entity_type):
        self.entity_id = entity_id
        self.entity_type = entity_type
    
    @property
    def key(self):
        return '{entity_type}:{entity_id}'.format(
            entity_id = self.entity_id,
            entity_type = self.entity_type
        )

    @abc.abstractproperty
    def address(self):
        raise NotImplementedError


class CandidateAccommodation(Entity):
    def __init__(self, **kwargs):
        super(CandidateAccommodation, self).__init__(kwargs['candidate_id'], 'candidate_accommodation')
        self.name = kwargs.get('name')
        self.street_address = kwargs.get('street')
        self.postal_code = kwargs.get('postal_code')
        self.district = kwargs.get('district')
        self.city = kwargs.get('city')
        self.region = kwargs.get('region')
        self.country = kwargs.get('country')
        self.longitude = kwargs.get('longitude')
        self.latitude = kwargs.get('latitude')
        self.flag = kwargs.get('flag', {})

        if 'country_mapper' in kwargs:
            self.country_code = self.get_country_code(kwargs['country_mapper'])
        else:
            self.country_code = None

        if not self.country_code:
            logger.log_event(logging.INFO, 'missing country code', country=self.country)

    def get_country_code(self, country_mapper):
        if self.country:
            if country_mapper.is_valid_country_code(self.country):
                return self.country

            by_iso_3166_3 = country_mapper.map_iso_3166_3(self.country)
            if by_iso_3166_3:
                return by_iso_3166_3

            by_name = country_mapper.map_name(self.country)
            if by_name:
                return by_name

        return None

    @property
    def address(self):
        data = {
            'name': self.name,
            'street': self.street_address,
            'district': self.district,
            'postal_code': self.postal_code,
            'city': self.city,
            'region': self.region,
            'country': self.country,
            'country_code': self.country_code
        }

        if self.longitude and self.latitude:
            data['guess'] = {
                'longitude': self.longitude,
                'latitude': self.latitude
            }

        return dict((k, v) for k, v in data.items() if v)

    def as_address(self):
        address = self.address

        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'address': address
        }

    def as_consolidation(self):
        return {
            'entity': ':'.join([self.entity_type, str(self.entity_id)]),
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'score': 1.0,
            'meta': {
                'city': self.city,
                'country_code': self.country_code
            }
        }

    def to_dict(self):
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type,
            'name': self.name,
            'longitude': self.longitude,
            'latitude': self.latitude
        }
