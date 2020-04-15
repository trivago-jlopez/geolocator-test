"""
Mapquest geocoder.
"""
import collections
import re

import geocoder

from geocode import helpers, location
from geocode.providers.base import Geocoder, geocoder_process


class Mapquest(Geocoder):
    """
    Mapquest geocoding service.
    """
    _version = '1.0.0'

    def __init__(self):
        super(Mapquest, self).__init__('mapquest')

    def format_address(self, address):
        return ', '.join([address[i] for i in [
            'street',
            'district',
            'postal_code',
            'city',
            'region',
            'country_code'
        ] if i in address])

    @geocoder_process
    def _geocode(self, address):
        key = self._request_key()

        try:
            query = self.format_address(address)
            kwargs = {
                'maxRows': 100
            }
            kwargs.update(key)

            if 'guess' in address:
                bbox = location.bounding_box(
                    address['guess'],
                    100000
                )
                kwargs['bbox'] = [bbox['west'], bbox['south'], bbox['east'], bbox['north']]

            response = geocoder.mapquest(query, **kwargs)

            if response.ok:
                return map(lambda x: x.json, response)
            else:
                if response.status_code == 403:
                    raise helpers.QuotaExhaustedError(self.name)
                elif response.status_code == 400:
                    raise helpers.InvalidRequestError(
                        self.name, response.status
                    )
                elif response.status_code == 500:
                    raise helpers.FailedRequestError(
                        self.name, response.status
                    )

        except (KeyError, AttributeError):
            raise helpers.NoResultsFoundError(self.name)

        raise helpers.NoResultsFoundError(self.name)

    def _parse_returned_address(self, result):
        f = lambda: collections.defaultdict(f)
        raw = collections.defaultdict(f, result['raw'])

        extract = {
            'district': raw.get('adminArea6'),
            'city': raw.get('adminArea5'),
            'postal_code': raw.get('postalCode'),
            'region': raw.get('adminArea3'),
            'country': raw.get('adminArea1'),
            'country_code': raw.get('adminArea1')
        }

        if raw.get('street'):
            match = re.search(
                r'(?P<number>\d+) (?P<street>.+)|(?P<street_alt>.+) (?P<number_alt>\d+)',
                raw['street']
            )
            if match:
                match = match.groupdict()
                extract.update({
                    'house_number': match['number'] or match['number_alt'],
                    'street': match['street'] or match['street_alt'],
                })
            else:
                extract['street'] = raw.get('street')

        return dict((k, v) for k, v in extract.items() if v)
