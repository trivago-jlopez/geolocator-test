import base64
import collections
import importlib
import json
import logging
import os
from typing import List
import uuid

import protobuf_to_dict
import rollbar
import yaml

from router import logger, streamer
from router.utils import Fetcher, Stasher, CountryMapper
from router.entity import CandidateAccommodation

# Logging (Rollbar)
ROLLBAR = {
    'access_token': '1ea244fa68ce4e01b73e171d1c51b329',
    'environment': os.getenv('ENVIRONMENT'),
    'handler': 'blocking',
    'locals': {'enabled': False}
}
if ROLLBAR['environment'] == 'production':
    rollbar.init(**ROLLBAR)


class CandidateHandler:
    def __init__(self, candidates : List[CandidateAccommodation]):
        self.candidates = candidates
        self.batch_id = str(uuid.uuid4())

    @classmethod
    def parse_records(cls, records):
        """
        Convert protobuf to CandidateAccommodation objects. A country mapper object tries to correct
        country codes in case they are not ISO 3166-2.
        """
        fetcher = Fetcher()
        country_mapper = CountryMapper(fetcher)

        candidate_module = importlib.import_module('router.protos.content.accommodation.candidate_pb2')
        candidates = []

        for record in records:
            message = candidate_module.candidate()
            print(record)
            print(record['kinesis'])
            decoded_data = base64.b64decode(record['kinesis']['data'])
            print(decoded_data)
            message.ParseFromString(
                base64.b64decode(record['kinesis']['data'])
            )

            data = protobuf_to_dict.protobuf_to_dict(message)

            data.update(data['key'])
            del data['key']

            candidate = CandidateAccommodation(**data, country_mapper=country_mapper)
            logger.log_message(logging.INFO, candidate.to_dict())
            candidates.append(candidate)

        return candidates

    def process(self, stasher : Stasher):
        """
        Utilise the stasher to process the candidates. The steps are as follows:

            - register the candidates for 3 hours TTL
            - candidates with coordinates indicated as good skip geocoding
            - others are geocoded for a list of providers
        """
        self.register_candidates(stasher)
        categories = self.categorize_candidates()

        # store high quality candidates as consolidated immediately
        consolidations = list(map(
            lambda x: dict(**x.as_consolidation(), batch_id=self.batch_id),
            categories['trusted']
        ))

        stasher.stash_consolidations(consolidations, os.getenv('ENVIRONMENT'))
        logger.log_message(logging.INFO, 'Stored %s consolidations', len(consolidations))

        # the others must pass through the geocoder
        addresses = list(map(
            lambda x: dict(**x.as_address(), batch_id=self.batch_id),
            categories['others']
        ))

        stasher.stash_trivago_candidates(addresses)

        providers = ('google', 'osm', 'arcgis', 'tomtom')
        tasks = self.create_geocoder_tasks(addresses, providers)

        stasher.send_geocoder_tasks(tasks)
        logger.log_message(logging.INFO, 'Sent %s geocoder tasks', len(tasks))

    def register_candidates(self, stasher):
        """
        Save the candidate accommodations in DynamoDB with a TTL.
        """
        stasher.register_candidates(self.candidates)
        logger.log_message(logging.INFO, 'Registered %s candidates', len(self.candidates))

    def categorize_candidates(self):
        """
        Split the candidates in two groups based on the valid geocode flag
        """
        categories = collections.defaultdict(list)
        for candidate in self.candidates:
            if candidate.flag['is_valid_geocode']:
                categories['trusted'].append(candidate)
            else:
                categories['others'].append(candidate)

        return categories

    def create_geocoder_tasks(self, addresses : List[dict], providers : List[str]):
        """
        Merge addresses that need geocoding with a list of geocoder providers to create tasks.
        """
        tasks = []

        for address in addresses:
            tasks.extend(map(lambda x: dict(**address, provider=x), providers))

        return tasks


def lambda_handler(event, context):
    try:
        candidates = CandidateHandler.parse_records(event['Records'])

        stasher = Stasher()
        handler = CandidateHandler(candidates)
        handler.process(stasher)

    except Exception as error:
        logger.log_exception(error)
        rollbar.report_exc_info(payload=event)

        raise error
