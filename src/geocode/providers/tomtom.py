"""
Tomtom geocoder.
"""
import collections

import geocoder

from geocode import helpers
from geocode.providers.base import Geocoder, geocoder_process


class Tomtom(Geocoder):
    """
    Tomtom geocoding service.
    """
    _version = '1.0.0'

    def __init__(self):
        super(Tomtom, self).__init__('tomtom')

    def format_address(self, address):
        return ', '.join([address[i] for i in [
            'street',
            'district',
            'postal_code',
            'city',
            'region'
        ] if i in address])

    @geocoder_process
    def _geocode(self, address):
        key = self._request_key()

        try:
            query = self.format_address(address)
            kwargs = {
                'countrySet': address['country_code'],
                'maxRows': 100
            }
            kwargs.update(key)

            if 'guess' in address:
                kwargs['lon'] = address['guess']['longitude']
                kwargs['lat'] = address['guess']['latitude']
                kwargs['radius'] = 100000

            response = geocoder.tomtom(query, **kwargs)

            if response.ok:
                return map(lambda x: x.json, response)
            elif response.status_code == 403:
                raise helpers.QuotaExhaustedError(self.name)
            elif response.status_code == 404:
                raise helpers.NoResultsFoundError(self.name)

        except (KeyError, ValueError):
            raise helpers.NoResultsFoundError(self.name)
        except TypeError:
            raise helpers.FailedRequestError(
                self.name,
                ''
            )

        raise helpers.NoResultsFoundError(self.name)

    def _parse_returned_address(self, result):
        f = lambda: collections.defaultdict(f)
        raw = collections.defaultdict(f, result['raw'].get('address', {}))

        extract = {
            'street': raw.get('streetName'),
            'house_number': raw.get('streetNumber'),
            'district': raw.get('municipalitySubdivision'),
            'city': raw.get('municipality'),
            'postal_code': raw.get('postalCode'),
            'region': raw.get('countrySecondarySubdivision'),
            'country': raw.get('country'),
            'country_code': raw.get('countryCode')
        }

        return dict((k, v) for k, v in extract.items() if v)
