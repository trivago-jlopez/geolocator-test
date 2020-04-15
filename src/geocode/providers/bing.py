"""
Bing geocoder.
"""
import collections
import re

import geocoder

from geocode import helpers
from geocode.providers.base import Geocoder, geocoder_process


class Bing(Geocoder):
    """
    Bing geocoding service.
    """
    _version = '1.0.0'

    def __init__(self):
        super(Bing, self).__init__('bing')

    @geocoder_process
    def _geocode(self, address):
        key = self._request_key()

        try:
            response = geocoder.bing(None, maxRows=100, method='details', **key, **self._map(address))

            if response.ok:
                return map(lambda x: x.json, response)
            else:
                if response.status_code in (401, 403):
                    raise helpers.QuotaExhaustedError(self.name)
                elif response.status_code == 404:
                    raise helpers.NoResultsFoundError(self.name)
                elif response.status_code == 429:
                    raise helpers.RateLimitExceededError(self.name)
                elif response.status_code == 400:
                    raise helpers.InvalidRequestError(
                        self.name, response.status
                    )
                elif response.status_code in (500, 503):
                    raise helpers.FailedRequestError(
                        self.name, response.status
                    )

        except (KeyError, AttributeError):
            raise helpers.NoResultsFoundError(self.name)

        raise helpers.NoResultsFoundError(self.name)

    def _parse_returned_address(self, result):
        f = lambda: collections.defaultdict(f)
        raw = collections.defaultdict(f, result['raw'].get('address', {}))

        extract = {
            'district': raw.get('adminDistrict'),
            'city': raw.get('locality'),
            'postal_code': raw.get('postalCode'),
            'region': raw.get('neighborhood'),
            'country': raw.get('countryRegion')
        }

        if raw.get('addressLine'):
            match = re.search(
                r'(?P<number>\d+) (?P<street>.+)|(?P<street_alt>.+) (?P<number_alt>\d+)',
                raw['addressLine']
            )
            if match:
                match = match.groupdict()
                extract.update({
                    'house_number': match['number'] or match['number_alt'],
                    'street': match['street'] or match['street_alt'],
                })
            else:
                extract['street'] = raw.get('addressLine')

        return dict((k, v) for k, v in extract.items() if v)
