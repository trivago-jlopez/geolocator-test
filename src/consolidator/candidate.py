"""
Candidate class to represent candidates as a source of geocodes for an entity.
"""
import collections

AccommodationCandidateBase = collections.namedtuple(
    'AccomodationCandidate',
    (
        'provider',
        'longitude',
        'latitude',
        'accuracy',
        'confidence',
        'quality',
        'score',
        'city',
        'country_code'
    )
)

class AccommodationCandidate(AccommodationCandidateBase):
    def __new__(cls, provider, **kwargs):
        return super(AccommodationCandidate, cls).__new__(
            cls,
            provider,
            kwargs['longitude'],
            kwargs['latitude'],
            kwargs.get('accuracy'),
            kwargs.get('confidence'),
            kwargs.get('quality'),
            kwargs.get('score'),
            kwargs.get('city'),
            kwargs.get('country_code')
        )


    def to_dict(self):
        return {
            'provider': self.provider,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'city': self.city,
            'country_code': self.country_code
        }


PointOfInterestCandidateBase = collections.namedtuple(
    'PointOfInterestCandidate',
    (
        'provider',
        'longitude',
        'latitude',
        'accuracy',
        'confidence',
        'quality',
        'score',
        'city',
        'country_code'
    )
)

class PointOfInterestCandidate(PointOfInterestCandidateBase):
    def __new__(cls, provider, **kwargs):
        return super(PointOfInterestCandidate, cls).__new__(
            cls,
            provider,
            kwargs['longitude'],
            kwargs['latitude'],
            kwargs.get('accuracy'),
            kwargs.get('confidence'),
            kwargs.get('quality'),
            kwargs.get('score'),
            kwargs.get('city'),
            kwargs.get('country_code')
        )


    def to_dict(self):
        return {
            'provider': self.provider,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'city': self.city,
            'country_code': self.country_code
        }


DestinationCandidateBase = collections.namedtuple(
    'DestinationCandidate',
    (
        'provider',
        'longitude',
        'latitude',
        'accuracy',
        'confidence',
        'quality',
        'score',
        'country_code'
    )
)

class DestinationCandidate(DestinationCandidateBase):
    def __new__(cls, provider, **kwargs):
        return super(DestinationCandidate, cls).__new__(
            cls,
            provider,
            kwargs['longitude'],
            kwargs['latitude'],
            kwargs.get('accuracy'),
            kwargs.get('confidence'),
            kwargs.get('quality'),
            kwargs.get('score'),
            kwargs.get('country_code')
        )


    def to_dict(self):
        return {
            'provider': self.provider,
            'longitude': self.longitude,
            'latitude': self.latitude,
            'country_code': self.country_code
        }
