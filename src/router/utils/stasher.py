import datetime
import decimal
import functools
import itertools
import json
import logging
import os
import random
import time
from typing import Iterable, Iterator
import multiprocessing

import boto3
from boto3.dynamodb.table import BatchWriter
from boto3.dynamodb.types import TypeDeserializer
from botocore.exceptions import ClientError
from six import binary_type, integer_types, string_types

from router import logger


def batch(iterable, batch_size=10):
    """
    Yields batches of an iterable of unknown length until the iterable is exhausted.
    """
    try:
        sourceiter = iter(iterable)
        while True:
            batchiter = itertools.islice(sourceiter, batch_size)
            yield itertools.chain([next(batchiter)], batchiter)
    except StopIteration:
        return


def parallelize(nr_of_procs=1):
    """
    Parallelize a function processing a workload by dividing the iterable into chunks and running
    the function on each chunk in parallel.
    """
    def _parallelize(function):
        @functools.wraps(function)
        def __parallelize(self, records, **kwargs):
            processes = []

            for i in range(nr_of_procs):
                process = multiprocessing.Process(
                    target=function,
                    args=(self, itertools.islice(records, i, None, nr_of_procs)),
                    kwargs=kwargs
                )

                process.start()
                processes.append(process)

            # wait for the processes to finish before proceeding
            for process in processes:
                process.join()

        return __parallelize

    return _parallelize


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


def dynamodb_json_to_dict(dynamodb_json):
    """
    Converts DynamoDB JSON to dict.
    """
    deserializer = TypeDeserializer()

    if isinstance(dynamodb_json, string_types):
        dynamodb_json = json.loads(dynamodb_json)

    return dict(
        [(k, deserializer.deserialize(v)) for k, v in dynamodb_json.items()]
    )


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


class Stasher:
    def __init__(self):
        self.client_dynamodb = boto3.client('dynamodb')
        self.client_kinesis = boto3.client('kinesis')
        self.client_sqs = boto3.client('sqs')

    @parallelize(nr_of_procs=4)
    def send_to_sqs(self, messages : Iterator[str], queue_url):
        for message_batch in batch(messages, batch_size=10):
            entries = list(message_batch)

            while entries:
                response = self.client_sqs.send_message_batch(
                    QueueUrl=queue_url,
                    Entries=[
                        {
                            'Id': str(i),
                            'MessageBody': entry
                        } for i, entry in enumerate(entries)
                    ]
                )

                entries = [entries[int(i['Id'])] for i in response.get('Failed', [])]
                time.sleep(0.1)

    def send_geocoder_tasks(self, tasks : Iterator[dict]):
        self.send_to_sqs(
            map(lambda x: json.dumps(x), tasks),
            queue_url=os.getenv('GEOCODER_QUEUE')
        )

    @parallelize(nr_of_procs=4)
    def stream_to_kinesis(self, records : list, stream_name : str, **kwargs):
        for record_batch in batch(records, batch_size=500):
            entries = list(record_batch)

            while entries:
                client = kwargs.get('client', self.client_kinesis)

                response = client.put_records(
                    Records=entries,
                    StreamName=stream_name
                )

                entries = [
                    e for i,e in enumerate(entries) if response['Records'][i].get('ErrorCode')
                ]

                time.sleep(0.1)

    def stream_candidate_geo_data(self, candidates):
        records = [
            {
                'Data': candidate.serialize(),
                'PartitionKey': candidate.key
            } for candidate in candidates
        ]

        self.stream_to_kinesis(
            records,
            stream_name=os.getenv('STREAM_CANDIDATE_GEO_DATA')
        )

    @parallelize(nr_of_procs=4)
    def write_to_dynamo(self, records : Iterator[dict], table_name : str, pkeys : tuple):
        dynamodb = boto3.resource('dynamodb')
        dynamodb.meta.client = self.client_dynamodb

        table = dynamodb.Table(table_name)
        with BatchWriterOCC(table, overwrite_by_pkeys=pkeys) as batch_writer:
            for record in records:
                batch_writer.put_item(Item=record)

    def insert_dynamodb(self, update : dict, table, pkeys : tuple, nr_of_retries=5):
        """
        Perform an update on a DynamoDB table. In case of write throughput exceeding, the update is
        retried a number of times. If the key is no not present in the database, no update is
        performed.
        """
        back_off = 1
        cap = 60

        attempts = 0
        while True:
            try:
                response = table.put_item(
                    Item=update,
                    ConditionExpression='attribute_not_exists({hash_or_range})'.format(
                        hash_or_range=pkeys[0]
                    )
                )

                return response
            except ClientError as error:
                if error.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    # the entry is already present, don't overwrite
                    return error.response
                else:
                    if attempts > nr_of_retries:
                        raise error
                    else:
                        time.sleep(back_off)

                        back_off = random.uniform(0, min(cap, 2 ** attempts))
                        attempts += 1

    @parallelize(nr_of_procs=4)
    def batch_insert_dynamo(self, updates : Iterator[dict], table_name : str, pkeys : tuple):
        dynamodb = boto3.resource('dynamodb')
        dynamodb.meta.client = self.client_dynamodb

        table = dynamodb.Table(table_name)

        responses = [
            self.insert_dynamodb(dynamo_sanitize(update), table, pkeys) for update in updates
        ]

        accepted_count = len(list(filter(lambda x: 'Error' not in x, responses)))
        logger.log_message(logging.INFO, 'Inserted %s/%s', accepted_count, len(responses))

    def update_dynamodb(self, update, table, nr_of_retries=5):
        """
        Perform an update on a DynamoDB table. In case of write throughput exceeding, the update is
        retried a number of times. If the key is no not present in the database, no update is
        performed.
        """
        back_off = 1
        cap = 60

        attempts = 0
        while True:
            try:
                update_fields = list(filter(lambda x: x != 'entity', update.keys()))

                update_expression = 'SET ' + ', '.join([
                    '{key}=:{key}'.format(key=field) for field in update_fields
                ])

                expression_attribute_values = dict(
                    (':' + field, update[field]) for field in update_fields
                )

                response = table.update_item(
                    Key={
                        'entity': update['entity']
                    },
                    ConditionExpression='attribute_exists(entity)',
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values
                )

                return response
            except ClientError as error:
                if error.response['Error']['Code'] == 'ConditionalCheckFailedException':
                    # the entry is already expired, nothing to update
                    return error.response
                else:
                    if attempts > nr_of_retries:
                        raise error
                    else:
                        time.sleep(back_off)

                        back_off = random.uniform(0, min(cap, 2 ** attempts))
                        attempts += 1

    @parallelize(nr_of_procs=4)
    def batch_update_dynamodb(self, updates : Iterator[dict], table_name):
        """
        Updates registered candidate accommodations in DynamoDB.
        """
        dynamodb = boto3.resource('dynamodb')
        dynamodb.meta.client = self.client_dynamodb

        table = dynamodb.Table(table_name)

        responses = [
            self.update_dynamodb(dynamo_sanitize(update), table) for update in updates
        ]

        accepted_count = len(list(filter(lambda x: 'Error' not in x, responses)))

    def stash_consolidations(self, consolidations, environment):
        records = []
        for entity in consolidations:
            records.append(dict(
                **dynamo_sanitize(entity),
                provider='consolidated_' + environment
            ))

        self.write_to_dynamo(
            records,
            table_name=os.getenv('GEOCODES_TABLE'),
            pkeys=('entity', 'provider')
        )

    def stash_trivago_candidates(self, geocoder_data : Iterator[dict]):
        """
        Extracts the trivago candidate from a geocoder task.
        """
        candidates = []
        for item in geocoder_data:
            try:
                guess = item['address'].pop('guess')

                candidates.append({
                    'entity': '{entity_type}:{entity_id}'.format(**item),
                    'entity_id': item['entity_id'],
                    'entity_type': item['entity_type'],
                    'provider': 'trivago',
                    'batch_id': item['batch_id'],
                    'meta': {
                        **item['address']
                    },
                    **guess
                })
            except KeyError:
                continue

        self.write_to_dynamo(
            list(map(lambda x: dynamo_sanitize(x), candidates)),
            table_name=os.getenv('GEOCODES_TABLE'),
            pkeys=('entity', 'provider')
        )

    def register_candidates(self, candidates):
        """
        Adds the keys for candidate accommodations to the transfer table in DynamoDB. Updates can
        add/modify other attibutes for registered candidate accommodations as long as they are
        present. Candidate accommodations are deleted after an hour.
        """
        expiration_timestamp = int(time.time()) + 3*3600

        records = []
        for candidate in candidates:
            records.append({
                'entity': candidate.key,
                'timestamp': expiration_timestamp
            })

        self.batch_insert_dynamo(
            records,
            table_name=os.getenv('TRANSFER_TABLE'),
            pkeys=('entity',)
        )
