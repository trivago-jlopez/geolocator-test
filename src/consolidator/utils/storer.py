"""
The storer module provider the Storer class, designed to store consolidated results for entities to
AWS.
"""
import datetime
import decimal
import json
import os
import random
import time

import boto3
from boto3.dynamodb.table import BatchWriter
from botocore.exceptions import ClientError


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


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


class Storer:
    def __init__(self):
        self.client_dynamodb = boto3.client('dynamodb')
        self.client_kinesis = boto3.client('kinesis')
        self.client_s3 = boto3.client('s3')

    def store_consolidations(self, consolidated_entities, environment):
        dynamodb = boto3.resource('dynamodb')
        dynamodb.meta.client = self.client_dynamodb

        table = dynamodb.Table(os.environ['GEOCODES_TABLE'])
        with BatchWriterOCC(table, overwrite_by_pkeys=('entity', 'provider')) as batch_writer:
            for result in consolidated_entities:
                data = {
                    'entity': result['entity'],
                    'entity_id': result['entity_id'],
                    'entity_type': result['entity_type'],
                    'batch_id': result.get('batch_id'),
                    'provider': 'consolidated_' + environment,
                    'longitude': decimal.Decimal(str(result['longitude'])),
                    'latitude': decimal.Decimal(str(result['latitude'])),
                    'score': decimal.Decimal(str(result['score'])),
                    'meta': {
                        'city': result['city'],
                        'country_code': result['country_code']
                    }
                }

                if os.environ['ENVIRONMENT'] != 'prod':
                    data['timestamp'] = int(datetime.datetime.utcnow().timestamp()) + 3*3600

                batch_writer.put_item(Item=data)

    def broadcast_consolidations(self, consolidated_entities):
        while consolidated_entities:
            response = self.client_kinesis.put_records(
                Records=[
                    {
                        'Data': json.dumps(record, cls=DecimalEncoder).encode('utf-8'),
                        'PartitionKey': '{entity_type}:{entity_id}'.format(**record)
                    } for record in consolidated_entities
                ],
                StreamName=os.environ['OUTPUT_STREAM']
            )

            consolidated_entities = [
                e for i, e in enumerate(consolidated_entities) if response['Records'][i].get('ErrorCode')
            ]

            time.sleep(0.1)


    def store_json_to_s3(self, obj, s3_bucket, s3_key):
        self.client_s3.put_object(
            Body=json.dumps(obj, cls=DecimalEncoder).encode('utf-8'),
            Bucket=s3_bucket,
            Key=s3_key
        )

    def store_destinations(self, destinations):
        self.store_json_to_s3(
            destinations,
            os.environ['WORLD_BUCKET'],
            'consolidation/destinations/latest.json'
        )
