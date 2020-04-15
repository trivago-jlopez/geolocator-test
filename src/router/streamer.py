import collections
import importlib
import json
import logging
import os

import rollbar
from router import logger
from router.utils import Stasher
from router.utils import dynamodb_json_to_dict

# Logging (Rollbar)
ROLLBAR = {
    'access_token': '1ea244fa68ce4e01b73e171d1c51b329',
    'environment': os.getenv('ENVIRONMENT'),
    'handler': 'blocking',
    'locals': {'enabled': False}
}
if ROLLBAR['environment'] == 'production':
    rollbar.init(**ROLLBAR)


CandidateGeoDataBase = collections.namedtuple(
    'CandidateGeoData',
    (
        'candidate_id',
        'longitude',
        'latitude',
        'locality_id',
        'administrative_division_id',
        'country_id',
        'valid_geo_point'
    )
)


class CandidateGeoData(CandidateGeoDataBase):
    definition = 'router.protos.content.accommodation.candidate_geo_data'

    def __new__(cls, **kwargs):
        return super(CandidateGeoData, cls).__new__(
            cls,
            kwargs.get('candidate_id'),
            kwargs.get('longitude'),
            kwargs.get('latitude'),
            kwargs.get('locality_id'),
            kwargs.get('administrative_division_id'),
            kwargs.get('country_id'),
            kwargs.get('valid_geo_point')
        )

    @property
    def locality_ns(self):
        if self.locality_id:
            return 200

    @property
    def administrative_division_ns(self):
        if self.administrative_division_id:
            return 200

    @property
    def country_ns(self):
        if self.country_id:
            return 200

    @property
    def key(self):
        return 'candidate_accommodation:{candidate_id}'.format(
            candidate_id=self.candidate_id
        )

    def parse_value(self, message, field):
        """
        Sets a non-dict field of a protobuf message after converting to the expected type.
        """
        if getattr(self, field, None):
            cls = type(getattr(message, field))
            setattr(message, field, cls(getattr(self, field)))

    def parse_dict(self, message):
        """
        Traverses a nested protobuf field to assign values to its subfields.
        """
        for field in message.DESCRIPTOR.fields_by_name:
            if hasattr(getattr(message, field), 'DESCRIPTOR'):
                self.parse_dict(getattr(message, field))
            else:
                self.parse_value(message, field)

    def serialize(self):
        msg = getattr(
            importlib.import_module(self.definition + '_pb2'),
            self.definition.split('.')[-1]
        )()

        self.parse_dict(msg)

        protobuf = msg.SerializeToString()
        logger.log_status(
            logging.INFO,
            status='OK',
            key=self.key,
            protobuf=protobuf
        )

        return protobuf


class Streamer:
    def __init__(self, stasher : Stasher):
        self.candidates = []
        self.stasher = stasher

    def put_record(self, record : dict):
        self.candidates.append(CandidateGeoData(**{
            'candidate_id': int(record['entity'].split(':')[-1]),
            **record
        }))

    def stream(self):
        if self.candidates:
            self.stasher.stream_candidate_geo_data(self.candidates)
            logger.log_message(logging.INFO, 'Streamed %s candidates', len(self.candidates))


def load_records(events):
    """
    Filters and converts expired DynamoDB records.
    """
    records = []
    for event in events:
        try:
            if event['eventName'] == 'REMOVE':
                records.append(dynamodb_json_to_dict(event['dynamodb']['OldImage']))

        except Exception as error:
            print(error)

    return records


def lambda_handler(event, context):
    """
    Stream out expired candidates from the transfer table. Candidates that were not updated by the
    citylocator, will only stream out the candidate ID, indicating no results were found.
    """
    try:
        stasher = Stasher()
        records = load_records(event['Records'])
        streamer_obj = Streamer(stasher)
        for record in records:
            streamer_obj.put_record(record)

        streamer_obj.stream()

    except Exception as error:
        logger.log_exception(error)
        rollbar.report_exc_info(payload=event)

        raise error
