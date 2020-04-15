"""
Geonames geocoder.
"""
import collections

import geocoder
import ratelim

from geocode import helpers, location
from geocode.providers.base import Geocoder, geocoder_process


class Geonames(Geocoder):
    """
    Geonames geocoding service.
    """
    _version = '1.0.0'

    def __init__(self):
        super(Geonames, self).__init__('geonames')

    @geocoder_process
    @ratelim.patient(1, 1)
    def _geocode(self, address):
        """
        TODO ERRORS
        """
        try:
            kwargs = {
                "location": address["city"],
                "country": address["country_code"],
                "key": self._request_key()
            }                      

            if 'guess' in address:
                bbox = location.bounding_box(
                    address['guess'],
                    100000
                )
                kwargs = {**kwargs, **bbox}

            response = geocoder.geonames(**kwargs)
            if response.ok:
                return map(lambda x: x.json, response)
            else:
                if response.status_code == 429:
                    raise helpers.RateLimitExceededError(self.name)

        except KeyError:
            raise helpers.NoResultsFoundError(self.name)

        raise helpers.NoResultsFoundError(self.name)

    def _parse_returned_address(self, result):
        f = lambda: collections.defaultdict(f)
        raw = collections.defaultdict(f, result['raw'].get('address', {}))

        extract = {
            'city': raw.get('city'),
            'region': raw.get('state'),
            'country': raw.get('country'),
            'country_code': raw.get('country_code')
        }

        return dict((k, v) for k, v in extract.items() if v)
