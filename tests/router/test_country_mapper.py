from unittest import mock
import pytest

from router.utils import country_mapper, fetcher


class TestCountryMapper:
    @pytest.fixture(scope='class', autouse=True)
    def clear_singleton(self):
        country_mapper.Singleton._instances = {}

    @pytest.fixture
    def fetcher_stub(self):
        stub = mock.Mock(spec=fetcher.Fetcher)
        stub.fetch_country_codes.return_value = [
            {
                'name': 'Belgium',
                'destination_id': 1,
                'iso_3166_2': 'BE',
                'iso_3166_3': 'BEL'
            },
            {
                'name': 'Australia',
                'destination_id': 2,
                'iso_3166_2': 'AU',
                'iso_3166_3': 'AUS'
            },
            {
                'name': 'Austria',
                'destination_id': 3,
                'iso_3166_2': 'AT',
                'iso_3166_3': 'AUT'
            }
        ]

        return stub

    def test_initialize(self, fetcher_stub):
        country_mapper.CountryMapper(fetcher_stub)

    def test_map_country_exact(self, fetcher_stub):
        mapper = country_mapper.CountryMapper(fetcher_stub)

        country_code = mapper.map_name('Belgium')
        assert country_code == 'BE'

    def test_map_country_inexact(self, fetcher_stub):
        mapper = country_mapper.CountryMapper(fetcher_stub)

        country_code = mapper.map_name('Australa')
        assert country_code == 'AU'

    def test_map_country_no_result(self, fetcher_stub):
        mapper = country_mapper.CountryMapper(fetcher_stub)

        country_code = mapper.map_name('Netherlands')
        assert country_code is None

    def test_map_destination_id(self, fetcher_stub):
        mapper = country_mapper.CountryMapper(fetcher_stub)

        country_code = mapper.map_destination_id(1)
        assert country_code == 'BE'

    def test_map_iso_3166_3(self, fetcher_stub):
        mapper = country_mapper.CountryMapper(fetcher_stub)

        country_code = mapper.map_iso_3166_3('BEL')
        assert country_code == 'BE'

    def test_map_accommodation_id(self, fetcher_stub, monkeypatch):
        mapper = country_mapper.CountryMapper(fetcher_stub)

        country_code = mapper.map_destination_id(1)
        assert country_code == 'BE'
