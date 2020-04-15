"""
Transform module to select relevant information for the consolidator.
"""
import decimal
import itertools
import json
import os

import boto3
from boto3.dynamodb.types import TypeDeserializer
from six import string_types

from consolidator.utils import storer


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if abs(o) % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)


def batch(iterable, batch_size=10):
    sourceiter = iter(iterable)
    while True:
        batchiter = itertools.islice(sourceiter, batch_size)
        yield itertools.chain([next(batchiter)], batchiter)


def dynamo_json_to_dict(dynamo_json):
    """
    Convert DynamoDB json string or object to dict.
    """
    deserializer = TypeDeserializer()

    if isinstance(dynamo_json, string_types):
        dynamo_json = json.loads(dynamo_json)

    return dict(
        [(k, deserializer.deserialize(v)) for k, v in dynamo_json.items()]
    )


def lambda_handler(event, context):
    """
    Forward DynamoDB inserts and updates to the geocoder output stream and the consolidator queue.
    """
    data_storer = storer.Storer()

    broadcast = []
    process = set()

    for record in event['Records']:
        if record['dynamodb'].get('NewImage'):
            payload = dynamo_json_to_dict(record['dynamodb']['NewImage'])
            if 'batch_id' not in payload:
                payload['batch_id'] = None

            print(payload)

            if payload['provider'].startswith('consolidated'):
                if payload['provider'] == 'consolidated_' + os.environ['ENVIRONMENT']:
                    broadcast.append({
                        'entity_id': payload['entity_id'],
                        'entity_type': payload['entity_type'],
                        'batch_id': payload.get('batch_id'),
                        'longitude': payload['longitude'],
                        'latitude': payload['latitude'],
                        'score': payload['score'],
                        'meta': payload['meta']
                    })
            else:
                process.add('{entity_type}:{entity_id}:{batch_id}'.format(**payload))

    if broadcast:
        for message_batch in batch(broadcast, batch_size=500):
            data_storer.broadcast_consolidations(message_batch)

    if process:
        messages = []
        for key in process:
            key_components = key.split(':')
            messages.append({
                'entity_type': key_components[0],
                'entity_id': int(key_components[1]),
                'batch_id': key_components[2]
            })

        queue = boto3.resource('sqs').Queue(os.environ['INPUT_QUEUE'])

        for message_batch in batch(messages, batch_size=10):
            queue.send_messages(
                Entries=[
                    {
                        'Id': str(i),
                        'MessageBody': json.dumps(message, cls=storer.DecimalEncoder)
                    } for i, message in enumerate(message_batch)
                ]
            )
