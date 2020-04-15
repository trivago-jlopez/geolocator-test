"""
Google geocoder.
"""
import collections
import datetime
import time

import geocoder
import pytz

from geocode import helpers
from geocode.location import bounding_box
from geocode.providers.base import Geocoder,  geocoder_process


class Google(Geocoder):
    """
    Google geocoding service.
    """
    _version = '1.0.0'

    def __init__(self):
        super(Google, self).__init__(
            'google',
            nr_of_retries=1,
            initial_backoff=3,
            quota_exceed_on_throttle=True
        )

    def parse_components(self, address):
        return '|'.join([
            '{component}:{value}'.format(
                component=k,
                value=address[k]
            ) for k in sorted(address)
        ])

    def quota_reset(self):
        timezone = pytz.timezone('US/Pacific')
        pacific_time = datetime.datetime.now(tz=timezone)

        # combine tomorrow date in Pacific timezone with 10 minutes past midnight
        reset_time = datetime.datetime.combine(
            pacific_time.date() + datetime.timedelta(days=1),
            datetime.time(0)
        )

        return timezone.localize(reset_time).astimezone(pytz.utc).timestamp()

    @geocoder_process
    def _geocode(self, address):
        """
        Error handling is based on the Google_ documentation.
        
        .. _Google: https://developers.google.com/places/web-service/details
        """
        key = self._request_key()
        
        try:
            mapped_address = self._map(address)

            kwargs = key.copy()

            if 'guess' in address:
                bbox = bounding_box(
                    address['guess'],
                    100000
                )
                kwargs['bounds'] = '{south},{west}|{north},{east}'.format(**bbox)

            response = geocoder.google(
                mapped_address.pop('address', None),
                components=self.parse_components(mapped_address),
                **kwargs
            )

            if response.ok == True:
                return map(lambda x: x.json, response)
            elif response.error == 'OVER_QUERY_LIMIT':
                #TODO: google does not distinguish between qps blocking and quota running out
                raise helpers.RateLimitExceededError(self.name)
            elif response.error in ('UNKNOWN_ERROR', 'REQUEST_DENIED'):
                raise helpers.FailedRequestError(
                    self.name,
                    response.status
                )
            elif response.error == 'INVALID_REQUEST':
                raise helpers.InvalidRequestError(
                    self.name,
                    response.status
                )

        except KeyError:
            raise helpers.NoResultsFoundError(self.name)

        raise helpers.NoResultsFoundError(self.name)

    def _parse_returned_address(self, result):
        f = lambda: collections.defaultdict(f)
        raw = collections.defaultdict(f, result['raw'])

        extract = {
            'street': raw['route'].get('long_name'),
            'house_number': raw['street_number'].get('long_name'),
            'district': raw['sublocality'].get('long_name'),
            'city': raw['locality'].get('long_name'),
            'postal_code': raw['postal_code'].get('long_name'),
            'region': raw['administrative_area_level_1'].get('long_name'),
            'country': raw['country'].get('long_name'),
            'country_code': raw['country'].get('short_name')
        }

        return dict((k, v) for k, v in extract.items() if v)


class GooglePlaces(Geocoder):
    """
    Google geocoding service.
    """
    _version = '1.0.0'

    def __init__(self):
        super(GooglePlaces, self).__init__(
            'google_places',
            nr_of_retries=1,
            initial_backoff=3,
            quota_exceed_on_throttle=True
        )

    def parse_components(self, address):
        return '|'.join([
            '{component}:{value}'.format(
                component=k,
                value=address[k]
            ) for k in sorted(address)
        ])

    def quota_reset(self):
        timezone = pytz.timezone('US/Pacific')
        pacific_time = datetime.datetime.now(tz=timezone)

        # combine tomorrow date in Pacific timezone with 10 minutes past midnight
        reset_time = datetime.datetime.combine(
            pacific_time.date() + datetime.timedelta(days=1),
            datetime.time(0)
        )

        return timezone.localize(reset_time).astimezone(pytz.utc).timestamp()

    def check_quota(self):
        time.sleep(2.0)

    @geocoder_process
    def _geocode(self, address):
        """
        Error handling is based on the Google_ documentation.
        
        .. _Google: https://developers.google.com/places/web-service/details
        """
        key = self._request_key()
        
        try:
            mapped_address = self._map(address)

            kwargs = key.copy()

            if 'guess' in address:
                bbox = bounding_box(
                    address['guess'],
                    100000
                )
                kwargs['bounds'] = '{south},{west}|{north},{east}'.format(**bbox)

            response = geocoder.google(
                mapped_address.pop('address'),
                components=self.parse_components(mapped_address),
                **kwargs
            )

            if response.ok == True:
                return map(lambda x: x.json, response)
            elif response.error == 'OVER_QUERY_LIMIT':
                #TODO: google does not distinguish between qps blocking and quota running out
                raise helpers.RateLimitExceededError(self.name)
            elif response.error in ('UNKNOWN_ERROR', 'REQUEST_DENIED'):
                raise helpers.FailedRequestError(
                    self.name,
                    response.status
                )
            elif response.error == 'INVALID_REQUEST':
                raise helpers.InvalidRequestError(
                    self.name,
                    response.status
                )

        except KeyError:
            raise helpers.NoResultsFoundError(self.name)

        raise helpers.NoResultsFoundError(self.name)

    def _parse_returned_address(self, result):
        f = lambda: collections.defaultdict(f)
        raw = collections.defaultdict(f, result['raw'])

        extract = {
            'street': raw['route'].get('long_name'),
            'house_number': raw['street_number'].get('long_name'),
            'district': raw['sublocality'].get('long_name'),
            'city': raw['locality'].get('long_name'),
            'postal_code': raw['postal_code'].get('long_name'),
            'region': raw['administrative_area_level_1'].get('long_name'),
            'country': raw['country'].get('long_name'),
            'country_code': raw['country'].get('short_name')
        }

        return dict((k, v) for k, v in extract.items() if v)
