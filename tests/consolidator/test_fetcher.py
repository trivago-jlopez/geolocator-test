import json
import os

from botocore.stub import Stubber, ANY
import pytest

from consolidator import candidate, entity
from consolidator.utils import fetcher


class TestFetcher:
    @pytest.fixture()
    def create_data_dir(self, tmpdir):
        data_dir = tmpdir.mkdir('data')

        destinations = data_dir.join("destinations.json")
        destinations.write(json.dumps(
            [
                {
                    'city_id': 1,
                    'name': 'London',
                    'longitude': 45.3425,
                    'latitude': 1.3424,
                    'country_id': 1,
                    'country_code': 'GB'
                },
                {
                    'city_id': 2,
                    'name': 'Amsterdam',
                    'longitude': 45.3425,
                    'latitude': 1.3424,
                    'country_id': 2,
                    'country_code': 'NL'
                }
            ]
        ))

        country_codes = data_dir.join("country_codes.json")
        country_codes.write(json.dumps(
            [
                {
                    "iso_3166_2": "GB",
                    "iso_3166_3": "GBR",
                    "iso_numeric": 826,
                    "destination_id": 66,
                    "name": "United Kingdom"
                },
                {
                    "iso_3166_2": "US",
                    "iso_3166_3": "USA",
                    "iso_numeric": 840,
                    "destination_id": 216,
                    "name": "United States"
                }
            ]
        ))

        ruleset = data_dir.join("geocoders-ruleset-test.json")
        ruleset.write(json.dumps(
            {
                "schema": {
                    "fields": [
                        "provider",
                        "accuracy",
                        "confidence",
                        "quality",
                        "score",
                        "country_code"
                    ],
                    "required": [
                        "provider"
                    ],
                    "filter": [
                        "country_code"
                    ]
                },
                "rules": [
                    {
                        "provider": "google",
                        "accuracy": "ROOFTOP",
                        "confidence": "9.0",
                        "quality" : "political"
                    },
                    {
                        "provider": "tomtom",
                        "confidence": "10.0",
                        "quality" : "Point Address"
                    },
                    {
                        "provider": "google",
                        "accuracy": "ROOFTOP",
                        "confidence": "8.0",
                        "quality" : "political"
                    },
                    {
                        "provider": "mapbox",
                        "accuracy": "interpolated",
                        "quality" : "0.9",
                        "country_code": "US"
                    },
                    {
                        "provider": "tomtom",
                        "confidence": "10.0",
                        "quality" : "Point Address",
                        "country_code": "US"
                    }
                ]
            }
        ))

        return str(data_dir)

    def test_initialize(self):
        fetcher.Fetcher()

    def test_fetch_candidates(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setitem(os.environ, 'GEOCODES_TABLE', 'test')
            data_fetcher = fetcher.Fetcher()

            stubber = Stubber(data_fetcher.client_dynamodb)
            stubber.add_response(
                'query',
                service_response={
                    'Count': 3,
                    'Items': [
                        {
                            'entity': {'S': 'accommodation:1'},
                            'entity_id': {'N': '1'},
                            'entity_type': {'S': 'accommodation'},
                            'provider': {'S': 'google'},
                            'longitude': {'N': '23.5245'},
                            'latitude': {'N': '-41.8499'},
                            'meta': {'M': {
                                'address': {'M': {
                                    'city': {'S': 'London'},
                                    'country_code': {'S': 'GB'}
                                }}
                            }}
                        },
                        {
                            'entity': {'S': 'accommodation:1'},
                            'entity_id': {'N': '1'},
                            'entity_type': {'S': 'accommodation'},
                            'provider': {'S': 'tomtom'},
                            'longitude': {'N': '23.8211'},
                            'latitude': {'N': '-41.9832'},
                            'meta': {'M': {
                                'address': {'M': {
                                    'city': {'S': 'London'},
                                    'country_code': {'S': 'GB'}
                                }}
                            }}
                        },
                        {
                            'entity': {'S': 'accommodation:1'},
                            'entity_id': {'N': '1'},
                            'entity_type': {'S': 'accommodation'},
                            'provider': {'S': 'osm'},
                            'longitude': {'N': '23.3338'},
                            'latitude': {'N': '-41.8942'},
                            'meta': {'M': {
                                'address': {'M': {
                                    'city': {'S': 'London'},
                                    'country_code': {'S': 'GB'}
                                }}
                            }}
                        }
                    ]
                },
                expected_params={
                    'TableName': os.environ['GEOCODES_TABLE'],
                    'KeyConditionExpression': ANY
                }
            )

            with stubber:
                entity_obj = entity.Accommodation(1, stubber)
                response = data_fetcher.fetch_candidates(entity_obj)

                assert len(response) == 3
                for i in response:
                    assert isinstance(i, dict)
                    candidate.AccommodationCandidate(**i)

                stubber.assert_no_pending_responses()

    @pytest.mark.skip(reason="No longer create destination dumps, instead use a static file")
    def test_fetch_aurora_credentials(self):
        data_fetcher = fetcher.Fetcher()

        stubber = Stubber(data_fetcher.client_ssm)
        stubber.add_response(
            'get_parameter',
            service_response={
                'Parameter': {
                    'Name': '/aurora/credentials/consolidator',
                    'Type': 'SecureString',
                    'Value': '{"port": 5432, "user": "consolidator", "database": "test"}',
                    'Version': 1
                }
            },
            expected_params={
                'Name': '/aurora/credentials/consolidator',
                'WithDecryption': True
            }
        )

        with stubber:
            response = data_fetcher.fetch_aurora_credentials('consolidator')
            assert isinstance(response, dict)

            stubber.assert_no_pending_responses()

    def test_fetch_ruleset_definition(self, create_data_dir):
            data_fetcher = fetcher.Fetcher()

            response = data_fetcher.fetch_ruleset_definition('geocoders', 'test', data_dir=create_data_dir)
            assert isinstance(response, dict)

    def test_fetch_destinations(self, create_data_dir):
            data_fetcher = fetcher.Fetcher()

            response = data_fetcher.fetch_destinations(data_dir=create_data_dir)
            assert isinstance(response, list)

    def test_fetch_country_codes(self, create_data_dir):
            data_fetcher = fetcher.Fetcher()

            response = data_fetcher.fetch_country_codes(data_dir=create_data_dir)
            assert isinstance(response, list)
