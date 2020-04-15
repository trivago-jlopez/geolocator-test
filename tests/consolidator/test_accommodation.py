import os

from botocore.exceptions import ClientError
from unittest import mock
import pytest

from consolidator import candidate, entity
from consolidator.approach import accommodation
from consolidator.strategy import fallback
from consolidator.utils import fetcher


class TestAccommodationConsolidation:
    @pytest.fixture(scope='class', autouse=True)
    def clear_singleton(self):
        fallback.Singleton._instances = {}

    @pytest.fixture
    def fetcher_stub(self):
        def fetch_ruleset_definition_side_effect(name, version):
            if name == 'geocoders':
                return {
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
            elif name == 'partners':
                return {
                    "schema": {
                        "fields": [
                            "provider"
                        ],
                        "required": [
                            "provider"
                        ]
                    },
                    "rules": [
                        {
                            "provider": "Homeaway"
                        },
                        {
                            "provider": "Hotelwiz"
                        }
                    ]
                }
            else:
                raise ClientError

        stub = mock.Mock(spec_set=fetcher.Fetcher)
        stub.fetch_destinations.return_value = [
            {
                'name': 'Amsterdam',
                'city_id': 27561,
                'country_code': 'NL',
                'country_id': 141,
                'longitude': -1.1317,
                'latitude': 52.6345
            },
            {
                'name': 'Rotterdam',
                'city_id': 27599,
                'country_code': 'NL',
                'country_id': 141,
                'longitude': 4.4780,
                'latitude': 51.9221
            },
            {
                'name': 'Amsterdam',
                'city_id': 49422,
                'country_code': 'US',
                'country_id': 216,
                'longitude': -74.1889,
                'latitude': 42.9389
            },
            {
                'name': 'New York City',
                'city_id': 14734,
                'country_code': 'US',
                'country_id': 216,
                'longitude': -73.9851,
                'latitude': 40.7588
            }
        ]

        stub.fetch_ruleset_definition.side_effect = fetch_ruleset_definition_side_effect

        return stub

    @pytest.fixture
    def candidates_geocoders(self):
        return [
            dict(
                provider="google",
                longitude=45.8941,
                latitude=-23.9191,
                accuracy="ROOFTOP",
                confidence="8.0",
                quality="political",
                country_code="US"
            ),
            dict(
                provider="tomtom",
                longitude=45.1192,
                latitude=-23.4723,
                confidence="10.0",
                quality= "Point Address",
                country_code="US"
            ),
            dict(
                provider="mapbox",
                longitude=45.5912,
                latitude=-23.9220,
                accuracy="interpolated",
                quality= "0.9",
                country_code="US"
            )
        ]

    def test_consolidate_geocoders(self, fetcher_stub, candidates_geocoders, monkeypatch):
        with monkeypatch.context() as m:
            m.setitem(os.environ, 'ENVIRONMENT', 'test')
            m.setitem(os.environ, 'GEOCODER_RULESET_VERSION', 'test')

            candidates = list(
                map(lambda x: candidate.AccommodationCandidate(**x), candidates_geocoders)
            )
            winner = accommodation.AccommodationConsolidator.consolidate(candidates, fetcher_stub)

            assert winner
            assert winner.provider == 'mapbox'
            assert winner.score == 1.0
            assert winner.country_code == 'US'

    @pytest.fixture
    def candidates_partners(self):
        return [
            dict(
                provider="google",
                longitude=45.8941,
                latitude=-23.9191,
                accuracy="ROOFTOP",
                confidence="8.0",
                quality="political",
                country_code="US"
            ),
            dict(
                provider="tomtom",
                longitude=45.1192,
                latitude=-23.4723,
                confidence="9.0",
                quality= "Point Address",
                country_code="US"
            ),
            dict(
                provider="mapbox",
                longitude=45.5912,
                latitude=-23.9220,
                accuracy="interpolated",
                quality= "0.8",
                country_code="US"
            ),
            dict(
                provider='Hotelwiz',
                longitude=45.7881,
                latitude=-23.9031,
                country_code='US'
            )
        ]

    def test_consolidate_partners(self, fetcher_stub, candidates_partners, monkeypatch):
        with monkeypatch.context() as m:
            m.setitem(os.environ, 'ENVIRONMENT', 'test')
            m.setitem(os.environ, 'GEOCODER_RULESET_VERSION', 'test')
            m.setitem(os.environ, 'PARTNER_RULESET_VERSION', 'test')

            candidates = list(
                map(lambda x: candidate.AccommodationCandidate(**x), candidates_partners)
            )
            winner = accommodation.AccommodationConsolidator.consolidate(candidates, fetcher_stub)

            assert winner
            assert winner.provider == 'Hotelwiz'
            assert winner.score == 0.5
            assert winner.country_code == 'US'

    @pytest.fixture
    def candidates_city_fallback(self):
        return [
            dict(
                provider="google",
                longitude=45.8941,
                latitude=-23.9191,
                accuracy="ROOFTOP",
                confidence="8.0",
                quality="political",
                city='Amsterdamn',
                country_code="US"
            ),
            dict(
                provider="tomtom",
                longitude=45.1192,
                latitude=-23.4723,
                confidence="9.0",
                quality= "Point Address",
                country_code="US"
            ),
            dict(
                provider="mapbox",
                longitude=45.5912,
                latitude=-23.9220,
                accuracy="interpolated",
                quality= "0.8",
                country_code="US"
            ),
            dict(
                provider='Hotelopia',
                longitude=45.7881,
                latitude=-23.9031,
                country_code='US'
            )
        ]

    def test_consolidate_city_fallback(self, fetcher_stub, candidates_city_fallback, monkeypatch):
        with monkeypatch.context() as m:
            m.setitem(os.environ, 'ENVIRONMENT', 'test')
            m.setitem(os.environ, 'GEOCODER_RULESET_VERSION', 'test')
            m.setitem(os.environ, 'PARTNER_RULESET_VERSION', 'test')

            candidates = list(
                map(lambda x: candidate.AccommodationCandidate(**x), candidates_city_fallback)
            )
            winner = accommodation.AccommodationConsolidator.consolidate(candidates, fetcher_stub)

            assert winner
            assert winner.provider == 'city_polygons'
            assert winner.score == 0.0
            assert winner.city == 'Amsterdam'
            assert winner.country_code == 'US'

    def test_consolidate_accommodation_replace(self, fetcher_stub, candidates_geocoders, monkeypatch):
        with monkeypatch.context() as m:
            m.setitem(os.environ, 'ENVIRONMENT', 'test')
            m.setitem(os.environ, 'GEOCODER_RULESET_VERSION', 'test')

            fetcher_stub.fetch_candidates.return_value = [*candidates_geocoders,
                dict(
                    provider="consolidator_" + os.environ['ENVIRONMENT'],
                    longitude=45.2202,
                    latitude=23.0091,
                    score=0.5,
                    city="Amsterdam",
                    country_code="US"
                )
            ]

            entity_obj = entity.Accommodation(1, fetcher_stub)
            winner = entity_obj.consolidated

            assert winner
            assert winner.provider == 'mapbox'
            assert winner.score == 1.0
            assert winner.country_code == 'US'

    def test_consolidate_accommodation_omit(self, fetcher_stub, candidates_city_fallback, monkeypatch):
        """
        Tests if the consolidated property is None if the consolidation result is not of a higher
        score than the previous result.
        """
        with monkeypatch.context() as m:
            m.setitem(os.environ, 'ENVIRONMENT', 'test')
            m.setitem(os.environ, 'GEOCODER_RULESET_VERSION', 'test')
            m.setitem(os.environ, 'PARTNER_RULESET_VERSION', 'test')

            fetcher_stub.fetch_candidates.return_value = [*candidates_city_fallback,
                dict(
                    provider="consolidator_" + os.environ['ENVIRONMENT'],
                    longitude=45.2202,
                    latitude=23.0091,
                    score=0.5,
                    city="Amsterdam",
                    country_code="US"
                )
            ]

            entity_obj = entity.Accommodation(1, fetcher_stub)
            winner = entity_obj.consolidated

            assert winner is None
