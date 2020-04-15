"""
The fetcher module provides the Fetcher class, designed to fetch data from AWS relevant to the
consolidator.
"""
import functools
import json
import logging
import operator
import os
import random
import time

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from consolidator import logger


def query_with_back_off_and_jitter(table, nr_of_retries=10, **kwargs):
    """
    Query DynamoDB with pagination and back off against throttling
    """
    back_off = 1
    base = 1
    cap = 60

    attempt = 0
    item_counter = 0

    limit = kwargs.get('limit')
    while True:
        try:
            response = table.query(**kwargs)
        except ClientError as exception:
            error_code = exception.response.get('Error', {}).get('Code')

            if error_code == 'ProvisionedThroughputExceededException':
                time.sleep(back_off)

                # exponential back off and jitter
                back_off = random.randint(0, min(cap, base * 2 ** attempt))
                attempt += 1

                if attempt > nr_of_retries:
                    raise exception
                else:
                    continue
            else:
                raise exception

        for item in response['Items']:
            yield item
            item_counter += 1
            if limit and item_counter >= limit:
                raise StopIteration

        last_evaluated_key = response.get('LastEvaluatedKey')
        if not last_evaluated_key:
            break
        else:
            kwargs.update(ExclusiveStartKey=last_evaluated_key)


class Fetcher:
    def __init__(self):
        self.client_dynamodb = boto3.client('dynamodb')
        self.client_ssm = boto3.client('ssm')

        self._ruleset_definitions = {}

    def fetch_candidates(self, entity):
        """
        Fetches accommodation candidates for an entity from DynamoDB.
        """
        dynamodb = boto3.resource('dynamodb')
        dynamodb.meta.client = self.client_dynamodb

        response = query_with_back_off_and_jitter(
            dynamodb.Table(os.environ['GEOCODES_TABLE']),
            KeyConditionExpression=Key('entity').eq(entity.key)
        )

        candidates = []
        for result in response:
            # legacy code
            address = result['meta'].get('address_out')
            if not address:
                address = result.get('result')
            if not address:
                address = result['meta'].get('address')
            if not address:
                address = result['meta']

            candidates.append({
                'entity_id': result['entity_id'],
                'entity_type': result['entity_type'],
                'provider': result['provider'],
                'longitude': result['longitude'],
                'latitude': result['latitude'],
                'batch_id': result.get('batch_id'),
                'accuracy': result.get('accuracy'),
                'confidence': result.get('confidence'),
                'quality': result.get('quality'),
                'score': result.get('score'),
                'city': address.get('city'),
                'country_code': address.get('country_code')
            })

        return candidates

    def fetch_ruleset_definition(self, name, version, data_dir='data'):
        with open(f'{data_dir}/{name}-ruleset-{version}.json') as f:
            return json.load(f)

    def fetch_destinations(self, data_dir='data'):
        with open(f'{data_dir}/destinations.json') as f:
            return json.load(f)

    def fetch_country_codes(self, data_dir='data'):
        with open(f'{data_dir}/country_codes.json') as f:
            return json.load(f)
