"""
Here geocoder.
"""
import collections

import geocoder

from geocode import helpers
from geocode.providers.base import Geocoder, geocoder_process


class Here(Geocoder):
    """
    Here.com geocoding service.
    """
    _version = '1.0.0'

    def __init__(self):
        super(Here, self).__init__('here')

    @geocoder_process
    def _geocode(self, address):
        key = self._request_key()

        try:
            kwargs = self._map(address)

            if 'guess' in address:
                kwargs['prox'] = '{latitude},{longitude},100000'.format(
                    **address['guess']
                )

            kwargs.update(key)
            kwargs['maxRows'] = 100

            response = geocoder.here(None, **kwargs)

            if response.ok:
                return map(lambda x: x.json, response)
            else:
                if response.status_code == 401:
                    raise helpers.InvalidRequestError(
                        self.name,
                        response.status
                    )

        except (KeyError, AttributeError, IndexError):
            raise helpers.NoResultsFoundError(self.name)

        raise helpers.NoResultsFoundError(self.name)

    def _parse_returned_address(self, result):
        f = lambda: collections.defaultdict(f)
        raw = collections.defaultdict(f, result['raw'].get('Address', {}))

        extract = {
            'street': raw.get('Street'),
            'house_number': raw.get('HouseNumber'),
            'district': raw.get('District'),
            'city': raw.get('City'),
            'postal_code': raw.get('PostalCode'),
            'region': raw.get('State'),
            'country': result['raw'].get('CountryName'),
            'country_code': raw.get('Country')
        }

        return dict((k, v) for k, v in extract.items() if v)
