"""
OpenStreetMap geocoder.
"""
import collections

import geocoder
import ratelim

from geocode import helpers, location
from geocode.providers.base import Geocoder, geocoder_process


class Osm(Geocoder):
    """
    OpenStreetMap geocoding service.
    """
    # custom server with medium plan
    __url = 'https://geocoding.geofabrik.de/c6d3f7c0d768419090eb35788e821a30/search'
    _version = '1.0.0'

    def __init__(self):
        super(Osm, self).__init__('osm')

    @geocoder_process
    @ratelim.patient(1, 1)
    def _geocode(self, address):
        """
        Error handling is based on OpenStreetMap documentation on Nominatim, a tool to search OSM
        data by name. See OSM_.

        .. _OSM: https://wiki.openstreetmap.org/wiki/Nominatim
        """
        try:
            kwargs = self._map(address)
            kwargs['method'] = 'details'
            kwargs['url'] = self.__url

            if 'guess' in address:
                bbox = location.bounding_box(
                    address['guess'],
                    100000
                )

                kwargs['viewbox'] = '{west},{south},{east},{north}'.format(**bbox)
                kwargs['bounded'] = '1'

            response = geocoder.osm(None, **kwargs)

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
            'street': raw.get('road'),
            'house_number': raw.get('house_number'),
            'district': raw.get('suburb'),
            'city': raw.get('city'),
            'postal_code': raw.get('postcode'),
            'region': raw.get('state'),
            'country': raw.get('country'),
            'country_code': raw.get('country_code')
        }

        return dict((k, v) for k, v in extract.items() if v)
