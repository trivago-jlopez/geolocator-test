"""
Retrieves API keys from Amazon Simple Systems Manager (SSM).
"""
import collections
import itertools
import json
import logging

import boto3


LOGGER = logging.getLogger('trvcoder.credentials')
LOGGER.setLevel(logging.INFO)


class Singleton(type):
    """
    Singleton pattern.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class KeyHandler(metaclass=Singleton):
    """
    Class to manage all free and business keys for geocoding APIs. Keys can be rotated in case of
    quota exhaustion.
    """
    def __init__(self, sm_name, sm_id):
        keys = self._retrieve_parameter(sm_name, sm_id)
        self.api_keys = dict((k, itertools.cycle(v)) for k, v in keys.items())
        self.key_count = dict((k, len(v)) for k, v in keys.items())

        # set first active keys for each provider
        self.active_keys = dict((k, next(v)) for k, v in self.api_keys.items())

    def _retrieve_parameter(self, sm_name, sm_id):
        """
        Retrieve all API keys from EC2 parameter store.
        """
        secret_str = boto3.client(service_name='secretsmanager').get_secret_value(
            SecretId=sm_name
        )['SecretString']
        value = json.loads(secret_str)[sm_id]

        return json.loads(value)

    def get_key(self, provider):
        """
        Return the current active key for the supplied provider.
        """
        return self.active_keys[provider]

    def cycle_key(self, provider):
        """
        Cycles the key for the supplied provider.
        """
        try:
            self.active_keys[provider] = next(self.api_keys[provider])
            LOGGER.info(dict(
                provider=provider,
                event={
                    'status': 'cycling keys',
                    'value': provider
                }
            ))
        except StopIteration:
            pass

    def number_of_keys(self, provider):
        """
        Returns the number of keys available for a provider.
        """
        return self.key_count[provider]