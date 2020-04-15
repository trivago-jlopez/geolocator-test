"""
Base functionality for a geocode provider.
"""
import abc
import datetime
import functools
import itertools
import logging
import math
import os
import random
import time
import yaml

from fuzzywuzzy import fuzz
from packaging import version
import rollbar

from geocode import credentials, location, logger
from geocode.helpers import RateLimitExceededError, QuotaExhaustedError, NoResultsFoundError, FailedRequestError


CONFIG = yaml.safe_load(open('data/config.yml'))

KEY_HANDLER = credentials.KeyHandler(os.environ['SECRET_NAME'], os.environ['GEOCODER_API_KEYS'])


def rate_result(returned_address, returned_coordinates, address):
    """
    Compares and rates a retrieved result with an input address.
    """
    score = 0.0

    if 'street' in returned_address and 'house_number' in returned_address:
        returned_address['street'] = ' '.join([returned_address['house_number'], returned_address['street']])

    shared_keys = set(returned_address.keys()) & set(address.keys())

    # linguistic scoring: street
    if 'street' in shared_keys:
        if fuzz.token_set_ratio(returned_address['street'], address['street']) > 75:
            score += 1.0

    # linguistic scoring: district
    if 'district' in shared_keys:
        if fuzz.token_set_ratio(returned_address['district'], address['district']) > 75:
            score += 1.0

    # linguistic scoring: city
    if 'city' in shared_keys:
        if fuzz.token_set_ratio(returned_address['city'], address['city']) > 75:
            score += 1.0

    # linguistic scoring: postal code
    if 'postal_code' in shared_keys:
        if fuzz.token_set_ratio(returned_address['postal_code'], address['postal_code']) > 75:
            score += 1.0

    # linguistic scoring: region
    if 'region' in shared_keys:
        if fuzz.token_set_ratio(returned_address['region'], address['region']) > 75:
            score += 1.0

    if 'guess' in address:
        guess = address['guess']

        distance = location.distance_geocodes(guess, returned_coordinates)

        distance_score = 3.0

        t = -10.0 / math.log(0.5)
        if distance > 10:
            # drop off after 10 meters
            distance_score *= math.exp((10.0 - distance) / t)

        score += distance_score

    return score


def geocoder_process(function):
    """
    Decorator to clean up responses returned from the geocoder package.
    """
    @functools.wraps(function)
    def _geocoder_process(self, address):
        def filter_best_candidate(results, address):
            return max(results, key=lambda x: rate_result(
                self.parse_returned_address(x),
                {
                    'longitude': x['longitude'],
                    'latitude': x['latitude'],
                },
                address
            ))

        responses = list(function(self, address))

        # delete obsolete or sentitive fields
        fields = (
            'client',
            'client_secret',
            'key',
            'ak',
            'sk',
            'ok'
        )

        filtered_responses = []

        for result in responses:
            try:
                for field in fields:
                    if field in result:
                        del result[field]

                result['longitude'] = result.pop('lng')
                result['latitude'] = result.pop('lat')

                filtered_responses.append(result)
            except KeyError:
                continue

        if filtered_responses:
            return filter_best_candidate(filtered_responses, address)
        else:
            raise NoResultsFoundError(self.name)

    return _geocoder_process


def back_off_and_jitter(function):
    """
    Decorator to perform a function with back off with jitter when a specific error is thrown.
    """
    @functools.wraps(function)
    def _back_off_and_jitter(self, *args, **kwargs):
        back_off = self.initial_backoff     # initial back off time
        cap = 60                            # maximum back off is 60 seconds

        base = 1
        nr_of_retries = self.nr_of_retries
        quota_exceed_on_throttle = self.quota_exceed_on_throttle

        attempts = 0
        keys_used = 1
        while True:
            try:
                try:
                    result = function(self, *args, **kwargs)
                    return result
                except (FailedRequestError, RateLimitExceededError) as error:
                    if attempts >= nr_of_retries:
                        if isinstance(error, RateLimitExceededError) and quota_exceed_on_throttle:
                            raise QuotaExhaustedError(self.name)
                        else:
                            raise error

                    event = dict(
                        state='Sleeping %g seconds' % back_off
                    )

                    logger.log_event(
                        logging.INFO,
                        event,
                        provider=self.name
                    )

                    time.sleep(back_off)
                    back_off = random.uniform(0, min(cap, base * 2 ** attempts))
                    attempts += 1
            except QuotaExhaustedError as error:
                if keys_used < KEY_HANDLER.number_of_keys(self.name):
                    # rotate keys, quota for current key is exhausted
                    KEY_HANDLER.cycle_key(self.name)
                    keys_used += 1
                else:
                    # used all keys for this provider, abort
                    raise error
            except Exception as error:
                raise error

    return _back_off_and_jitter


class GeocoderMeta(abc.ABCMeta):
    """
    Attaches a class version property. This version is used for version control in obtaining or 
    ignoring caching results from the geocoder.
    """
    def __new__(metaclass, name, bases, namespace):
        if bases:
            max_base_version = max([version.parse(base.version) for base in bases])
            max_version = max(max_base_version, version.parse(namespace['_version']))

            namespace['version'] = max_version.base_version
        else:
            namespace['version'] = version.parse(namespace['_version']).base_version

        return type.__new__(metaclass, name, bases, namespace)


class Geocoder(metaclass=GeocoderMeta):
    """
    Base class for geocoder services.
    """
    _version = '1.0.0'

    def __init__(self, name, nr_of_retries=3, initial_backoff=1, quota_exceed_on_throttle=False):
        """
        Required fields are fields that are always factored into the API requests if values are
        supplied. Priority fields are optional fields ordered from most to least important.

        The geocoder will always start with all required and priority fields and shed fields from
        the priority fields tailwise until a response is received.
        """
        self.name = name
        self.required_fields = CONFIG[name].get('requested')
        self.priority_fields = CONFIG[name].get('arbitrary')
        self.mapping = CONFIG[name].get('mapping')

        # number of retries when API requests fails or is throttled
        self.nr_of_retries = nr_of_retries
        # initial wait time upon API request fail or throttling
        self.initial_backoff = initial_backoff
        # when throttling retries fail, treat as quota exceeding or not
        self.quota_exceed_on_throttle = quota_exceed_on_throttle

    def _map(self, address):
        """
        If a mapping specified between supplied address components and fields relevant to the
        considered API, then a new dictionary is returned containing the mappings. Otherwise, throw
        an error.
        """
        if self.mapping:
            mapped_address = {}
            for k, v in self.mapping.items():
                if isinstance(v, list):
                    if any(i in address for i in v):
                        mapped_address[k] = ' '.join([address[i] for i in v if i in address])
                elif v in address:
                    mapped_address[k] = address[v]

            return mapped_address
        else:
            raise ValueError
            
    def _request_key(self):
        """
        Gets the current key for this provider.
        """
        return KEY_HANDLER.get_key(self.name)

    @property
    def ttl(self):
        """
        Return the time to live (TTL) for a geocoder. If the record can be stored permanently, an
        error is thrown. The TTL must be in seconds.
        """
        return None

    def quota_reset(self):
        """
        Determine the next datetime in epoch format when the quota for this provider resets.
        """
        reset_time = datetime.datetime.now() + datetime.timedelta(hours=1)
        return reset_time.timestamp()

    @abc.abstractmethod
    def _parse_returned_address(self, response):
        """
        Each geocoder derived from this base class picks fields from the returned response to
        assemble an address corresponding to the returned coordinates of that geocoder.
        """
        raise NotImplementedError

    def parse_returned_address(self, response):
        """
        Parse the response to extract an address for the returned coordinates.
        """
        returned_address = self._parse_returned_address(response)

        return returned_address

    @abc.abstractmethod
    def _geocode(self, address):
        """
        Each geocoder derived from this base class chooses its own way of geocoding an address.
        However, each geocoder must map status and error codes to convenient classes to make higher
        level code aware of what's going on.
        """
        raise NotImplementedError

    @back_off_and_jitter
    def geocode(self, entity):
        """
        Check whether the geocoder has enough information to geocode this entity and return the
        geocoder response if this is the case.
        """
        address = entity.address

        priority = list(filter(lambda i: i in entity.address, self.priority_fields))

        address = dict(filter(lambda pair: pair[0] in itertools.chain(
            self.required_fields,
            priority
        ) , address.items()))

        discarded = []

        # attempt all fields
        try:
            result = self._geocode(address)
        except (TypeError, NoResultsFoundError):
            # start removing optional fields
            while priority:
                omission = priority.pop()
                discarded.append(omission)

                event = dict(
                    state='field omission',
                    field=omission,
                    value=address.pop(omission)
                )

                logger.log_event(
                    logging.INFO,
                    event,
                    provider=self.name,
                    entity_id=entity.entity_id,
                    entity_type=entity.entity_type
                )

                try:
                    result = self._geocode(address)
                    break
                except NoResultsFoundError:
                    continue
            else:
                raise NoResultsFoundError(self.name)

        result['meta'] = {
            'rejected': discarded,
            'supplied': list(address.keys()),
            'address': entity.address,
            'address_out': self.parse_returned_address(result)
        }

        if hasattr(entity, 'guess'):
            offer = {
                'longitude': result['longitude'],
                'latitude': result['latitude']
            }

            result['meta'].update({
                'guess': entity.guess,
                'distance': location.distance_geocodes(entity.guess, offer)
            })

        # time to live in DynamoDB
        if self.ttl:
            result['timestamp'] = int(datetime.datetime.now().timestamp()) + self.ttl

        # entity data
        entity_meta = dict(
            entity_id=entity.entity_id,
            entity_type=entity.entity_type
        )
        result.update(entity_meta)

        # hash and range keys
        result.update(dict(
            entity='{entity_type}:{entity_id}'.format(**entity_meta),
            provider=self.name,
        ))

        return result
