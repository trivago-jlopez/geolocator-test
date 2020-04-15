"""
Helper functions for the geocoder lambda.
"""
import decimal
import json
import random
from six import string_types, integer_types, binary_type
import time

import boto3
from boto3.dynamodb.table import BatchWriter
from botocore.exceptions import ClientError


class GeocoderError(Exception):
    """
    Error class for geocoder errors. The inheritance will be used for JSON logging in the logger
    module.
    """
    status = 'UNKNOWN'
    status_code = -1


class QuotaExhaustedError(GeocoderError):
    """
    Error class for quota exhaustion.
    """
    status = 'QUOTA EXHAUSTED'
    status_code = 1


class RateLimitExceededError(GeocoderError):
    """
    Error class for exceeding an API rate limit. Due to the setup in the AWS infrastructure, we
    cannot rely on the rate limiters from this party libraries to deal with rate limit issues.
    """
    status = 'RATE LIMIT EXCEEDED'
    status_code = 2


class FailedRequestError(GeocoderError):
    """
    Error class for failed API requests. The failure is expected to be on the API side.
    """
    status = 'FAILED REQUEST'
    status_code = 3


class InvalidRequestError(GeocoderError):
    """
    Error class for invalid API requests. The failure is expected to be on our side.
    """
    status = 'INVALID REQUEST'
    status_code = 4


class NoResultsFoundError(GeocoderError):
    """
    Error class for addresses that cannot be geocoded by some API.
    """
    status='NO RESULTS'
    status_code = 5


def dynamo_sanitize(data):
    """Sanitize an object so it can be updated to dynamodb (recursive).
    Here are the various conversions:
    Python                                  DynamoDB
    ------                                  --------
    None                                    {'NULL': True}
    True/False                              {'BOOL': True/False}
    int/Decimal                             {'N': str(value)}
    string                                  {'S': string}
    Binary/bytearray/bytes (py3 only)       {'B': bytes}
    set([int/Decimal])                      {'NS': [str(value)]}
    set([string])                           {'SS': [string])
    set([Binary/bytearray/bytes])           {'BS': [bytes]}
    list                                    {'L': list}
    dict                                    {'M': dict}
    :param data: python object to be sanitized
    :returns: A sanitized copy of the input object.
    """
    if isinstance(data, string_types) and not data.strip() or isinstance(data, set) and not data:
        new_data = None  # empty strings/sets are forbidden by dynamodb
    elif isinstance(data, (string_types, bool, binary_type)):
        new_data = data  # important to handle these ones before sequences and int!
    elif isinstance(data, (float, integer_types)):
        new_data = decimal.Decimal(str(data))  # Decimal converts str better than float
    elif isinstance(data, (list, tuple)):
        new_data = [dynamo_sanitize(item) for item in data]
    elif isinstance(data, set):
        new_data = {dynamo_sanitize(item) for item in data}
    elif isinstance(data, dict):
        new_data = {
            str(key) if not isinstance(key, string_types) \
            else key: dynamo_sanitize(data[key]) for key in data
        }  # keys should be a string
    else:
        new_data = data
    return new_data


class BatchWriterOCC(BatchWriter):
    """
    Implements optimistic concurrency control (OCC) as specified in aws_. This class provides a
    batch writer that implements exponential back off and jitter (full) to decluster calls made
    to Dynamo.

    .. _aws: https://www.awsarchitectureblog.com/2015/03/backoff.html
    """
    def __init__(self, table, flush_amount=25, overwrite_by_pkeys=None, nr_of_retries=10):
        super(BatchWriterOCC, self).__init__(
            table.table_name,
            table.meta.client,
            flush_amount=flush_amount,
            overwrite_by_pkeys=overwrite_by_pkeys
        )

        self.back_off = 1   # initial back off starts at 1 seconds
        self.cap = 60       # maximum back off of 60 seconds
        self.base = 1
        self.nr_of_retries = nr_of_retries


    def _flush(self):
        if int(len(self._items_buffer) / self._flush_amount) > 0:
            repetitions = int(len(self._items_buffer) / self._flush_amount)

            # flush increments equal to flush amount
            for _ in range(repetitions):
                self._flush_with_back_off_and_jitter()
        else:
            # flush last records
            while self._items_buffer:
                self._flush_with_back_off_and_jitter()


    def _flush_with_back_off_and_jitter(self):
        attempt = 0

        while self._items_buffer:
            try:
                super(BatchWriterOCC, self)._flush()
            except ClientError as exception:
                print(exception)
                error_code = exception.response.get('Error', {}).get('Code')

                if error_code == 'ProvisionedThroughputExceededException':
                    time.sleep(self.back_off)

                    # exponential back off and jitter
                    self.back_off = random.randint(0, min(self.cap, self.base * 2 ** attempt))
                    attempt += 1

                    if attempt > self.nr_of_retries:
                        raise exception
                else:
                    raise exception

        self.back_off = 1

    def __exit__(self, type, value, traceback):
        while self._items_buffer:
            self._flush_with_back_off_and_jitter()


def load_validation_schema():
    """
    Loads country codes as a dictionary indexed by ISO-3166-2 country codes. The value for each key
    is the destination id of the country code.
    """
    with open('schemas/geocoder.json') as f:
        return json.load(f)
