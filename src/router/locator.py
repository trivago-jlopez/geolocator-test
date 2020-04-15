import base64
import json
import logging
import os
from dataclasses import dataclass
from typing import List, Iterable
from urllib.parse import quote

import boto3
import requests
import requests_aws4auth
import retrying

from router import logger
from router.utils import Stasher


class NoCityFound(Exception):
    pass

class LimitExceeded(Exception):
    pass

class BadRequest(Exception):
    pass

class RetryableException(Exception):
    pass

class TooManyRequests(RetryableException):
    pass


@dataclass
class Location:
    candidate_id: int
    longitude: float
    latitude: float
    city: str
    valid_geo_point: bool


@dataclass
class Located:
    location: Location
    locality_id: int
    locality_ns: int
    administrative_division_id: int
    administrative_division_ns: int
    country_id: int
    country_ns: int

    def to_dict(self):
        return {
            'entity': f'candidate_accommodation:{self.location.candidate_id}',
            'entity_id': self.location.candidate_id,
            'locality_id': self.locality_id,
            'locality_ns': self.locality_ns,
            'administrative_division_id': self.administrative_division_id,
            'administrative_division_ns': self.administrative_division_ns,
            'country_id': self.country_id,
            'country_ns': self.country_ns,
            'longitude': self.location.longitude,
            'latitude': self.location.latitude,
            'valid_geo_point': self.location.valid_geo_point
        }


class CityLocatorApi:
    def __init__(self, api_id : str, api_key : str, aws_region : str, environment: str):
        self.aws_region = aws_region
        self.url = f'https://{api_id}.execute-api.{aws_region}.amazonaws.com/{environment}/locate'

        self.headers = {
            'x-api-key': api_key
        }

    def authorize(self):
        session = boto3.session.Session()
        credentials = session.get_credentials()

        auth = requests_aws4auth.AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.aws_region,
            'execute-api',
            session_token=credentials.token
        )

        return auth

    @retrying.retry(wait_fixed=100, retry_on_exception=lambda exc: isinstance(exc, RetryableException))
    def locate(self, location : Location) -> Located:
        auth = self.authorize()

        parameters = {
            'longitude': location.longitude,
            'latitude': location.latitude,
            'city': quote(location.city)
        }
        print("URL", self.url)
        print("Auth", auth)
        print("headers", self.headers)
        print("Params", parameters)
        response = requests.request(
            'GET',
            self.url,
            auth=auth,
            headers=self.headers,
            params=parameters
        )

        if response.ok:
            result = response.json()
            if not result:
                raise NoCityFound

            return Located(
                location=location,
                locality_id=result[0]['locality_id'],
                locality_ns=result[0]['locality_ns'],
                administrative_division_id=None,
                administrative_division_ns=None,
                country_id=result[0]['country_id'],
                country_ns=result[0]['country_ns'],
            )
        else:
            logger.log_status(logging.INFO, status=response.status_code)

            # bad request
            if response.status_code == 400:
                raise BadRequest(f'Bad Request (longitude={location.longitude}, latitude={location.latitude}, city={location.city})')
            if response.status_code == 429:
                reason = json.loads(response.text)
                if reason['message'] == 'Limit Exceeded':
                    raise LimitExceeded('Quota Exceeded')
                else:
                    raise TooManyRequests('Too Many Requests')
            if response.status_code == 403:
                raise Exception('Access Denied')

            raise RetryableException

    def process(self, locations : List[Location]) -> Iterable[Located]:
        for location in locations:
            logger.log_message(logging.INFO, location)
            try:
                yield self.locate(location)
            except (NoCityFound, BadRequest, LimitExceeded) as error:
                logger.log_exception(error)
                continue


def parse_location(record):
    data = json.loads(base64.b64decode(record['kinesis']['data']).decode('utf-8'))
    return Location(
        data['entity_id'],
        data['longitude'],
        data['latitude'],
        data.get('meta', {}).get('city'),
        data.get('score', 0.0) >= 0.5
    )


def lambda_handler(event, context):
    try:
        citylocator = CityLocatorApi(
            api_id=os.getenv('API_ID'),
            api_key=os.getenv('API_KEY'),
            aws_region=os.getenv('AWS_REGION'),
            environment='prod' if os.getenv('ENVIRONMENT') == 'production' else 'dev'
        )

        locations = map(parse_location, event['Records'])
        updates = []

        for result in citylocator.process(locations):
            logger.log_message(logging.INFO, result)
            updates.append(result.to_dict())

        stasher = Stasher()
        stasher.batch_update_dynamodb(updates, table_name=os.getenv('TRANSFER_TABLE'))

    except Exception as error:
        logger.log_exception(error)
        raise error
