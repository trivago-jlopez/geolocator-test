from unittest import mock
import pytest

from consolidator import candidate
from consolidator.strategy import fallback
from consolidator.utils import fetcher


class TestCityFallback:
    @pytest.fixture(scope='class', autouse=True)
    def clear_singleton(self):
        fallback.Singleton._instances = {}

    @pytest.fixture
    def fetcher_stub(self):
        stub = mock.Mock(spec_set=fetcher.Fetcher)
        stub.fetch_destinations.return_value = [
            {
                'name': 'London',
                'city_id': 17399,
                'country_code': 'GB',
                'country_id': 66,
                'longitude': -0.0166,
                'latitude': 51.5432
            },
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
                'name': 'Boston',
                'city_id': 14535,
                'country_code': 'US',
                'country_id': 216,
                'longitude': -71.0569,
                'latitude': 42.3588
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

        return stub

    def test_initialization(self, fetcher_stub):
        fallback.CityFallback(fetcher_stub)

    def test_search_destinations(self, fetcher_stub):
        fallback_obj = fallback.CityFallback(fetcher_stub)

        match = fallback_obj.search_destinations('Londn', 'GB')
        assert isinstance(match, dict)
        assert match['name'] == 'London'
        assert match['country_code'] == 'GB'

    def test_search_destinations_wrong_country_code(self, fetcher_stub):
        fallback_obj = fallback.CityFallback(fetcher_stub)

        match = fallback_obj.search_destinations('New York City', 'JP')
        assert match is None

    def test_search_destinations_country_code(self, fetcher_stub):
        fallback_obj = fallback.CityFallback(fetcher_stub)

        match = fallback_obj.search_destinations('Amster-damn', 'NL')
        assert isinstance(match, dict)
        assert match['name'] == 'Amsterdam'
        assert match['country_code'] == 'NL'

        match = fallback_obj.search_destinations('Amster-damn', 'US')
        assert isinstance(match, dict)
        assert match['name'] == 'Amsterdam'
        assert match['country_code'] == 'US'

    def test_search_destinations_no_country_code(self, fetcher_stub):
        fallback_obj = fallback.CityFallback(fetcher_stub)

        # the NL Amsterdam was inserted first
        match = fallback_obj.search_destinations('Amster-damn', None)
        assert isinstance(match, dict)
        assert match['name'] == 'Amsterdam'
        assert match['country_code'] == 'NL'

    @pytest.fixture
    def candidates_nulls(self):
        return [
            candidate.AccommodationCandidate(
                provider="google",
                longitude=45.8941,
                latitude=-23.9191,
                accuracy="ROOFTOP",
                confidence="8.0",
                quality="political",
                city="Boston"
            ),
            candidate.AccommodationCandidate(
                provider="tomtom",
                longitude=45.1192,
                latitude=-23.4723,
                confidence="10.0",
                quality= "Point Address",
                country_code="US",
                city="Boston"
            ),
            candidate.AccommodationCandidate(
                provider="mapbox",
                longitude=45.5912,
                latitude=-23.9220,
                accuracy="interpolated",
                quality= "0.9",
                country_code="US",
                city="New York City"
            )
        ]

    @pytest.fixture
    def candidates_dissenting(self):
        return [
            candidate.AccommodationCandidate(
                provider="google",
                longitude=45.8941,
                latitude=-23.9191,
                accuracy="ROOFTOP",
                confidence="8.0",
                quality="political",
                country_code="NL",
                city="Amsterdam"
            ),
            candidate.AccommodationCandidate(
                provider="tomtom",
                longitude=45.1192,
                latitude=-23.4723,
                confidence="10.0",
                quality= "Point Address",
                country_code="US",
                city="Amsterdam"
            ),
            candidate.AccommodationCandidate(
                provider="mapbox",
                longitude=45.5912,
                latitude=-23.9220,
                accuracy="interpolated",
                quality= "0.9",
                country_code="US",
                city="New York City"
            )
        ]

    def test_get_fallback_coordinates_nulls(self, fetcher_stub, candidates_nulls):
        fallback_obj = fallback.CityFallback(fetcher_stub)
        candidate_fallback = fallback_obj.get_fallback_coordinates(candidates_nulls)

        assert isinstance(candidate_fallback, candidate.AccommodationCandidate)
        assert candidate_fallback.provider == 'city_polygons'
        assert candidate_fallback.city == 'Boston'
        assert candidate_fallback.country_code == 'US'

    def test_get_fallback_coordinates_dissenting(self, fetcher_stub, candidates_dissenting):
        fallback_obj = fallback.CityFallback(fetcher_stub)
        candidate_fallback = fallback_obj.get_fallback_coordinates(candidates_dissenting)

        assert isinstance(candidate_fallback, candidate.AccommodationCandidate)
        assert candidate_fallback.provider == 'city_polygons'
        assert candidate_fallback.city == 'Amsterdam'
        assert candidate_fallback.country_code == 'NL'
