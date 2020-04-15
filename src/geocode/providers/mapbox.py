"""
Mapbox geocoder.
"""
import collections

import geocoder

from geocode import helpers, location
from geocode.providers.base import Geocoder, geocoder_process


class Mapbox(Geocoder):
    """
    Mapbox geocoding service.
    """
    _version = '1.0.0'

    def __init__(self):
        super(Mapbox, self).__init__('mapbox')

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
                'country': address['country_code']
            }

            if 'guess' in address:
                bbox = location.bounding_box(
                    address['guess'],
                    100000
                )

                kwargs['bbox'] = [
                    bbox['west'], bbox['south'], bbox['east'], bbox['north']
                ]

            response = geocoder.mapbox(query, **key, **kwargs)

            if response.ok:
                return map(lambda x: x.json, response)
            else:
                if response.status_code == 404:
                    raise helpers.NoResultsFoundError(self.name)
                if response.status_code == 401:
                    raise helpers.QuotaExhaustedError(self.name)

        except KeyError:
            raise helpers.NoResultsFoundError(self.name)

        raise helpers.NoResultsFoundError(self.name)

    def _parse_returned_address(self, result):
        f = lambda: collections.defaultdict(f)
        raw = collections.defaultdict(f, result['raw'])

        extract = {
            'street': raw.get('text'),
            'house_number': raw.get('address'),
            'district': raw.get('place'),
            'city': raw.get('locality'),
            'postal_code': raw.get('postcode'),
            'region': raw.get('region'),
            'country': raw.get('country'),
        }

        for i in raw.get('context', []):
            if i['id'].startswith('country'):
                extract['country_code'] = i['short_code']

        return dict((k, v) for k, v in extract.items() if v)
